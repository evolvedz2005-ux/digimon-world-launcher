"""Sonido y velocidad DuckStation — [Audio] OutputVolume y [Main] FastForwardSpeed.

© Nyxen
"""
import configparser
import shutil
from pathlib import Path

from paths import resolve_settings


def _resolve(path=None) -> Path | None:
    if path is not None:
        return Path(path)
    return resolve_settings()


def _load_ini(path=None) -> configparser.ConfigParser:
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str
    try:
        p = _resolve(path)
        if p is not None and p.is_file():
            cp.read(p, encoding="utf-8")
    except Exception:
        pass
    return cp


TURBO_OPTIONS = {"Ilimitada": 0.0, "2x": 2.0, "3x": 3.0, "4x": 4.0, "5x": 5.0}
TURBO_LABELS = list(TURBO_OPTIONS.keys())


def _turbo_label(value: float) -> str:
    for label, v in TURBO_OPTIONS.items():
        if abs(v - value) < 0.01:
            return label
    return "Ilimitada"


def get_audio(path=None) -> dict:
    out = {"volume": 100, "muted": False, "turbo": 0.0}
    try:
        cp = _load_ini(path)
        if cp.has_option("Audio", "OutputVolume"):
            try:
                out["volume"] = max(0, min(100, int(float(cp.get("Audio", "OutputVolume")))))
            except ValueError:
                pass
        if cp.has_option("Audio", "OutputMuted"):
            out["muted"] = cp.get("Audio", "OutputMuted").strip().lower() in ("1", "true", "yes", "on")
        if cp.has_option("Main", "FastForwardSpeed"):
            try:
                out["turbo"] = max(0.0, float(cp.get("Main", "FastForwardSpeed")))
            except ValueError:
                pass
    except Exception:
        pass
    out["turbo_label"] = _turbo_label(out["turbo"])
    return out


def set_audio(values: dict, path=None) -> dict:
    try:
        volume = int(values.get("volume", 100))
    except (ValueError, TypeError):
        return {"ok": False, "error": "Volumen no válido."}
    if not 0 <= volume <= 100:
        return {"ok": False, "error": "Volumen fuera de rango (0-100)."}
    try:
        turbo = float(values.get("turbo", 0.0))
    except (ValueError, TypeError):
        return {"ok": False, "error": "Velocidad turbo no válida."}
    if not 0.0 <= turbo <= 10.0:
        return {"ok": False, "error": "Turbo fuera de rango."}
    muted = bool(values.get("muted", False))
    p = _resolve(path)
    if p is None or not p.parent.is_dir():
        return {"ok": False, "error": "Configura el emulador primero (asistente inicial)."}
    try:
        if p.is_file():
            shutil.copyfile(p, p.with_suffix(".ini.bak"))
    except Exception:
        pass
    try:
        cp = _load_ini(p)
        for sec in ("Audio", "Main"):
            if not cp.has_section(sec):
                cp.add_section(sec)
        cp.set("Audio", "OutputVolume", str(volume))
        cp.set("Audio", "OutputMuted", "true" if muted else "false")
        cp.set("Main", "FastForwardSpeed", str(int(turbo) if turbo == int(turbo) else turbo))
        with open(p, "w", encoding="utf-8") as f:
            cp.write(f)
        return {"ok": True}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
