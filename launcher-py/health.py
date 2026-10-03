"""Diagnóstico Digimon World Vice PC — revisa emu/ROM/BIOS/settings/saves/disco.

Solo lectura (no modifica nada). Devuelve lista de checks:
{'key', 'label', 'status': 'ok'|'warn'|'bad', 'detail'}

© Nyxen
"""
import configparser
import shutil
import subprocess

from paths import (
    resolve_emu, resolve_rom, resolve_bios_dir, resolve_settings,
    resolve_memcards, bios_files,
)

EMU_EXE_NAME = "duckstation-qt-x64-ReleaseLTCG.exe"


def _emu_running() -> bool | None:
    """True/False si DuckStation está en ejecución; None si no se pudo saber."""
    try:
        r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {EMU_EXE_NAME}", "/NH"],
                           capture_output=True, text=True, timeout=10)
        out = (r.stdout or "").upper()
        if EMU_EXE_NAME.upper() in out and "INFO: NO" not in out:
            return True
        return False
    except Exception:
        return None


def run_checks() -> list:
    checks = []

    emu = resolve_emu()
    checks.append({"key": "emu", "label": "Emulador",
                   "status": "ok" if emu is not None else "bad",
                   "detail": str(emu) if emu is not None else "Sin configurar: usa el asistente inicial."})

    rom = resolve_rom()
    if rom is not None:
        try:
            detail = f"{rom.name} ({rom.stat().st_size // (1024 * 1024)} MB)"
        except OSError:
            detail = rom.name
    else:
        detail = "Sin configurar: usa el asistente inicial."
    checks.append({"key": "rom", "label": "Juego",
                   "status": "ok" if rom is not None else "bad",
                   "detail": detail})

    names = bios_files()
    bdir = resolve_bios_dir()
    checks.append({"key": "bios", "label": "BIOS",
                   "status": "ok" if names else "bad",
                   "detail": ", ".join(names) if names
                   else (f"Carpeta vacía:\n{bdir}" if bdir is not None
                         else "Sin configurar: usa el asistente inicial.")})

    spath = resolve_settings()
    if spath is not None and spath.is_file():
        try:
            cp = configparser.ConfigParser(interpolation=None)
            cp.optionxform = str
            cp.read(spath, encoding="utf-8")
            problems = []
            if not cp.has_section("GPU") or not cp.has_option("GPU", "Renderer"):
                problems.append("falta GPU.Renderer")
            if not cp.has_section("Pad1"):
                problems.append("falta [Pad1]")
            checks.append({"key": "settings", "label": "Ajustes (settings.ini)",
                           "status": "ok" if not problems else "warn",
                           "detail": "Todo en orden." if not problems else "; ".join(problems)})
        except Exception as e:  # noqa: BLE001
            checks.append({"key": "settings", "label": "Ajustes (settings.ini)",
                           "status": "bad", "detail": f"No se pudo leer: {e}"})
    else:
        checks.append({"key": "settings", "label": "Ajustes (settings.ini)",
                       "status": "warn" if emu is not None else "bad",
                       "detail": "Se creará al guardar ajustes por primera vez."
                       if emu is not None else "Sin emulador configurado."})

    running = _emu_running()
    checks.append({"key": "running", "label": "DuckStation en ejecución",
                   "status": "warn" if running else "ok",
                   "detail": ("Cierra DuckStation antes de aplicar cambios en el launcher."
                              if running else "Cerrado (los cambios se aplicarán bien).")
                   if running is not None else "No se pudo comprobar."})

    mdir = resolve_memcards()
    n_cards = sum(1 for _ in mdir.glob("*.mcd")) if mdir is not None and mdir.is_dir() else 0
    checks.append({"key": "saves", "label": "Partidas",
                   "status": "ok",
                   "detail": f"{n_cards} memory card(s). Respáldalas en SAVES."})

    try:
        from paths import app_dir
        free_gb = shutil.disk_usage(app_dir()).free / (1024 ** 3)
        checks.append({"key": "disk", "label": "Espacio libre",
                       "status": "ok" if free_gb >= 1 else "warn",
                       "detail": f"{free_gb:.1f} GB libres."})
    except Exception:
        checks.append({"key": "disk", "label": "Espacio libre",
                       "status": "warn", "detail": "No se pudo comprobar."})

    return checks


def overall(checks: list) -> tuple:
    if any(c["status"] == "bad" for c in checks):
        return ("bad", "Hay problemas que impiden jugar. Revisa los ✗.")
    if any(c["status"] == "warn" for c in checks):
        return ("warn", "Listo para jugar, con avisos menores.")
    return ("ok", "Todo en orden. Listo para jugar.")


def report_text(checks: list) -> str:
    icon = {"ok": "✓", "warn": "!", "bad": "✗"}
    lines = ["Diagnóstico Digimon World Vice PC"]
    for c in checks:
        lines.append(f"[{icon.get(c['status'], '?')}] {c['label']}: {c['detail']}")
    return "\n".join(lines)
