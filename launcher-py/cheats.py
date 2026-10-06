"""Trucos DuckStation — cheat Vice siempre activo (con interruptor).
Escribe cheats/SLUS-01032-PC.cht (fusionando el bloque, sin borrar
otros cheats) y gamesettings/SLUS-01032.ini ([Cheats] EnableCheats +
lista Enable de líneas repetidas, preservando el resto).

© Nyxen
"""
import shutil
from pathlib import Path

from paths import resolve_cheats, resolve_gamesettings

SERIAL = "SLUS-01032"
CHT_FILENAME = "SLUS-01032-PC.cht"
CHEAT_NAME = "Control de evolución"
LEGACY_NAMES = ["AutoEvo General R1+Select"]
GAME_INI = "SLUS-01032.ini"

CHEAT_BLOCK = """[Control de evolución]
Type = Gameshark
Activation = EndFrame
Description = Controla la evolución de tu Digimon: pulsa R1+Select en campo. Limpia bloqueo de carga y evoTimer=144. (Usar en partida nueva.)
Author = Nyxen
D4000000 0108
80134CA8 0000
D4000000 0108
801384B6 0090"""

CHEAT_DESC = (
    "💊 TRUCOS (Control de evolución, R1+Select): truco que ayuda a "
    "controlar la evolución y evolucionar a placer, ya sin errores. En "
    "partida nueva actúa al momento; tras cargar partida el temporizador "
    "debe descontarse en tiempo de juego al usarse el cheat.\n\n"
    "• Úsalo en partida nueva: no funciona en partidas ya creadas.\n"
    "• Para activar o desactivar, cierra DuckStation primero."
)


def _is_ours(name: str) -> bool:
    return name == CHEAT_NAME or name in LEGACY_NAMES


def _cheat_path() -> Path | None:
    d = resolve_cheats()
    return d / CHT_FILENAME if d is not None else None


def _ini_path() -> Path | None:
    d = resolve_gamesettings()
    return d / GAME_INI if d is not None else None


def _merge_cht_block(text: str) -> str:
    """Reemplaza nuestro bloque [nombre] (nuevo o antiguo) o lo agrega."""
    lines = text.splitlines()
    out, i, found = [], 0, False
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("[") and s.endswith("]") and len(s) > 2 and s[1:-1] in (CHEAT_NAME, *LEGACY_NAMES):
            found = True
            i += 1
            while i < len(lines):
                s = lines[i].strip()
                if s.startswith("[") and s.endswith("]") and len(s) > 2:
                    break
                i += 1
            out.extend(CHEAT_BLOCK.splitlines())
            continue
        out.append(lines[i])
        i += 1
    if not found:
        if out and out[-1].strip() != "":
            out.append("")
        out.extend(CHEAT_BLOCK.splitlines())
    return "\n".join(out) + "\n"


def _read_enable_list(text: str) -> tuple:
    """Devuelve (enable_cheats: bool|None, [nombres en Enable])."""
    flag, names, in_cheats = None, [], False
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("[") and s.endswith("]") and len(s) > 2:
            in_cheats = s[1:-1].strip().lower() == "cheats"
            continue
        if in_cheats and "=" in s and not s.startswith((";", "#")):
            k, _, v = s.partition("=")
            kl = k.strip().lower()
            if kl == "enablecheats":
                flag = v.strip().lower() in ("1", "true", "yes", "on")
            elif kl == "enable" and v.strip():
                names.append(v.strip())
    return flag, names


def _apply_ini(text: str, enable: bool) -> str:
    """Fusiona [Cheats]: flag + lista Enable (repetidas), resto intacto."""
    _, others = _read_enable_list(text)
    others = [n for n in others if not _is_ours(n)]
    lines = text.splitlines()
    # quitar EnableCheats/Enable previos dentro de [Cheats]
    out, in_cheats = [], False
    for ln in lines:
        s = ln.strip()
        if s.startswith("[") and s.endswith("]") and len(s) > 2:
            in_cheats = s[1:-1].strip().lower() == "cheats"
            out.append(ln)
            continue
        if in_cheats and "=" in s and not s.startswith((";", "#")):
            if s.partition("=")[0].strip().lower() in ("enablecheats", "enable"):
                continue
        out.append(ln)
    # índice de inserción: final de la sección [Cheats]
    has_section, idx, in_cheats = False, len(out), False
    for i, ln in enumerate(out):
        s = ln.strip()
        if s.startswith("[") and s.endswith("]") and len(s) > 2:
            if in_cheats:
                idx = i
                break
            in_cheats = s[1:-1].strip().lower() == "cheats"
            if in_cheats:
                has_section = True
                idx = i + 1
        elif in_cheats:
            idx = i + 1
    if not has_section:
        out.append("[Cheats]")
        idx = len(out)
    names = ([CHEAT_NAME] + others) if enable else others
    block = ["EnableCheats = true" if (enable or others) else "EnableCheats = false"]
    block.extend(f"Enable = {n}" for n in names)
    out[idx:idx] = block
    return "\n".join(out) + "\n"


def get_cheat_state() -> dict:
    """{available, installed, enabled}."""
    cp, ip = _cheat_path(), _ini_path()
    if cp is None or ip is None:
        return {"available": False, "installed": False, "enabled": False}
    installed = False
    if cp.is_file():
        txt = cp.read_text(encoding="utf-8", errors="ignore")
        installed = any(f"[{n}]" in txt for n in (CHEAT_NAME, *LEGACY_NAMES))
    enabled = False
    if ip.is_file():
        flag, names = _read_enable_list(ip.read_text(encoding="utf-8", errors="ignore"))
        enabled = bool(flag) and any(_is_ours(n) for n in names)
    return {"available": True, "installed": installed, "enabled": enabled}


def set_cheat_enabled(on: bool) -> dict:
    cp, ip = _cheat_path(), _ini_path()
    if cp is None or ip is None:
        return {"ok": False, "error": "Configura el emulador primero (asistente inicial)."}
    try:
        cp.parent.mkdir(parents=True, exist_ok=True)
        ip.parent.mkdir(parents=True, exist_ok=True)
        cur = cp.read_text(encoding="utf-8", errors="ignore") if cp.is_file() else ""
        if cp.is_file():
            shutil.copyfile(cp, cp.with_suffix(".cht.bak"))
        cp.write_text(_merge_cht_block(cur), encoding="utf-8")
        cur_ini = ip.read_text(encoding="utf-8", errors="ignore") if ip.is_file() else ""
        if ip.is_file():
            shutil.copyfile(ip, ip.with_suffix(".ini.bak"))
        ip.write_text(_apply_ini(cur_ini, on), encoding="utf-8")
        return {"ok": True, "message": "Control de evolución activado." if on
                else "Control de evolución desactivado (tu archivo se conserva)."}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
