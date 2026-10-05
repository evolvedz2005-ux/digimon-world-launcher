"""Mando DuckStation — lee/escribe [Pad1] de settings.ini (teclado).

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


def _split_binding(raw: str) -> str:
    """'Keyboard/K' -> 'K'. Si es mando (SDL-x/...) lo devuelve tal cual."""
    s = (raw or "").strip()
    if "/" in s:
        return s.split("/", 1)[1].strip() or s
    return s


# (clave ini, etiqueta visible)
BUTTONS = [
    ("Up", "Arriba"),
    ("Down", "Abajo"),
    ("Left", "Izquierda"),
    ("Right", "Derecha"),
    ("Cross", "Cruz (X)"),
    ("Circle", "Círculo (O)"),
    ("Square", "Cuadrado"),
    ("Triangle", "Triángulo"),
    ("Start", "Start"),
    ("Select", "Select"),
    ("L1", "L1"),
    ("R1", "R1"),
    ("L2", "L2"),
    ("R2", "R2"),
    ("L3", "L3 (stick)"),
    ("R3", "R3 (stick)"),
    ("LUp", "Stick izq. arriba"),
    ("LDown", "Stick izq. abajo"),
    ("LLeft", "Stick izq. izquierda"),
    ("LRight", "Stick izq. derecha"),
    ("RUp", "Stick der. arriba"),
    ("RDown", "Stick der. abajo"),
    ("RLeft", "Stick der. izquierda"),
    ("RRight", "Stick der. derecha"),
]
BUTTON_KEYS = [k for k, _ in BUTTONS]

DEFAULTS = {
    "Up": "UpArrow", "Down": "DownArrow", "Left": "LeftArrow", "Right": "RightArrow",
    "Cross": "K", "Circle": "L", "Square": "J", "Triangle": "I",
    "Start": "Enter", "Select": "Backspace",
    "L1": "Q", "R1": "E", "L2": "1", "R2": "3", "L3": "2", "R3": "4",
    "LUp": "W", "LDown": "S", "LLeft": "A", "LRight": "D",
    "RUp": "T", "RDown": "G", "RLeft": "F", "RRight": "H",
}


def get_controls(path=None) -> dict:
    out = dict(DEFAULTS)
    try:
        cp = _load_ini(path)
        if cp.has_section("Pad1"):
            for k in BUTTON_KEYS:
                if cp.has_option("Pad1", k):
                    v = _split_binding(cp.get("Pad1", k))
                    if v:
                        out[k] = v
    except Exception:
        pass
    return out


def get_raw_bindings(path=None) -> dict:
    """Devuelve el binding completo ('Keyboard/K' o 'SDL-0/...') por si hay mando."""
    out = {}
    try:
        cp = _load_ini(path)
        if cp.has_section("Pad1"):
            for k in BUTTON_KEYS:
                if cp.has_option("Pad1", k):
                    out[k] = cp.get("Pad1", k).strip()
    except Exception:
        pass
    return out


def set_controls(values: dict, path=None) -> dict:
    cleaned = {}
    for k in BUTTON_KEYS:
        v = str(values.get(k, "")).strip()
        if not v:
            return {"ok": False, "error": f"Falta tecla para {k}."}
        if len(v) > 32 or any(c in v for c in "= \t\n\r"):
            return {"ok": False, "error": f"Tecla no válida para {k}: {v}"}
        cleaned[k] = v
    # avisar duplicados de teclado (no bloquea, pero informa)
    seen = {}
    dupes = set()
    for k, v in cleaned.items():
        vl = v.lower()
        if vl in seen:
            dupes.add(v)
        else:
            seen[vl] = k
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
        if not cp.has_section("Pad1"):
            cp.add_section("Pad1")
        if not cp.has_option("Pad1", "Type"):
            cp.set("Pad1", "Type", "AnalogController")
        for k in BUTTON_KEYS:
            cp.set("Pad1", k, f"Keyboard/{cleaned[k]}")
        with open(p, "w", encoding="utf-8") as f:
            cp.write(f)
        msg = "Mando guardado en settings.ini."
        if dupes:
            msg += f" Ojo: tecla repetida ({', '.join(sorted(dupes))})."
        return {"ok": True, "message": msg}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


HOTKEYS = [("FastForward", "Turbo (fast-forward)"),
           ("SaveSelectedSaveState", "Guardar estado"),
           ("LoadSelectedSaveState", "Cargar estado")]
HOTKEY_DEFAULTS = {"FastForward": "Tab", "SaveSelectedSaveState": "F2", "LoadSelectedSaveState": "F1"}


def get_hotkeys(path=None) -> dict:
    """{'FastForward': 'Tab'} — atajos de [Hotkeys]."""
    out = dict(HOTKEY_DEFAULTS)
    try:
        cp = _load_ini(path)
        if cp.has_section("Hotkeys"):
            for k, _ in HOTKEYS:
                if cp.has_option("Hotkeys", k):
                    v = _split_binding(cp.get("Hotkeys", k))
                    if v:
                        out[k] = v
    except Exception:
        pass
    return out


def set_hotkey(name: str, key: str, path=None) -> dict:
    if name not in HOTKEY_DEFAULTS:
        return {"ok": False, "error": f"Atajo no válido: {name}"}
    key = str(key or "").strip()
    if not key or len(key) > 32 or any(c in key for c in "= \t\n\r"):
        return {"ok": False, "error": f"Tecla no válida para {name}."}
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
        if not cp.has_section("Hotkeys"):
            cp.add_section("Hotkeys")
        cp.set("Hotkeys", name, f"Keyboard/{key}")
        with open(p, "w", encoding="utf-8") as f:
            cp.write(f)
        return {"ok": True, "message": f"Atajo guardado: {name} = {key}."}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


# Map keysym Tk -> nombre DuckStation
_TK_MAP = {
    "Up": "UpArrow", "Down": "DownArrow", "Left": "LeftArrow", "Right": "RightArrow",
    "Return": "Enter", "BackSpace": "Backspace", "space": "Space", "Escape": "Escape",
    "Tab": "Tab", "Shift_L": "LeftShift", "Shift_R": "RightShift",
    "Control_L": "LeftControl", "Control_R": "RightControl",
    "Alt_L": "LeftAlt", "Alt_R": "RightAlt",
    "Minus": "Minus", "Equal": "Equal", "bracketleft": "BracketLeft",
    "bracketright": "BracketRight", "backslash": "Backslash", "semicolon": "Semicolon",
    "apostrophe": "Quote", "grave": "Backquote", "comma": "Comma",
    "period": "Period", "slash": "Slash", "Caps_Lock": "CapsLock",
}


def tk_to_duck(keysym: str) -> str:
    if not keysym:
        return ""
    if keysym in _TK_MAP:
        return _TK_MAP[keysym]
    if len(keysym) == 1:
        return keysym.upper()
    if keysym.startswith("F") and keysym[1:].isdigit():
        return keysym  # F1..F12
    if keysym.startswith("KP_"):
        rest = keysym[3:]
        return "Numpad" + (rest if len(rest) > 1 else rest.upper())
    # resto: capitalizar primera (ej: Delete -> Delete, Insert -> Insert)
    return keysym[:1].upper() + keysym[1:]
