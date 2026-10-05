"""Rutas configurables — el launcher NO incluye emulador, BIOS ni juego.
El usuario aporta los 3 archivos; las rutas se guardan en rutas.json
junto al exe (portable). Si no hay rutas pero existe el layout
integrado anterior, se usa este como compatibilidad.

© Nyxen
"""
import json
import os
import sys
from pathlib import Path

ROM_EXTS = {".cue", ".iso", ".chd", ".m3u", ".pbp", ".ecm"}
BIOS_EXT = ".bin"


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundled_base() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "digimon_vice_data"
    return Path(__file__).resolve().parent.parent


def bundled_emu() -> Path:
    return bundled_base() / "duckstation-windows-x64-release" / "duckstation-qt-x64-ReleaseLTCG.exe"


def bundled_rom() -> Path:
    return bundled_base() / "vice" / "Digimon World Vice.cue"


def bundled_bios_dir() -> Path:
    return bundled_base() / "duckstation-windows-x64-release" / "bios"


RUTAS_FILE = app_dir() / "rutas.json"


def load_rutas() -> dict:
    try:
        if RUTAS_FILE.is_file():
            d = json.loads(RUTAS_FILE.read_text(encoding="utf-8"))
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}


def save_rutas(d: dict) -> bool:
    try:
        RUTAS_FILE.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False


def set_ruta(key: str, value: str) -> bool:
    d = load_rutas()
    d[key] = value
    return save_rutas(d)


def resolve_emu() -> Path | None:
    r = load_rutas()
    if r.get("emu"):
        p = Path(r["emu"])
        if p.is_file():
            return p
    b = bundled_emu()
    return b if b.is_file() else None


def resolve_rom() -> Path | None:
    r = load_rutas()
    if r.get("rom"):
        p = Path(r["rom"])
        if p.is_file():
            return p
    b = bundled_rom()
    return b if b.is_file() else None


def is_portable(emu: Path) -> bool:
    try:
        return (emu.parent / "portable.txt").is_file()
    except Exception:
        return False


def user_dir() -> Path | None:
    """Carpeta de datos de DuckStation (settings, bios, saves)."""
    e = resolve_emu()
    if e is not None:
        if is_portable(e):
            return e.parent
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local) / "DuckStation"
        return e.parent
    b = bundled_base() / "duckstation-windows-x64-release"
    return b if b.is_dir() else None


def resolve_bios_dir() -> Path | None:
    e = resolve_emu()
    if e is not None:
        if is_portable(e):
            return e.parent / "bios"
        u = user_dir()
        return u / "bios" if u is not None else None
    b = bundled_bios_dir()
    return b if b.is_dir() else None


def resolve_settings() -> Path | None:
    u = user_dir()
    return u / "settings.ini" if u is not None else None


def resolve_memcards() -> Path | None:
    u = user_dir()
    return u / "memcards" if u is not None else None


def resolve_savestates() -> Path | None:
    u = user_dir()
    return u / "savestates" if u is not None else None


def resolve_screenshots() -> Path | None:
    u = user_dir()
    return u / "screenshots" if u is not None else None


def resolve_cheats() -> Path | None:
    u = user_dir()
    return u / "cheats" if u is not None else None


def resolve_gamesettings() -> Path | None:
    u = user_dir()
    return u / "gamesettings" if u is not None else None


def bios_files() -> list:
    d = resolve_bios_dir()
    if d is None or not d.is_dir():
        return []
    try:
        return sorted(f.name for f in d.iterdir() if f.is_file() and f.suffix.lower() == BIOS_EXT)
    except Exception:
        return []


def all_ok() -> bool:
    e = resolve_emu()
    r = resolve_rom()
    return bool(e is not None and r is not None and len(bios_files()) > 0)


def validate_emu(p: Path) -> bool:
    try:
        return p.is_file() and p.suffix.lower() == ".exe" and p.name.lower().startswith("duckstation")
    except Exception:
        return False


def validate_rom(p: Path) -> bool:
    try:
        return p.is_file() and p.suffix.lower() in ROM_EXTS
    except Exception:
        return False


def import_bios_file(src: str | Path) -> dict:
    """Copia un .bin a la carpeta bios del emulador configurado."""
    import shutil
    src = Path(src)
    if not src.is_file():
        return {"ok": False, "error": "Elige un archivo válido."}
    if src.suffix.lower() != BIOS_EXT:
        return {"ok": False, "error": "La BIOS debe ser un archivo .bin"}
    dest_dir = resolve_bios_dir()
    if dest_dir is None:
        # sin emulador aún: usa la integrada si existe para no perder el archivo
        b = bundled_bios_dir()
        dest_dir = b if b.is_dir() or resolve_emu() is None and b.parent.is_dir() else None
        if dest_dir is None:
            return {"ok": False, "error": "Configura el emulador primero (paso 1)."}
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        size = src.stat().st_size
        dest = dest_dir / src.name
        if src.resolve() != dest.resolve():
            shutil.copyfile(src, dest)
        msg = f"BIOS instalada: {src.name} ({size // 1024} KB)."
        if size != 512 * 1024:
            msg += " Ojo: tamaño distinto al esperado (512 KB)."
        return {"ok": True, "message": msg, "name": src.name}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
