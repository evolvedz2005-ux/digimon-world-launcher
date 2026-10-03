"""BIOS DuckStation — lista, importa y elimina .bin de la carpeta bios/.

© Nyxen
"""
import shutil
from pathlib import Path

from paths import resolve_bios_dir, import_bios_file

VALID_EXTS = {".bin"}
# BIOS PS1 tipica: 512 KiB
EXPECTED_SIZE = 512 * 1024


def _resolve(bios_dir=None) -> Path | None:
    if bios_dir is not None:
        return Path(bios_dir)
    return resolve_bios_dir()


def list_bios(bios_dir=None) -> list:
    out = []
    d = _resolve(bios_dir)
    if d is None:
        return out
    try:
        if d.is_dir():
            for f in sorted(d.iterdir()):
                if f.is_file() and f.suffix.lower() in VALID_EXTS:
                    out.append({"name": f.name, "size": f.stat().st_size})
    except Exception:
        pass
    return out


def import_bios(src: str | Path, bios_dir=None) -> dict:
    if bios_dir is None:
        return import_bios_file(src)
    src = Path(src)
    if not src.is_file():
        return {"ok": False, "error": f"No encuentro el archivo:\n{src}"}
    if src.suffix.lower() not in VALID_EXTS:
        return {"ok": False, "error": "La BIOS debe ser un archivo .bin"}
    try:
        dest_dir = Path(bios_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        size = src.stat().st_size
        dest = dest_dir / src.name
        if src.resolve() != dest.resolve():
            shutil.copyfile(src, dest)
        msg = f"BIOS instalada: {src.name} ({size // 1024} KB)."
        if size != EXPECTED_SIZE:
            msg += f" Ojo: tamaño distinto al esperado (512 KB)."
        return {"ok": True, "message": msg, "name": src.name}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


def delete_bios(name: str, bios_dir=None) -> dict:
    d = _resolve(bios_dir)
    if d is None:
        return {"ok": False, "error": "Configura el emulador primero (asistente inicial)."}
    target = d / name
    try:
        if not target.is_file():
            return {"ok": False, "error": f"No existe: {name}"}
        # evitar path traversal
        if target.resolve().parent != d.resolve():
            return {"ok": False, "error": "Nombre no válido."}
        target.unlink()
        return {"ok": True, "message": f"BIOS eliminada: {name}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
