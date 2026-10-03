"""Fotos DuckStation — lista PNG/JPG de screenshots/ con tamaño y fecha.

© Nyxen
"""
from pathlib import Path

from paths import resolve_screenshots

VALID_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
PAGE_SIZE = 30


def _resolve(shots_dir=None) -> Path | None:
    if shots_dir is not None:
        return Path(shots_dir)
    return resolve_screenshots()


def list_photos(shots_dir=None) -> list:
    """[{'name', 'path', 'size', 'mtime'}] ordenadas: recientes primero."""
    out = []
    d = _resolve(shots_dir)
    if d is None:
        return out
    try:
        if d.is_dir():
            for f in d.iterdir():
                if f.is_file() and f.suffix.lower() in VALID_EXTS:
                    try:
                        st = f.stat()
                        out.append({"name": f.name, "path": str(f),
                                    "size": st.st_size, "mtime": st.st_mtime})
                    except OSError:
                        pass
    except Exception:
        pass
    out.sort(key=lambda d: d["mtime"], reverse=True)
    return out


def delete_photo(path: str | Path) -> dict:
    target = Path(path)
    base = resolve_screenshots()
    if base is None:
        return {"ok": False, "error": "Configura el emulador primero (asistente inicial)."}
    try:
        if target.resolve().parent != base.resolve():
            return {"ok": False, "error": "Ruta no válida."}
        target.unlink()
        return {"ok": True, "message": f"Foto eliminada: {target.name}"}
    except FileNotFoundError:
        return {"ok": False, "error": "La foto ya no existe."}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


def thumb_size(orig_w: int, orig_h: int, box: int = 160) -> tuple:
    if orig_w <= 0 or orig_h <= 0:
        return (box, box)
    scale = min(box / orig_w, box / orig_h, 1.0)
    return (max(1, int(orig_w * scale)), max(1, int(orig_h * scale)))
