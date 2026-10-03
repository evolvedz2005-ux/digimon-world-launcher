"""Launcher Digimon World Vice PC — abre DuckStation directo, sin pedir BIOS.
La BIOS se autodetecta en ../duckstation-windows-x64-release/bios/
(portable.txt hace que DuckStation la use sin preguntar).
Uso: python launcher.py [--ventana] [--dry-run]

© Nyxen
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def get_data_dir():
    # Congelado (.exe): digimon_vice_data/ esta junto al exe.
    # Desarrollo: funciona este launcher-py dentro o fuera de digimon_vice_data/.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "digimon_vice_data"
    cand = BASE.parent
    if (cand / "vice").is_dir() or (cand / "duckstation-windows-x64-release").is_dir():
        return cand
    return cand / "digimon_vice_data"


DATA = get_data_dir()
EMU = DATA / "duckstation-windows-x64-release" / "duckstation-qt-x64-ReleaseLTCG.exe"
ROM = DATA / "vice" / "Digimon World Vice.cue"
BIOS_DIR = DATA / "duckstation-windows-x64-release" / "bios"

# Rutas configurables por el usuario (rutas.json). Si no existen,
# se usa el layout integrado anterior como compatibilidad.
from paths import resolve_emu, resolve_rom, bios_files


def check():
    emu = resolve_emu()
    rom = resolve_rom()
    return {"emu": emu is not None, "rom": rom is not None, "bios": len(bios_files()) > 0}


def build_cmd(fullscreen=True):
    emu = resolve_emu()
    rom = resolve_rom()
    args = ["-batch"]
    if fullscreen:
        args.append("-fullscreen")
    args.append(str(rom))
    return [str(emu)] + args


def main():
    fullscreen = "--ventana" not in sys.argv
    dry = "--dry-run" in sys.argv
    st = check()
    missing = [k for k, v in st.items() if not v]
    if missing:
        print("FALTA:", ", ".join(missing))
        print(f" emu: {EMU}\n rom: {ROM}\n bios dir: {BIOS_DIR}")
        sys.exit(1)
    cmd = build_cmd(fullscreen)
    if dry:
        print("DRY-RUN OK")
        print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
        return
    subprocess.Popen(cmd, close_fds=False)


if __name__ == "__main__":
    main()
