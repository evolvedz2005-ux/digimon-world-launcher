"""Saves DuckStation — lista, respalda y restaura memory cards y savestates.

© Nyxen
"""
import shutil
from datetime import datetime
from pathlib import Path

from paths import app_dir, resolve_memcards, resolve_savestates

BACKUPS_DIR = app_dir() / "respaldos"


def _iter_files(base):
    if base is None or not base.is_dir():
        return
    for f in sorted(base.rglob("*")):
        if f.is_file():
            yield f


def list_saves() -> list:
    """[{'kind': 'Memory card'|'Savestate', 'name', 'size', 'mtime'}]"""
    out = []
    for base, kind in ((resolve_memcards(), "Memory card"), (resolve_savestates(), "Savestate")):
        for f in _iter_files(base):
            try:
                st = f.stat()
                out.append({
                    "kind": kind,
                    "name": f.name,
                    "size": st.st_size,
                    "mtime": st.st_mtime,
                })
            except OSError:
                pass
    out.sort(key=lambda d: (d["kind"], d["name"]))
    return out


def fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n // 1024} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def fmt_date(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")


def backup_saves() -> dict:
    items = list_saves()
    if not items:
        return {"ok": False, "error": "No hay saves que respaldar."}
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUPS_DIR / f"respaldo-{stamp}"
    try:
        n = 0
        for base, sub in ((resolve_memcards(), "memcards"), (resolve_savestates(), "savestates")):
            if base is None or not base.is_dir():
                continue
            for f in _iter_files(base):
                target = dest / sub / f.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, target)
                n += 1
        return {"ok": True, "message": f"Respaldo creado ({n} archivos): respaldo-{stamp}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


def restore_backup(src: str | Path) -> dict:
    src = Path(src)
    if not src.is_dir():
        return {"ok": False, "error": "Carpeta de respaldo no válida."}
    files = [f for f in src.rglob("*") if f.is_file()]
    if not files:
        return {"ok": False, "error": "El respaldo está vacío."}
    try:
        n = 0
        memcards = resolve_memcards()
        savestates = resolve_savestates()
        if memcards is None or savestates is None:
            return {"ok": False, "error": "Configura el emulador primero (asistente inicial)."}
        for f in files:
            rel = f.relative_to(src)
            if rel.parts and rel.parts[0] == "memcards":
                dest = memcards / f.name
            elif rel.parts and rel.parts[0] == "savestates":
                dest = savestates / f.name
            else:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, dest)
            n += 1
        if n == 0:
            return {"ok": False, "error": "Nada que restaurar (formato desconocido)."}
        return {"ok": True, "message": f"Respaldo restaurado ({n} archivos)."}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
