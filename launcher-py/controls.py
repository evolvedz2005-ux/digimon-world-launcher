"""Mando DuckStation — lee/escribe [Pad1] de settings.ini (teclado y mando XInput).
Los bindings se guardan completos ("Keyboard/K", "XInput-0/A").

© Nyxen
"""
import configparser
import re
import shutil
from pathlib import Path

from paths import resolve_settings

_BINDING_RE = re.compile(r"^(Keyboard|XInput-\d+|SDL-\d+|DInput-\d+)/\S+$")

STICK_THRESHOLD = 15000
TRIGGER_THRESHOLD = 40


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
    "Up": "Keyboard/UpArrow", "Down": "Keyboard/DownArrow",
    "Left": "Keyboard/LeftArrow", "Right": "Keyboard/RightArrow",
    "Cross": "Keyboard/K", "Circle": "Keyboard/L",
    "Square": "Keyboard/J", "Triangle": "Keyboard/I",
    "Start": "Keyboard/Enter", "Select": "Keyboard/Backspace",
    "L1": "Keyboard/Q", "R1": "Keyboard/E",
    "L2": "Keyboard/1", "R2": "Keyboard/3",
    "L3": "Keyboard/2", "R3": "Keyboard/4",
    "LUp": "Keyboard/W", "LDown": "Keyboard/S",
    "LLeft": "Keyboard/A", "LRight": "Keyboard/D",
    "RUp": "Keyboard/T", "RDown": "Keyboard/G",
    "RLeft": "Keyboard/F", "RRight": "Keyboard/H",
}


def pretty_binding(full) -> str:
    """'Keyboard/K' -> 'K'; 'XInput-0/A' -> '🎮 A'."""
    s = str(full or "").strip()
    if "/" in s:
        dev, _, key = s.partition("/")
        if dev == "Keyboard":
            return key or s
        if dev.split("-")[0] in ("XInput", "SDL", "DInput"):
            return "🎮 " + (key or s)
        return key or s
    return s


def get_controls(path=None) -> dict:
    """Bindings completos de [Pad1], ej. {'Cross': 'Keyboard/K'}."""
    out = dict(DEFAULTS)
    try:
        cp = _load_ini(path)
        if cp.has_section("Pad1"):
            for k in BUTTON_KEYS:
                if cp.has_option("Pad1", k):
                    v = cp.get("Pad1", k).strip()
                    if v:
                        out[k] = v
    except Exception:
        pass
    return out


def get_raw_bindings(path=None) -> dict:
    """Alias de get_controls (compatibilidad)."""
    return get_controls(path)


def set_controls(values: dict, path=None) -> dict:
    cleaned = {}
    for k in BUTTON_KEYS:
        v = str(values.get(k, "")).strip()
        if not v:
            return {"ok": False, "error": f"Falta tecla/botón para {k}."}
        if len(v) > 48 or not _BINDING_RE.match(v):
            return {"ok": False, "error": f"Binding no válido para {k}: {v}"}
        cleaned[k] = v
    # avisar duplicados (no bloquea, pero informa)
    seen = {}
    dupes = set()
    for k, v in cleaned.items():
        if v in seen:
            dupes.add(pretty_binding(v))
        else:
            seen[v] = k
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
            cp.set("Pad1", k, cleaned[k])
        if any(v.startswith("XInput-") for v in cleaned.values()):
            if not cp.has_section("InputSources"):
                cp.add_section("InputSources")
            cp.set("InputSources", "XInput", "true")
        with open(p, "w", encoding="utf-8") as f:
            cp.write(f)
        msg = "Mando guardado en settings.ini."
        if dupes:
            msg += f" Ojo: repetido ({', '.join(sorted(dupes))})."
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
                    v = cp.get("Hotkeys", k).strip()
                    if "/" in v:
                        v = v.split("/", 1)[1].strip() or v
                    if v:
                        out[k] = v
    except Exception:
        pass
    return out


