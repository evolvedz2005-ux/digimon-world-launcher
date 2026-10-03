"""Graficos DuckStation — lee/escribe settings.ini sin romper otras claves.

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
    cp.optionxform = str  # preservar mayusculas (Renderer != renderer)
    try:
        p = _resolve(path)
        if p is not None and p.is_file():
            cp.read(p, encoding="utf-8")
    except Exception:
        pass
    return cp

ALLOWED_RENDERERS = ["Automatic", "D3D11", "D3D12", "Vulkan", "OpenGL", "Software"]
ALLOWED_FILTERS = ["Nearest", "Bilinear", "JINC2", "xBR"]
ALLOWED_ASPECTS = ["Auto (Game Native)", "4:3", "16:9"]
ALLOWED_SCALES = [0, 1, 2, 3, 4, 5, 6, 8, 9]

DEFAULTS = {
    "renderer": "Automatic",
    "resolution_scale": 1,
    "texture_filter": "Nearest",
    "widescreen": False,
    "pgxp": False,
    "vsync": False,
    "aspect_ratio": "Auto (Game Native)",
}


def _to_bool(v, default=False) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off"):
        return False
    return default


def get_graphics(path=None) -> dict:
    cp = _load_ini(path)
    g = dict(DEFAULTS)
    try:
        if cp.has_option("GPU", "Renderer"):
            r = cp.get("GPU", "Renderer").strip()
            g["renderer"] = r if r in ALLOWED_RENDERERS else DEFAULTS["renderer"]
        if cp.has_option("GPU", "ResolutionScale"):
            try:
                s = int(cp.get("GPU", "ResolutionScale"))
                g["resolution_scale"] = s if s in ALLOWED_SCALES else DEFAULTS["resolution_scale"]
            except ValueError:
                pass
        if cp.has_option("GPU", "TextureFilter"):
            f = cp.get("GPU", "TextureFilter").strip()
            g["texture_filter"] = f if f in ALLOWED_FILTERS else DEFAULTS["texture_filter"]
        if cp.has_option("GPU", "WidescreenHack"):
            g["widescreen"] = _to_bool(cp.get("GPU", "WidescreenHack"), False)
        if cp.has_option("GPU", "PGXPEnable"):
            g["pgxp"] = _to_bool(cp.get("GPU", "PGXPEnable"), False)
        if cp.has_option("Display", "VSync"):
            g["vsync"] = _to_bool(cp.get("Display", "VSync"), False)
        if cp.has_option("Display", "AspectRatio"):
            a = cp.get("Display", "AspectRatio").strip()
            g["aspect_ratio"] = a if a in ALLOWED_ASPECTS else DEFAULTS["aspect_ratio"]
    except Exception:
        pass
    return g


def set_graphics(values: dict, path=None) -> dict:
    """Valida y guarda. Devuelve {'ok': True} o {'ok': False, 'error': ...}."""
    renderer = str(values.get("renderer", DEFAULTS["renderer"])).strip()
    if renderer not in ALLOWED_RENDERERS:
        return {"ok": False, "error": f"Renderer no valido: {renderer}"}
    try:
        scale = int(values.get("resolution_scale", 1))
    except (ValueError, TypeError):
        return {"ok": False, "error": "Resolucion no valida."}
    if scale not in ALLOWED_SCALES:
        return {"ok": False, "error": f"Resolucion no valida: {scale}"}
    texture = str(values.get("texture_filter", "Nearest")).strip()
    if texture not in ALLOWED_FILTERS:
        return {"ok": False, "error": f"Filtro no valido: {texture}"}
    aspect = str(values.get("aspect_ratio", DEFAULTS["aspect_ratio"])).strip()
    if aspect not in ALLOWED_ASPECTS:
        return {"ok": False, "error": f"Aspecto no valido: {aspect}"}
    widescreen = bool(values.get("widescreen", False))
    pgxp = bool(values.get("pgxp", False))
    vsync = bool(values.get("vsync", False))

    p = _resolve(path)
    if p is None or not p.parent.is_dir():
        return {"ok": False, "error": "Configura el emulador primero (asistente inicial)."}
    if p.is_file():
        try:
            shutil.copyfile(p, p.with_suffix(".ini.bak"))
        except Exception:
            pass

    try:
        cp = _load_ini(p)
        for sec in ("GPU", "Display"):
            if not cp.has_section(sec):
                cp.add_section(sec)
        cp.set("GPU", "Renderer", renderer)
        cp.set("GPU", "ResolutionScale", str(scale))
        cp.set("GPU", "TextureFilter", texture)
        cp.set("GPU", "SpriteTextureFilter", texture)
        cp.set("GPU", "WidescreenHack", "true" if widescreen else "false")
        cp.set("GPU", "PGXPEnable", "true" if pgxp else "false")
        cp.set("Display", "VSync", "true" if vsync else "false")
        cp.set("Display", "AspectRatio", aspect)
        with open(p, "w", encoding="utf-8") as f:
            cp.write(f)
        return {"ok": True}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