def set_hotkey(name: str, key: str, path=None) -> dict:
    if name not in HOTKEY_DEFAULTS:
        return {"ok": False, "error": f"Atajo no válido: {name}"}
    key = str(key or "").strip()
    if "/" in key:
        if len(key) > 48 or not _BINDING_RE.match(key):
            return {"ok": False, "error": f"Binding no válido para {name}: {key}"}
        full = key
    else:
        if not key or len(key) > 32 or any(c in key for c in "= \t\n\r"):
            return {"ok": False, "error": f"Tecla no válida para {name}."}
        full = f"Keyboard/{key}"
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
        cp.set("Hotkeys", name, full)
        if full.startswith("XInput-"):
            if not cp.has_section("InputSources"):
                cp.add_section("InputSources")
            cp.set("InputSources", "XInput", "true")
        with open(p, "w", encoding="utf-8") as f:
            cp.write(f)
        return {"ok": True, "message": f"Atajo guardado: {name} = {pretty_binding(full)}."}
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


# Botones XInput en orden de prioridad (máscara, nombre DuckStation)
XINPUT_BUTTONS = [
    (0x0001, "DPadUp"), (0x0002, "DPadDown"),
    (0x0004, "DPadLeft"), (0x0008, "DPadRight"),
    (0x0010, "Start"), (0x0020, "Back"),
    (0x0100, "LeftShoulder"), (0x0200, "RightShoulder"),
    (0x0040, "LeftStick"), (0x0080, "RightStick"),
    (0x1000, "A"), (0x2000, "B"), (0x4000, "X"), (0x8000, "Y"),
    (0x0400, "Guide"),
]

_xinput_dll = None


def _get_xinput_dll():
    global _xinput_dll
    if _xinput_dll is not None:
        return _xinput_dll
    import ctypes

    for name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
        try:
            _xinput_dll = ctypes.WinDLL(name)
            return _xinput_dll
        except OSError:
            pass
    _xinput_dll = False
    return False


def _read_pad(index: int):
    """Devuelve dict con botones/ejes o None si desconectado."""
    import ctypes

    dll = _get_xinput_dll()
    if not dll:
        return None

    class _Pad(ctypes.Structure):
        _fields_ = [("buttons", ctypes.c_ushort),
                    ("lt", ctypes.c_ubyte), ("rt", ctypes.c_ubyte),
                    ("lx", ctypes.c_short), ("ly", ctypes.c_short),
                    ("rx", ctypes.c_short), ("ry", ctypes.c_short)]

    class _State(ctypes.Structure):
        _fields_ = [("packet", ctypes.c_ulong), ("gamepad", _Pad)]

    try:
        st = _State()
        if dll.XInputGetState(index, ctypes.byref(st)) != 0:
            return None
        g = st.gamepad
        return {"buttons": g.buttons, "lt": g.lt, "rt": g.rt,
                "lx": g.lx, "ly": g.ly, "rx": g.rx, "ry": g.ry}
    except Exception:
        return None


def pad_pressed_suffixes(index: int):
    """Sufijos DuckStation pulsados ahora en ese mando (set, ordenado)."""
    st = _read_pad(index)
    if st is None:
        return None
    out = []
    for mask, name in XINPUT_BUTTONS:
        if st["buttons"] & mask:
            out.append(name)
    if st["lt"] > TRIGGER_THRESHOLD:
        out.append("+LeftTrigger")
    if st["rt"] > TRIGGER_THRESHOLD:
        out.append("+RightTrigger")
    # Y invertido en XInput respecto a SDL: arriba físico = -LeftY
    if st["lx"] > STICK_THRESHOLD:
        out.append("+LeftX")
    elif st["lx"] < -STICK_THRESHOLD:
        out.append("-LeftX")
    if st["ly"] > STICK_THRESHOLD:
        out.append("-LeftY")
    elif st["ly"] < -STICK_THRESHOLD:
        out.append("+LeftY")
    if st["rx"] > STICK_THRESHOLD:
        out.append("+RightX")
    elif st["rx"] < -STICK_THRESHOLD:
        out.append("-RightX")
    if st["ry"] > STICK_THRESHOLD:
        out.append("-RightY")
    elif st["ry"] < -STICK_THRESHOLD:
        out.append("+RightY")
    return set(out)


def first_connected_pad():
    """Índice del primer mando conectado o None."""
    for i in range(4):
        if _read_pad(i) is not None:
            return i
    return None


def count_xinput_pads() -> int | None:
    """N° de mandos XInput conectados (None si no se pudo comprobar)."""
    if not _get_xinput_dll():
        return None
    n = 0
    for i in range(4):
        if _read_pad(i) is not None:
            n += 1
    return n
