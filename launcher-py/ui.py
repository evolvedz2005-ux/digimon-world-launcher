"""UI Digimon World Vice PC — edicion rica (customtkinter).

© Nyxen
"""
import random
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
from launcher import check, build_cmd, DATA
from paths import (
    app_dir, set_ruta, resolve_emu, resolve_rom, resolve_bios_dir,
    resolve_screenshots, user_dir, validate_emu, validate_rom,
    import_bios_file, bios_files, all_ok,
)
from graphics import (
    get_graphics,
    set_graphics,
    ALLOWED_RENDERERS,
    ALLOWED_FILTERS,
    ALLOWED_ASPECTS,
)
from controls import (BUTTONS, DEFAULTS as PAD_DEFAULTS, get_controls, get_raw_bindings,
                      set_controls, tk_to_duck, get_hotkeys, set_hotkey, HOTKEY_DEFAULTS, HOTKEYS)
from bios import list_bios, import_bios, delete_bios
from saves import list_saves, fmt_size, fmt_date, backup_saves, restore_backup
from audio import get_audio, set_audio, TURBO_OPTIONS, TURBO_LABELS
from photos import list_photos, delete_photo, thumb_size, PAGE_SIZE
from health import run_checks, overall, report_text

BG = "#0b0f1a"
PANEL = "#131a2b"
EDGE = "#232f4d"
ORANGE = "#ff9b1a"
CYAN = "#35e0ff"
GREEN = "#00ff9d"
RED = "#ff3860"
DIM = "#8b93a7"
TEXT = "#eef3ff"

ctk.set_appearance_mode("dark")

root = ctk.CTk()
root.title("Digimon World Vice PC")
root.geometry("1000x780")
root.minsize(940, 700)
root.resizable(True, True)
root.configure(bg=BG)
try:
    _ico = next((p for p in (app_dir() / "dmw.ico", DATA / "dmw.ico") if p.is_file()), None)
    if _ico is not None:
        root.iconbitmap(str(_ico))
except Exception:  # noqa: BLE001
    pass

st = check()

# ============ BANNER MATRIX ============
banner = tk.Canvas(root, bg="#05080f", highlightthickness=0, bd=0, height=170)
banner.pack(fill="x")
GLYPHS = "01ABCDEF$#*+=<>VW01"
drops = []
for _cx in range(10, 990, 26):
    _hot = random.random() < 0.3
    _d = {"x": _cx, "y": random.randint(-170, 0), "speed": random.randint(5, 12)}
    _d["id"] = banner.create_text(
        _d["x"], _d["y"],
        text="\n".join(random.choice(GLYPHS) for _ in range(7)),
        font=("Consolas", 9), fill="#00ff9d" if _hot else "#14401f", justify="center",
    )
    drops.append(_d)
banner.create_text(500, 62, text="DIGIMON WORLD", font=("Segoe UI", 34, "bold"), fill="#eef3ff")
banner.create_text(500, 112, text="— V I C E · PC EDITION —", font=("Segoe UI", 13, "bold"), fill=ORANGE)
banner.create_text(992, 156, text="✦ Nyxen", font=("Segoe UI", 10, "bold"), fill="#8b93a7", anchor="e")
banner.create_rectangle(0, 166, 1000, 170, fill=ORANGE, outline="")


def tick():
    for _d in drops:
        _d["y"] += _d["speed"]
        if _d["y"] - 110 > 170:
            _d["y"] = random.randint(-120, -10)
            _d["speed"] = random.randint(5, 12)
            banner.itemconfig(_d["id"], text="\n".join(random.choice(GLYPHS) for _ in range(7)))
        banner.coords(_d["id"], _d["x"], _d["y"])
    root.after(90, tick)


tick()

# ============ CUERPO ============
_full = {"on": False}


def toggle_fullscreen(_e=None):
    _full["on"] = not _full["on"]
    root.attributes("-fullscreen", _full["on"])
    return "break"


def exit_fullscreen(_e=None):
    if _full["on"]:
        _full["on"] = False
        root.attributes("-fullscreen", False)


root.bind("<F11>", toggle_fullscreen)
root.bind("<Escape>", exit_fullscreen)

foot = ctk.CTkFrame(root, fg_color="transparent")
foot.pack(side="bottom", fill="x", padx=18, pady=(0, 8))
ctk.CTkLabel(foot, text="✦ Desarrollado por Nyxen", font=ctk.CTkFont(size=11),
             text_color=DIM).pack(side="left")
ctk.CTkButton(foot, text="⛶ Pantalla completa (F11)", width=220, fg_color="transparent",
              border_color=EDGE, border_width=1, text_color=TEXT,
              command=toggle_fullscreen).pack(side="right")
body = ctk.CTkFrame(root, fg_color=BG)
body.pack(fill="both", expand=True, padx=18, pady=(14, 6))

# ---- lateral: portada + estado ----
side = ctk.CTkFrame(body, fg_color=PANEL, border_color=EDGE, border_width=1,
                    width=250, corner_radius=14)
side.pack(side="left", fill="y", padx=(0, 14))
side.pack_propagate(False)

cover = tk.Canvas(side, bg="#0b0e18", highlightthickness=0, bd=0, height=190)
cover.pack(fill="x", padx=12, pady=12)
# digivice estilizado
cover.create_oval(75, 12, 175, 52, fill=ORANGE, outline="")
cover.create_oval(85, 20, 165, 44, fill="#0b0e18", outline="")
cover.create_text(125, 32, text="DW", font=("Segoe UI", 12, "bold"), fill=ORANGE)
cover.create_rectangle(60, 60, 190, 150, fill="#05080f", outline=CYAN, width=2)
cover.create_text(125, 92, text="DIGIMON", font=("Segoe UI", 13, "bold"), fill=CYAN)
cover.create_text(125, 116, text="WORLD VICE", font=("Segoe UI", 11, "bold"), fill=TEXT)
cover.create_text(125, 136, text="HACK 2.2", font=("Consolas", 9), fill=DIM)
cover.create_oval(40, 165, 52, 177, fill=GREEN, outline="")
cover.create_oval(198, 165, 210, 177, fill=RED, outline="")

ctk.CTkLabel(side, text="ESTADO DEL SISTEMA", font=ctk.CTkFont(size=11, weight="bold"),
             text_color=DIM).pack(anchor="w", padx=16)
st_refs = {}


def _status_label(key, ok, text):
    lbl = ctk.CTkLabel(side, text=f"● {text}: {'OK' if ok else 'FALTA'}",
                       font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                       text_color=GREEN if ok else RED)
    lbl.pack(anchor="w", padx=16, pady=1)
    st_refs[key] = (lbl, text)


_status_label("emu", st["emu"], "Emulador")
_status_label("rom", st["rom"], "Juego")
_status_label("bios", st["bios"], "BIOS auto")


def refresh_status():
    global st
    st = check()
    for key, ok in (("emu", st["emu"]), ("rom", st["rom"]), ("bios", st["bios"])):
        lbl, text = st_refs[key]
        lbl.configure(text=f"● {text}: {'OK' if ok else 'FALTA'}",
                      text_color=GREEN if ok else RED)
    try:
        play_btn.configure(state="normal" if all(st.values()) else "disabled")
    except Exception:  # noqa: BLE001
        pass  # play_btn aun no existe durante el arranque

fs_var = tk.BooleanVar(value=True)
ctk.CTkSwitch(side, text="Pantalla completa", variable=fs_var,
              progress_color=ORANGE, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=16, pady=(10, 4))


msg = None
gfx_msg = None
pad_msg = None
bios_msg = None


def open_duckstation():
    """Abre DuckStation para ajustes avanzados (mando USB, etc.)."""
    emu = resolve_emu()
    if emu is None:
        if msg is not None:
            msg.configure(text="Sin emulador: abre el asistente con 📂 Mis archivos.")
        return
    try:
        subprocess.Popen([str(emu)])
        txt = "DuckStation abierto: configura ahí tu mando USB o ajustes avanzados."
        if msg is not None:
            msg.configure(text=txt)
        if pad_msg is not None:
            pad_msg.configure(text=txt)
    except Exception as e:  # noqa: BLE001
        if msg is not None:
            msg.configure(text=f"Error: {e}")


def open_folder():
    import os
    rom = resolve_rom()
    if rom is None:
        if msg is not None:
            msg.configure(text="Sin juego: abre el asistente con 📂 Mis archivos.")
        return
    try:
        os.startfile(str(rom.parent))  # noqa: S606
        txt = f"Carpeta abierta: {rom.parent}"
        if msg is not None:
            msg.configure(text=txt)
    except Exception as e:  # noqa: BLE001
        if msg is not None:
            msg.configure(text=f"Error: {e}")


ctk.CTkButton(side, text="📁  Abrir carpeta", command=open_folder, fg_color="transparent",
              border_color=EDGE, border_width=1, text_color=TEXT,
              hover_color=EDGE).pack(fill="x", padx=14, pady=(8, 4))

# ---- principal con pestañas JUGAR | GRÁFICOS | MANDO | BIOS ----
main = ctk.CTkFrame(body, fg_color=PANEL, border_color=EDGE, border_width=1, corner_radius=14)
main.pack(side="left", fill="both", expand=True)

tabbar = ctk.CTkFrame(main, fg_color="transparent")
tabbar.pack(fill="x", padx=14, pady=(12, 6))
tabrow1 = ctk.CTkFrame(tabbar, fg_color="transparent")
tabrow1.pack(fill="x", pady=(0, 4))
tabrow2 = ctk.CTkFrame(tabbar, fg_color="transparent")
tabrow2.pack(fill="x")

tab_play = ctk.CTkButton(tabrow1, text="▶  JUGAR", width=90, fg_color=ORANGE,
                         text_color="#1a0e00", font=ctk.CTkFont(size=11, weight="bold"))
tab_gfx = ctk.CTkButton(tabrow1, text="🎨  GRÁFICOS", width=90, fg_color="transparent",
                        border_color=EDGE, border_width=1, text_color=TEXT,
                        font=ctk.CTkFont(size=11, weight="bold"))
tab_pad = ctk.CTkButton(tabrow1, text="🎮  MANDO", width=90, fg_color="transparent",
                        border_color=EDGE, border_width=1, text_color=TEXT,
                        font=ctk.CTkFont(size=11, weight="bold"))
tab_bios = ctk.CTkButton(tabrow2, text="💾  BIOS", width=90, fg_color="transparent",
                         border_color=EDGE, border_width=1, text_color=TEXT,
                         font=ctk.CTkFont(size=11, weight="bold"))
tab_saves = ctk.CTkButton(tabrow2, text="📦  SAVES", width=90, fg_color="transparent",
                          border_color=EDGE, border_width=1, text_color=TEXT,
                          font=ctk.CTkFont(size=11, weight="bold"))
tab_photos = ctk.CTkButton(tabrow2, text="📷  FOTOS", width=90, fg_color="transparent",
                           border_color=EDGE, border_width=1, text_color=TEXT,
                           font=ctk.CTkFont(size=11, weight="bold"))
tab_play.pack(side="left", expand=True, fill="x", padx=(0, 4))
tab_gfx.pack(side="left", expand=True, fill="x", padx=2)
tab_pad.pack(side="left", expand=True, fill="x", padx=(4, 0))
tab_bios.pack(side="left", expand=True, fill="x", padx=(0, 4))
tab_saves.pack(side="left", expand=True, fill="x", padx=2)
tab_photos.pack(side="left", expand=True, fill="x", padx=(4, 0))

view_play = ctk.CTkFrame(main, fg_color="transparent")
view_gfx = ctk.CTkFrame(main, fg_color="transparent")
view_pad = ctk.CTkFrame(main, fg_color="transparent")
view_bios = ctk.CTkFrame(main, fg_color="transparent")
view_saves = ctk.CTkFrame(main, fg_color="transparent")
view_photos = ctk.CTkFrame(main, fg_color="transparent")

ctk.CTkLabel(view_play, text="⚡  INCLUYE · VICE HACK 2.2", font=ctk.CTkFont(size=14, weight="bold"),
             text_color=ORANGE).pack(anchor="w", padx=18, pady=(4, 4))

plist = ctk.CTkScrollableFrame(view_play, fg_color="#0a0e18", border_color=EDGE,
                               border_width=1, height=170, corner_radius=10)
plist.pack(fill="x", padx=18)


def load_patches():
    try:
        lines = (DATA / "vice" / "Vice hack + parches.txt").read_text(encoding="utf-8").splitlines()
        items = [l.strip()[2:].strip() for l in lines if l.strip().startswith("- ")]
        if items:
            return items
    except Exception:  # noqa: BLE001
        pass
    return ["Inicio rápido", "Super crianza", "Muchas recompensas"]


for _p in load_patches():
    ctk.CTkLabel(plist, text=f"▸ {_p}", font=ctk.CTkFont(size=12),
                 text_color=TEXT).pack(anchor="w", padx=10, pady=1)

# ---- ajustes rápidos: volumen y turbo (guardan en settings.ini) ----
_audio = get_audio()
vol_var = tk.IntVar(value=_audio["volume"])
turbo_var = tk.StringVar(value=_audio.get("turbo_label", "Ilimitada"))

quick = ctk.CTkFrame(view_play, fg_color="#0a0e18", border_color=EDGE, border_width=1, corner_radius=10)
quick.pack(fill="x", padx=18, pady=(8, 0))
ctk.CTkLabel(quick, text="🔊", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10, 2))
vol_slider = ctk.CTkSlider(quick, from_=0, to=100, number_of_steps=100, variable=vol_var,
                           progress_color=ORANGE, width=150)
vol_slider.pack(side="left", padx=4)
vol_lbl = ctk.CTkLabel(quick, text=f"{_audio['volume']}%", font=ctk.CTkFont(family="Consolas", size=12),
                       text_color=CYAN, width=48)
vol_lbl.pack(side="left")
ctk.CTkLabel(quick, text="⏩ Turbo", font=ctk.CTkFont(size=12), text_color=TEXT).pack(side="left", padx=(10, 2))
turbo_menu = ctk.CTkOptionMenu(quick, variable=turbo_var, values=TURBO_LABELS, width=110,
                               fg_color=PANEL, button_color=ORANGE)
turbo_menu.pack(side="left", padx=(0, 10))


def _save_audio_quick():
    res = set_audio({"volume": int(vol_var.get()), "turbo": TURBO_OPTIONS.get(turbo_var.get(), 0.0)})
    if not res.get("ok") and msg is not None:
        msg.configure(text=f"Error audio: {res.get('error')}")


def _on_vol_move(_v):
    vol_lbl.configure(text=f"{int(float(_v))}%")


def _on_vol_release(_e):
    vol_lbl.configure(text=f"{vol_var.get()}%")
    _save_audio_quick()


vol_slider.configure(command=_on_vol_move)
vol_slider.bind("<ButtonRelease-1>", _on_vol_release)
turbo_menu.configure(command=lambda _c: _save_audio_quick())

# ---- TRUCOS: cheat Vice siempre activo (interruptor) ----
from cheats import get_cheat_state, set_cheat_enabled, CHEAT_NAME, CHEAT_DESC

cheat_var = tk.BooleanVar(value=True)

truco = ctk.CTkFrame(view_play, fg_color="#0a0e18", border_color=EDGE, border_width=1, corner_radius=10)
truco.pack(fill="x", padx=18, pady=(8, 0))
ctk.CTkLabel(truco, text="💊  TRUCOS", font=ctk.CTkFont(size=12, weight="bold"),
             text_color=ORANGE).pack(side="left", padx=(10, 2))
cheat_switch = ctk.CTkSwitch(truco, text=CHEAT_NAME, variable=cheat_var,
                             progress_color=ORANGE, font=ctk.CTkFont(size=12))
cheat_switch.pack(side="left", padx=4)
ctk.CTkButton(truco, text="📖  Descripción", width=110, fg_color="transparent",
              border_color=EDGE, border_width=1, text_color=CYAN,
              command=lambda: show_cheat_desc()).pack(side="right", padx=10)
ctk.CTkLabel(view_play, text="(Úsalo en partida nueva: no funciona en partidas ya creadas.)",
             font=ctk.CTkFont(size=11, weight="bold"), text_color=RED,
             wraplength=500, justify="left").pack(anchor="w", padx=20, pady=(4, 0))
ctk.CTkLabel(view_play, text="⚠ Cambia esto con DuckStation cerrado: abierto no se aplica.",
             font=ctk.CTkFont(size=11, weight="bold"), text_color=RED,
             wraplength=500, justify="left").pack(anchor="w", padx=20, pady=(0, 2))


def show_cheat_desc():
    win = ctk.CTkToplevel(root)
    win.title("Control de evolución")
    win.geometry("460x340")
    win.resizable(False, False)
    win.configure(fg_color=BG)
    ctk.CTkLabel(win, text="💊  Control de evolución",
                 font=ctk.CTkFont(size=15, weight="bold"), text_color=ORANGE).pack(pady=(14, 6))
    ctk.CTkLabel(win, text=CHEAT_DESC, font=ctk.CTkFont(size=12), text_color=TEXT,
                 wraplength=400, justify="left").pack(padx=16, pady=(0, 10))
    ctk.CTkButton(win, text="Cerrar", fg_color=ORANGE, text_color="#1a0e00",
                  command=win.destroy).pack(fill="x", padx=16, pady=(0, 14))


def _on_cheat_toggle():
    res = set_cheat_enabled(bool(cheat_var.get()))
    if msg is not None:
        msg.configure(text=res.get("message", res.get("error", "")))


cheat_switch.configure(command=_on_cheat_toggle)


def reload_cheat():
    stc = get_cheat_state()
    if not stc["available"]:
        cheat_switch.configure(state="disabled")
        cheat_var.set(False)
        return
    cheat_switch.configure(state="normal")
    # por defecto desactivado: el jugador lo activa con el interruptor
    cheat_var.set(bool(stc["installed"] and stc["enabled"]))


ctk.CTkButton(view_play, text="🔍  Diagnosticar sistema", command=lambda: open_diagnose(),
              fg_color="transparent", border_color=EDGE, border_width=1,
              text_color=TEXT).pack(fill="x", padx=18, pady=(6, 0))
ctk.CTkButton(view_play, text="📂  Mis archivos (emulador, BIOS, juego)",
              command=lambda: open_setup(),
              fg_color="transparent", border_color=EDGE, border_width=1,
              text_color=TEXT).pack(fill="x", padx=18, pady=(6, 0))

msg = ctk.CTkLabel(view_play, text="Acepta el reto y pulsa JUGAR.", font=ctk.CTkFont(size=12),
                   text_color=DIM, wraplength=480)
msg.pack(pady=(10, 2))


COUNT_COLORS = {5: "#00a651", 4: "#7cb342", 3: "#f9a825", 2: "#fb8c00", 1: "#e53935"}

count_frame = ctk.CTkFrame(view_play, fg_color="#eef3ff", corner_radius=16, height=140)
count_frame.pack_propagate(False)
count_msg = ctk.CTkLabel(count_frame, text="Entrando al mundo digital…",
                         font=ctk.CTkFont(size=22, weight="bold"), text_color="black")
count_msg.pack(pady=(14, 0))
count_num = ctk.CTkLabel(count_frame, text="5",
                         font=ctk.CTkFont(size=56, weight="bold"), text_color="#00a651")
count_num.pack(pady=(0, 8))

counting = {"active": False}


def play():
    if not all(st.values()):
        msg.configure(text="Falta emulador, juego o BIOS: usa 📂 Mis archivos.")
        return
    if counting["active"]:
        return  # ya hay un conteo en curso
    counting["active"] = True
    play_btn.pack_forget()
    count_frame.pack(fill="x", padx=18, pady=(10, 6))
    count = {"n": 5}

    def tick_count():
        if count["n"] > 0:
            count_num.configure(text=str(count["n"]), text_color=COUNT_COLORS[count["n"]])
            msg.configure(text=f"Entrando al mundo digital… {count['n']}", text_color="#eef3ff")
            count["n"] -= 1
            root.after(1000, tick_count)
        else:
            launch_game()

    def end_count():
        counting["active"] = False
        count_frame.pack_forget()
        play_btn.configure(text="▶  JUGAR", state="normal")
        play_btn.pack(fill="x", padx=18, pady=(10, 6))
        msg.configure(text_color=DIM)

    def launch_game():
        try:
            subprocess.Popen(build_cmd(fs_var.get()))
        except Exception as e:  # noqa: BLE001
            end_count()
            msg.configure(text=f"Error: {e}")
            return
        end_count()
        msg.configure(text="¡Ya estás dentro! Cambia a la ventana del emulador.")

    tick_count()


play_btn = ctk.CTkButton(view_play, text="▶  JUGAR", command=play, fg_color=ORANGE,
                         hover_color=CYAN, text_color="#1a0e00",
                         font=ctk.CTkFont(size=36, weight="bold"),
                         height=140, corner_radius=16)
play_btn.pack(fill="x", padx=18, pady=(10, 6))
ctk.CTkLabel(view_play, text="La BIOS se detecta sola · Progreso guardado en modo portable",
             font=ctk.CTkFont(size=11), text_color=DIM).pack(pady=(0, 10))

# ---- vista GRÁFICOS (edita settings.ini de DuckStation) ----
SCALE_OPTIONS = {
    "Automática": 0,
    "1x Nativa": 1,
    "2x": 2,
    "3x (720p)": 3,
    "4x": 4,
    "5x (1080p)": 5,
    "6x (1440p)": 6,
    "8x": 8,
    "9x (4K)": 9,
}
SCALE_LABELS = list(SCALE_OPTIONS.keys())
SCALE_VALUES = {v: k for k, v in SCALE_OPTIONS.items()}

gfx = get_graphics()

renderer_var = tk.StringVar(value=gfx["renderer"] if gfx["renderer"] in ALLOWED_RENDERERS else "Automatic")
_scale_label = SCALE_VALUES.get(gfx["resolution_scale"], "1x Nativa")
scale_var = tk.StringVar(value=_scale_label)
filter_var = tk.StringVar(value=gfx["texture_filter"] if gfx["texture_filter"] in ALLOWED_FILTERS else "Nearest")
aspect_var = tk.StringVar(value=gfx["aspect_ratio"] if gfx["aspect_ratio"] in ALLOWED_ASPECTS else ALLOWED_ASPECTS[0])
widescreen_var = tk.BooleanVar(value=bool(gfx["widescreen"]))
pgxp_var = tk.BooleanVar(value=bool(gfx["pgxp"]))
vsync_var = tk.BooleanVar(value=bool(gfx["vsync"]))

ctk.CTkLabel(view_gfx, text="🎨  OPCIONES GRÁFICAS · DuckStation",
             font=ctk.CTkFont(size=14, weight="bold"), text_color=ORANGE).pack(anchor="w", padx=18, pady=(4, 2))
ctk.CTkLabel(view_gfx, text="Se guardan en settings.ini. Cierra DuckStation antes de aplicar.",
             font=ctk.CTkFont(size=11), text_color=DIM).pack(anchor="w", padx=18, pady=(0, 8))

PRESETS = {
    "rendimiento": {"resolution_scale": 1, "texture_filter": "Nearest",
                    "widescreen": False, "pgxp": False, "vsync": False,
                    "aspect_ratio": "Auto (Game Native)"},
    "equilibrado": {"resolution_scale": 3, "texture_filter": "Bilinear",
                    "widescreen": False, "pgxp": True, "vsync": True,
                    "aspect_ratio": "Auto (Game Native)"},
    "ultra": {"resolution_scale": 5, "texture_filter": "Bilinear",
              "widescreen": False, "pgxp": True, "vsync": True,
              "aspect_ratio": "Auto (Game Native)"},
}


def apply_preset(name):
    vals = get_graphics()
    vals.update(PRESETS[name])
    res = set_graphics(vals)
    refresh_gfx_form(get_graphics())
    if gfx_msg is not None:
        if res.get("ok"):
            gfx_msg.configure(text=f"Preset {name} aplicado (resolución + filtro + PGXP + VSync).")
        else:
            gfx_msg.configure(text=f"Error: {res.get('error')}")


presetrow = ctk.CTkFrame(view_gfx, fg_color="transparent")
presetrow.pack(fill="x", padx=18, pady=(0, 8))
for _pname, _plabel in (("rendimiento", "⚡ Rendimiento"), ("equilibrado", "🎨 Equilibrado"), ("ultra", "💎 Ultra")):
    ctk.CTkButton(presetrow, text=_plabel, fg_color="transparent",
                  border_color=EDGE, border_width=1, text_color=TEXT,
                  command=lambda n=_pname: apply_preset(n)).pack(side="left", expand=True, fill="x", padx=3)

form = ctk.CTkFrame(view_gfx, fg_color="#0a0e18", border_color=EDGE, border_width=1, corner_radius=10)
form.pack(fill="x", padx=18)

_row = 0
ctk.CTkLabel(form, text="🎯 Resolución del juego", font=ctk.CTkFont(size=13, weight="bold"), text_color=ORANGE).grid(
    row=_row, column=0, sticky="w", padx=12, pady=6)
ctk.CTkOptionMenu(form, variable=scale_var, values=SCALE_LABELS,
                  fg_color=PANEL, button_color=ORANGE,
                  font=ctk.CTkFont(size=13, weight="bold")).grid(row=_row, column=1, sticky="ew", padx=12, pady=6)
_row += 1
ctk.CTkLabel(form, text="Renderizador", font=ctk.CTkFont(size=12), text_color=TEXT).grid(
    row=_row, column=0, sticky="w", padx=12, pady=6)
ctk.CTkOptionMenu(form, variable=renderer_var, values=ALLOWED_RENDERERS,
                  fg_color=PANEL, button_color=ORANGE).grid(row=_row, column=1, sticky="ew", padx=12, pady=6)
_row += 1
ctk.CTkLabel(form, text="Filtro de texturas", font=ctk.CTkFont(size=12), text_color=TEXT).grid(
    row=_row, column=0, sticky="w", padx=12, pady=6)
ctk.CTkOptionMenu(form, variable=filter_var, values=ALLOWED_FILTERS,
                  fg_color=PANEL, button_color=ORANGE).grid(row=_row, column=1, sticky="ew", padx=12, pady=6)
_row += 1
ctk.CTkLabel(form, text="Aspecto", font=ctk.CTkFont(size=12), text_color=TEXT).grid(
    row=_row, column=0, sticky="w", padx=12, pady=6)
ctk.CTkOptionMenu(form, variable=aspect_var, values=ALLOWED_ASPECTS,
                  fg_color=PANEL, button_color=ORANGE).grid(row=_row, column=1, sticky="ew", padx=12, pady=6)
form.grid_columnconfigure(1, weight=1)

ctk.CTkSwitch(view_gfx, text="Widescreen hack (16:9 real)", variable=widescreen_var,
              progress_color=ORANGE).pack(anchor="w", padx=20, pady=(8, 2))
ctk.CTkSwitch(view_gfx, text="PGXP (geometría sin temblor)", variable=pgxp_var,
              progress_color=ORANGE).pack(anchor="w", padx=20, pady=2)
ctk.CTkSwitch(view_gfx, text="VSync (evita tearing)", variable=vsync_var,
              progress_color=ORANGE).pack(anchor="w", padx=20, pady=2)

gfx_msg = ctk.CTkLabel(view_gfx, text="Listo.", font=ctk.CTkFont(size=12),
                       text_color=DIM, wraplength=480)
gfx_msg.pack(pady=(8, 2))

btnrow = ctk.CTkFrame(view_gfx, fg_color="transparent")
btnrow.pack(fill="x", padx=18, pady=(2, 10))
apply_btn = ctk.CTkButton(btnrow, text="💾  Aplicar gráficos", fg_color=ORANGE,
                          text_color="#1a0e00", font=ctk.CTkFont(size=13, weight="bold"))
reset_btn = ctk.CTkButton(btnrow, text="↺ Restablecer", fg_color="transparent",
                          border_color=EDGE, border_width=1, text_color=TEXT)
apply_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))
reset_btn.pack(side="left", expand=True, fill="x", padx=(6, 0))


def refresh_gfx_form(values: dict):
    renderer_var.set(values.get("renderer", "Automatic"))
    scale_var.set(SCALE_VALUES.get(values.get("resolution_scale", 1), "1x Nativa"))
    filter_var.set(values.get("texture_filter", "Nearest"))
    aspect_var.set(values.get("aspect_ratio", ALLOWED_ASPECTS[0]))
    widescreen_var.set(bool(values.get("widescreen", False)))
    pgxp_var.set(bool(values.get("pgxp", False)))
    vsync_var.set(bool(values.get("vsync", False)))


def apply_gfx():
    vals = {
        "renderer": renderer_var.get(),
        "resolution_scale": SCALE_OPTIONS.get(scale_var.get(), 1),
        "texture_filter": filter_var.get(),
        "widescreen": widescreen_var.get(),
        "pgxp": pgxp_var.get(),
        "vsync": vsync_var.get(),
        "aspect_ratio": aspect_var.get(),
    }
    res = set_graphics(vals)
    if res.get("ok"):
        gfx_msg.configure(text="Gráficos guardados en settings.ini. Tendrán efecto al abrir el juego.")
    else:
        gfx_msg.configure(text=f"Error: {res.get('error')}")


def reset_gfx():
    refresh_gfx_form(get_graphics())
    gfx_msg.configure(text="Valores recargados desde settings.ini.")


apply_btn.configure(command=apply_gfx)
reset_btn.configure(command=reset_gfx)


# ---- vista MANDO (remapa el teclado del Jugador 1 en settings.ini) ----
pad_pending = dict(get_controls())
pad_btns = {}
hk_pending = dict(get_hotkeys())
hk_btns = {}
capturing = {"target": None}

ctk.CTkLabel(view_pad, text="🎮  MANDO · Jugador 1 (teclado)",
             font=ctk.CTkFont(size=14, weight="bold"), text_color=ORANGE).pack(anchor="w", padx=18, pady=(4, 2))
pad_hint = ctk.CTkLabel(view_pad, text="Pulsa una tecla y luego pulsa la tecla nueva. Esc cancela.",
                        font=ctk.CTkFont(size=11), text_color=DIM)
pad_hint.pack(anchor="w", padx=18, pady=(0, 4))
pad_usb_hint = ctk.CTkLabel(view_pad, text="", font=ctk.CTkFont(size=11, weight="bold"),
                            text_color=CYAN, wraplength=500, justify="left")
pad_usb_hint.pack(anchor="w", padx=18)

pad_rows = ctk.CTkScrollableFrame(view_pad, fg_color="#0a0e18", border_color=EDGE,
                                  border_width=1, height=230, corner_radius=10)
pad_rows.pack(fill="x", padx=18, pady=(4, 0))


def _clear(frame):
    for w in frame.winfo_children():
        w.destroy()


def build_pad_rows():
    _clear(pad_rows)
    pad_btns.clear()
    for key, label in BUTTONS:
        row = ctk.CTkFrame(pad_rows, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=1)
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), text_color=TEXT,
                     width=220, anchor="w").pack(side="left")
        b = ctk.CTkButton(row, text=pad_pending.get(key, "?"), width=150,
                          fg_color=PANEL, border_color=EDGE, border_width=1, text_color=CYAN,
                          font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                          command=lambda k=key: start_capture("pad", k))
        b.pack(side="right")
        pad_btns[key] = b


def _target_text(kind, key):
    if kind == "pad":
        return pad_pending.get(key, "?")
    return hk_pending.get(key, "?")


def _target_button(kind, key):
    return pad_btns[key] if kind == "pad" else hk_btns[key]


def reload_pad_form():
    pad_pending.clear()
    pad_pending.update(get_controls())
    hk_pending.clear()
    hk_pending.update(get_hotkeys())
    build_pad_rows()
    build_hk_rows()
    raw = get_raw_bindings()
    usb = sorted(k for k, v in raw.items() if v and not v.startswith("Keyboard/"))
    if usb:
        pad_usb_hint.configure(
            text=f"⚠ {len(usb)} botones usan mando USB ({', '.join(usb)}). Al aplicar se cambiarán a teclado.")
    else:
        pad_usb_hint.configure(text="")
    if pad_msg is not None:
        pad_msg.configure(text="Listo. Pulsa una tecla para remapearla.")


def start_capture(kind, key):
    if capturing["target"] is not None:
        cancel_capture()
    capturing["target"] = (kind, key)
    _target_button(kind, key).configure(text="Pulsa tecla…")
    root.bind("<Key>", on_capture)
    root.focus_set()


def cancel_capture():
    target = capturing["target"]
    capturing["target"] = None
    try:
        root.unbind("<Key>")
    except Exception:  # noqa: BLE001
        pass
    if target is not None:
        kind, key = target
        try:
            _target_button(kind, key).configure(text=_target_text(kind, key))
        except Exception:  # noqa: BLE001
            pass  # filas aún no construidas


def on_capture(event):
    target = capturing["target"]
    if target is None:
        return "break"
    if event.keysym in ("Escape",):
        cancel_capture()
        return "break"
    duck = tk_to_duck(event.keysym)
    if not duck:
        return "break"
    kind, key = target
    if kind == "pad":
        pad_pending[key] = duck
    else:
        hk_pending[key] = duck
    capturing["target"] = None
    try:
        root.unbind("<Key>")
    except Exception:  # noqa: BLE001
        pass
    _target_button(kind, key).configure(text=duck)
    if pad_msg is not None:
        pad_msg.configure(text=f"{key} → {duck}. Pulsa Aplicar para guardar.")
    return "break"


def apply_pad():
    res = set_controls(pad_pending)
    hk_bad = ""
    for _name, _key in hk_pending.items():
        _r = set_hotkey(_name, _key)
        if not _r.get("ok"):
            hk_bad = _r.get("error", "")
            break
    if pad_msg is not None:
        if res.get("ok") and not hk_bad:
            pad_msg.configure(text=res.get("message", "") + " Atajos guardados.")
        elif not res.get("ok"):
            pad_msg.configure(text=res.get("error", ""))
        else:
            pad_msg.configure(text=hk_bad)
    reload_pad_rows_only()


def reload_pad_rows_only():
    for key, btn in pad_btns.items():
        btn.configure(text=pad_pending.get(key, "?"))
    for key, btn in hk_btns.items():
        btn.configure(text=hk_pending.get(key, "?"))


def reset_pad():
    pad_pending.clear()
    pad_pending.update(get_controls())
    hk_pending.clear()
    hk_pending.update(get_hotkeys())
    reload_pad_rows_only()
    if pad_msg is not None:
        pad_msg.configure(text="Valores recargados desde settings.ini.")


def default_pad():
    pad_pending.clear()
    pad_pending.update(dict(PAD_DEFAULTS))
    hk_pending.clear()
    hk_pending.update(dict(HOTKEY_DEFAULTS))
    reload_pad_rows_only()
    if pad_msg is not None:
        pad_msg.configure(text="Valores por defecto cargados. Pulsa Aplicar para guardar.")


HK_LABELS = {"FastForward": "⏩ Turbo (fast-forward)",
             "SaveSelectedSaveState": "💾 Guardar estado",
             "LoadSelectedSaveState": "📂 Cargar estado"}


def build_hk_rows():
    _clear(hk_rows)
    hk_btns.clear()
    for key, _label in HOTKEYS:
        row = ctk.CTkFrame(hk_rows, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=1)
        ctk.CTkLabel(row, text=HK_LABELS.get(key, key), font=ctk.CTkFont(size=12), text_color=TEXT,
                     width=220, anchor="w").pack(side="left")
        b = ctk.CTkButton(row, text=hk_pending.get(key, "?"), width=150,
                          fg_color=PANEL, border_color=EDGE, border_width=1, text_color=CYAN,
                          font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                          command=lambda k=key: start_capture("hk", k))
        b.pack(side="right")
        hk_btns[key] = b


hk_title = ctk.CTkLabel(view_pad, text="⌨️  ATAJOS DE TECLADO",
                        font=ctk.CTkFont(size=12, weight="bold"), text_color=ORANGE)
hk_title.pack(anchor="w", padx=18, pady=(8, 2))
hk_rows = ctk.CTkFrame(view_pad, fg_color="#0a0e18", border_color=EDGE,
                       border_width=1, corner_radius=10)
hk_rows.pack(fill="x", padx=18)
build_hk_rows()


pad_msg = ctk.CTkLabel(view_pad, text="Listo.", font=ctk.CTkFont(size=12),
                       text_color=DIM, wraplength=500)
pad_msg.pack(pady=(6, 2))

ctk.CTkLabel(view_pad, text="⚠ Cierra DuckStation antes de Aplicar: con el emulador abierto los cambios no se guardan.",
             font=ctk.CTkFont(size=11, weight="bold"), text_color=RED,
             wraplength=500, justify="left").pack(anchor="w", padx=18, pady=(6, 0))
padbtnrow = ctk.CTkFrame(view_pad, fg_color="transparent")
padbtnrow.pack(fill="x", padx=18, pady=(2, 6))
pad_apply = ctk.CTkButton(padbtnrow, text="💾  Aplicar mando", command=apply_pad,
                          fg_color=ORANGE, text_color="#1a0e00",
                          font=ctk.CTkFont(size=13, weight="bold"))
pad_reset = ctk.CTkButton(padbtnrow, text="↺ Recargar", command=reset_pad, fg_color="transparent",
                          border_color=EDGE, border_width=1, text_color=TEXT)
pad_default = ctk.CTkButton(padbtnrow, text="★ Por defecto", command=default_pad, fg_color="transparent",
                            border_color=EDGE, border_width=1, text_color=TEXT)
pad_apply.pack(side="left", expand=True, fill="x", padx=(0, 4))
pad_reset.pack(side="left", expand=True, fill="x", padx=4)
pad_default.pack(side="left", expand=True, fill="x", padx=(4, 0))
ctk.CTkButton(view_pad, text="🎛️  Abrir DuckStation (mando USB / avanzado)", command=open_duckstation,
              fg_color="transparent", border_color=EDGE, border_width=1,
              text_color=TEXT).pack(fill="x", padx=18, pady=(0, 8))

# ---- vista BIOS (cambia el .bin de la carpeta bios/) ----
ctk.CTkLabel(view_bios, text="💾  BIOS · PlayStation 1",
             font=ctk.CTkFont(size=14, weight="bold"), text_color=ORANGE).pack(anchor="w", padx=18, pady=(4, 2))
ctk.CTkLabel(view_bios, text="El juego usa la BIOS que esté en la carpeta bios/. Importa la tuya para cambiarla.",
             font=ctk.CTkFont(size=11), text_color=DIM, wraplength=500,
             justify="left").pack(anchor="w", padx=18, pady=(0, 6))

bios_rows = ctk.CTkScrollableFrame(view_bios, fg_color="#0a0e18", border_color=EDGE,
                                   border_width=1, height=150, corner_radius=10)
bios_rows.pack(fill="x", padx=18)


def refresh_bios_list():
    _clear(bios_rows)
    items = list_bios()
    if not items:
        ctk.CTkLabel(bios_rows, text="⚠ Sin BIOS: el juego no arrancará hasta importar una.",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color=RED).pack(padx=10, pady=10)
    for it in items:
        row = ctk.CTkFrame(bios_rows, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=3)
        kb = it["size"] // 1024
        mark = "✓" if it["size"] == 512 * 1024 else "?"
        ctk.CTkLabel(row, text=f"{mark} {it['name']} ({kb} KB)",
                     font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                     text_color=GREEN if mark == "✓" else ORANGE).pack(side="left")
        ctk.CTkButton(row, text="✕ Eliminar", width=100, fg_color="transparent",
                      border_color=EDGE, border_width=1, text_color=RED,
                      command=lambda n=it["name"]: delete_one_bios(n)).pack(side="right")


def delete_one_bios(name):
    if not messagebox.askyesno("Eliminar BIOS", f"¿Eliminar {name} de la carpeta bios/?"):
        return
    res = delete_bios(name)
    if bios_msg is not None:
        bios_msg.configure(text=res.get("message", res.get("error", "")))
    refresh_bios_list()
    refresh_status()


def import_one_bios():
    f = filedialog.askopenfilename(title="Elige la BIOS (.bin)",
                                   filetypes=[("BIOS PS1", "*.bin"), ("Todos", "*.*")])
    if not f:
        return
    res = import_bios(f)
    if bios_msg is not None:
        bios_msg.configure(text=res.get("message", res.get("error", "")))
    refresh_bios_list()
    refresh_status()


def open_bios_folder():
    import os
    d = resolve_bios_dir()
    if d is None:
        if bios_msg is not None:
            bios_msg.configure(text="Sin emulador: abre el asistente con 📂 Mis archivos.")
        return
    try:
        d.mkdir(parents=True, exist_ok=True)
        os.startfile(str(d))  # noqa: S606
    except Exception as e:  # noqa: BLE001
        if bios_msg is not None:
            bios_msg.configure(text=f"Error: {e}")


bios_msg = ctk.CTkLabel(view_bios, text="Listo.", font=ctk.CTkFont(size=12),
                        text_color=DIM, wraplength=500)
bios_msg.pack(pady=(8, 2))

biosbtnrow = ctk.CTkFrame(view_bios, fg_color="transparent")
biosbtnrow.pack(fill="x", padx=18, pady=(2, 10))
bios_import = ctk.CTkButton(biosbtnrow, text="📥  Cambiar / importar BIOS", command=import_one_bios,
                           fg_color=ORANGE, text_color="#1a0e00",
                           font=ctk.CTkFont(size=13, weight="bold"))
bios_folder_btn = ctk.CTkButton(biosbtnrow, text="📁 Carpeta", command=open_bios_folder,
                                fg_color="transparent", border_color=EDGE, border_width=1, text_color=TEXT)
bios_reload = ctk.CTkButton(biosbtnrow, text="↺ Recargar", command=refresh_bios_list,
                            fg_color="transparent", border_color=EDGE, border_width=1, text_color=TEXT)
bios_import.pack(side="left", expand=True, fill="x", padx=(0, 4))
bios_folder_btn.pack(side="left", expand=True, fill="x", padx=4)
bios_reload.pack(side="left", expand=True, fill="x", padx=(4, 0))

# ---- vista SAVES (memory cards + savestates: lista, respaldo, restaura) ----
ctk.CTkLabel(view_saves, text="📦  SAVES · partidas guardadas",
             font=ctk.CTkFont(size=14, weight="bold"), text_color=ORANGE).pack(anchor="w", padx=18, pady=(4, 2))
saves_count = ctk.CTkLabel(view_saves, text="", font=ctk.CTkFont(size=11), text_color=DIM)
saves_count.pack(anchor="w", padx=18, pady=(0, 4))

saves_rows = ctk.CTkScrollableFrame(view_saves, fg_color="#0a0e18", border_color=EDGE,
                                    border_width=1, height=210, corner_radius=10)
saves_rows.pack(fill="x", padx=18)


def refresh_saves_list():
    _clear(saves_rows)
    items = list_saves()
    if not items:
        ctk.CTkLabel(saves_rows, text="Sin partidas todavía: juega y guarda para verlas aquí.",
                     font=ctk.CTkFont(size=12), text_color=DIM).pack(padx=10, pady=10)
    for it in items:
        icon = "💾" if it["kind"] == "Memory card" else "⏺"
        ctk.CTkLabel(saves_rows,
                     text=f"{icon} [{it['kind']}] {it['name']} · {fmt_size(it['size'])} · {fmt_date(it['mtime'])}",
                     font=ctk.CTkFont(family="Consolas", size=11),
                     text_color=TEXT).pack(anchor="w", padx=10, pady=1)
    saves_count.configure(text=f"{len(items)} archivo(s). El respaldo copia todo a vice/respaldos/.")


def do_backup():
    res = backup_saves()
    if saves_msg is not None:
        saves_msg.configure(text=res.get("message", res.get("error", "")))
    refresh_saves_list()


def do_restore():
    d = filedialog.askdirectory(title="Elige la carpeta del respaldo (respaldo-...)")
    if not d:
        return
    if not messagebox.askyesno("Restaurar respaldo",
                                "Se copiarán los saves del respaldo a DuckStation, sobreescribiendo los actuales. ¿Seguir?"):
        return
    res = restore_backup(d)
    if saves_msg is not None:
        saves_msg.configure(text=res.get("message", res.get("error", "")))
    refresh_saves_list()


def open_saves_folder():
    import os
    u = user_dir()
    if u is None:
        if saves_msg is not None:
            saves_msg.configure(text="Sin emulador: abre el asistente con 📂 Mis archivos.")
        return
    try:
        os.startfile(str(u))  # noqa: S606
    except Exception as e:  # noqa: BLE001
        if saves_msg is not None:
            saves_msg.configure(text=f"Error: {e}")


saves_msg = ctk.CTkLabel(view_saves, text="Listo.", font=ctk.CTkFont(size=12),
                         text_color=DIM, wraplength=500)
saves_msg.pack(pady=(8, 2))

savesbtnrow = ctk.CTkFrame(view_saves, fg_color="transparent")
savesbtnrow.pack(fill="x", padx=18, pady=(2, 10))
saves_backup = ctk.CTkButton(savesbtnrow, text="📦  Crear respaldo", command=do_backup,
                             fg_color=ORANGE, text_color="#1a0e00",
                             font=ctk.CTkFont(size=13, weight="bold"))
saves_restore = ctk.CTkButton(savesbtnrow, text="↩ Restaurar", command=do_restore,
                              fg_color="transparent", border_color=EDGE, border_width=1, text_color=TEXT)
saves_folder_btn = ctk.CTkButton(savesbtnrow, text="📁 Carpeta", command=open_saves_folder,
                                 fg_color="transparent", border_color=EDGE, border_width=1, text_color=TEXT)
saves_backup.pack(side="left", expand=True, fill="x", padx=(0, 4))
saves_restore.pack(side="left", expand=True, fill="x", padx=4)
saves_folder_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

# ---- vista FOTOS (galería de screenshots/) ----
photos_shown = {"n": PAGE_SIZE}
photo_thumbs = {}

ctk.CTkLabel(view_photos, text="📷  FOTOS · capturas del juego (F10)",
             font=ctk.CTkFont(size=14, weight="bold"), text_color=ORANGE).pack(anchor="w", padx=18, pady=(4, 2))
photos_count = ctk.CTkLabel(view_photos, text="", font=ctk.CTkFont(size=11), text_color=DIM)
photos_count.pack(anchor="w", padx=18, pady=(0, 4))

photos_grid = ctk.CTkScrollableFrame(view_photos, fg_color="#0a0e18", border_color=EDGE,
                                     border_width=1, height=240, corner_radius=10)
photos_grid.pack(fill="x", padx=18)


def make_thumb(path):
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        img.thumbnail((160, 160))
        return ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
    except Exception:  # noqa: BLE001
        return None


def refresh_photos(reset=True):
    if reset:
        photos_shown["n"] = PAGE_SIZE
        photo_thumbs.clear()
    _clear(photos_grid)
    items = list_photos()
    if not items:
        ctk.CTkLabel(photos_grid, text="Sin fotos todavía: juega y pulsa F10 para capturar.",
                     font=ctk.CTkFont(size=12), text_color=DIM).pack(padx=10, pady=10)
    for it in items[:photos_shown["n"]]:
        cell = ctk.CTkFrame(photos_grid, fg_color="transparent")
        cell.pack(fill="x", padx=8, pady=4)
        thumb = make_thumb(it["path"])
        if thumb is not None:
            photo_thumbs[it["path"]] = thumb
            ctk.CTkLabel(cell, text="", image=thumb).pack(side="left", padx=(0, 10))
        else:
            ctk.CTkLabel(cell, text="🖼", font=ctk.CTkFont(size=28)).pack(side="left", padx=(0, 10))
        info = ctk.CTkFrame(cell, fg_color="transparent")
        info.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(info, text=it["name"][:40], font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text=f"{fmt_size(it['size'])} · {fmt_date(it['mtime'])}",
                     font=ctk.CTkFont(size=11), text_color=DIM, anchor="w").pack(anchor="w")
        btns = ctk.CTkFrame(cell, fg_color="transparent")
        btns.pack(side="right")
        ctk.CTkButton(btns, text="🔍 Ver", width=70, fg_color="transparent",
                      border_color=EDGE, border_width=1, text_color=CYAN,
                      command=lambda p=it["path"]: preview_photo(p)).pack(pady=1)
        ctk.CTkButton(btns, text="📁", width=70, fg_color="transparent",
                      border_color=EDGE, border_width=1, text_color=TEXT,
                      command=lambda p=it["path"]: open_photo(p)).pack(pady=1)
        ctk.CTkButton(btns, text="✕", width=70, fg_color="transparent",
                      border_color=EDGE, border_width=1, text_color=RED,
                      command=lambda p=it["path"]: delete_one_photo(p)).pack(pady=1)
    rest = len(items) - photos_shown["n"]
    if rest > 0:
        ctk.CTkButton(photos_grid, text=f"Ver más ({rest} restantes)", fg_color="transparent",
                      border_color=EDGE, border_width=1, text_color=CYAN,
                      command=show_more_photos).pack(pady=6)
    photos_count.configure(text=f"{len(items)} foto(s). Se toman con F10 dentro del juego.")


def show_more_photos():
    photos_shown["n"] += PAGE_SIZE
    refresh_photos(reset=False)


def open_photo(path):
    import os
    try:
        os.startfile(str(path))  # noqa: S606
    except Exception as e:  # noqa: BLE001
        if photos_msg is not None:
            photos_msg.configure(text=f"Error: {e}")


def delete_one_photo(path):
    if not messagebox.askyesno("Eliminar foto", f"¿Eliminar {Path(path).name}?"):
        return
    res = delete_photo(path)
    if photos_msg is not None:
        photos_msg.configure(text=res.get("message", res.get("error", "")))
    refresh_photos(reset=False)


def preview_photo(path):
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        img.thumbnail((820, 560))
        pic = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
    except Exception as e:  # noqa: BLE001
        if photos_msg is not None:
            photos_msg.configure(text=f"Error: {e}")
        return
    win = ctk.CTkToplevel(root)
    win.title(Path(path).name)
    win.configure(fg_color=BG)
    lbl = ctk.CTkLabel(win, text="", image=pic)
    lbl.image = pic
    lbl.pack(padx=12, pady=12)
    row = ctk.CTkFrame(win, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=(0, 12))
    ctk.CTkButton(row, text="📁 Abrir", fg_color="transparent", border_color=EDGE,
                  border_width=1, text_color=TEXT,
                  command=lambda: open_photo(path)).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ctk.CTkButton(row, text="✕ Eliminar", fg_color="transparent", border_color=EDGE,
                  border_width=1, text_color=RED,
                  command=lambda: (win.destroy(), delete_one_photo(path))).pack(
                      side="left", expand=True, fill="x", padx=4)
    ctk.CTkButton(row, text="Cerrar", fg_color=ORANGE, text_color="#1a0e00",
                  command=win.destroy).pack(side="left", expand=True, fill="x", padx=(4, 0))


def open_shots_folder():
    import os
    d = resolve_screenshots()
    if d is None:
        if photos_msg is not None:
            photos_msg.configure(text="Sin emulador: abre el asistente con 📂 Mis archivos.")
        return
    try:
        d.mkdir(parents=True, exist_ok=True)
        os.startfile(str(d))  # noqa: S606
    except Exception as e:  # noqa: BLE001
        if photos_msg is not None:
            photos_msg.configure(text=f"Error: {e}")


photos_msg = ctk.CTkLabel(view_photos, text="Listo.", font=ctk.CTkFont(size=12),
                          text_color=DIM, wraplength=500)
photos_msg.pack(pady=(8, 2))

photosbtnrow = ctk.CTkFrame(view_photos, fg_color="transparent")
photosbtnrow.pack(fill="x", padx=18, pady=(2, 10))
ctk.CTkButton(photosbtnrow, text="↺ Recargar", command=lambda: refresh_photos(reset=True),
              fg_color="transparent", border_color=EDGE, border_width=1,
              text_color=TEXT).pack(side="left", expand=True, fill="x", padx=(0, 4))
ctk.CTkButton(photosbtnrow, text="📁 Carpeta", command=open_shots_folder,
              fg_color="transparent", border_color=EDGE, border_width=1,
              text_color=TEXT).pack(side="left", expand=True, fill="x", padx=(4, 0))

# ---- diagnóstico (ventana emergente, solo lectura) ----
STATUS_COLOR = {"ok": GREEN, "warn": ORANGE, "bad": RED}
STATUS_ICON = {"ok": "●", "warn": "●", "bad": "●"}


def open_diagnose():
    checks = run_checks()
    status, summary = overall(checks)
    win = ctk.CTkToplevel(root)
    win.title("Diagnóstico del sistema")
    win.geometry("580x500")
    win.resizable(False, False)
    win.configure(fg_color=BG)
    ctk.CTkLabel(win, text="🔍  Diagnóstico del sistema",
                 font=ctk.CTkFont(size=15, weight="bold"), text_color=ORANGE).pack(pady=(14, 2))
    summ = ctk.CTkLabel(win, text=summary, font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=STATUS_COLOR.get(status, TEXT), wraplength=520)
    summ.pack(pady=(0, 8))
    box = ctk.CTkScrollableFrame(win, fg_color="#0a0e18", border_color=EDGE,
                                 border_width=1, height=280, corner_radius=10)
    box.pack(fill="x", padx=16)

    def fill(items):
        _clear(box)
        for c in items:
            col = STATUS_COLOR.get(c["status"], TEXT)
            ctk.CTkLabel(box, text=f"{STATUS_ICON.get(c['status'], '●')} {c['label']}",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=col, anchor="w").pack(anchor="w", padx=10, pady=(4, 0))
            ctk.CTkLabel(box, text=c["detail"], font=ctk.CTkFont(size=11),
                         text_color=DIM, anchor="w", wraplength=480,
                         justify="left").pack(anchor="w", padx=18, pady=(0, 2))

    fill(checks)

    def reload():
        items = run_checks()
        st2, summ2 = overall(items)
        summ.configure(text=summ2, text_color=STATUS_COLOR.get(st2, TEXT))
        fill(items)

    def copy_report():
        try:
            win.clipboard_clear()
            win.clipboard_append(report_text(run_checks()))
            summ.configure(text="Informe copiado al portapapeles.")
        except Exception as e:  # noqa: BLE001
            summ.configure(text=f"Error: {e}")

    row = ctk.CTkFrame(win, fg_color="transparent")
    row.pack(fill="x", padx=16, pady=12)
    ctk.CTkButton(row, text="↺ Recargar", command=reload, fg_color="transparent",
                  border_color=EDGE, border_width=1, text_color=TEXT).pack(
                      side="left", expand=True, fill="x", padx=(0, 4))
    ctk.CTkButton(row, text="📋 Copiar informe", command=copy_report, fg_color="transparent",
                  border_color=EDGE, border_width=1, text_color=TEXT).pack(
                      side="left", expand=True, fill="x", padx=4)
    ctk.CTkButton(row, text="Cerrar", command=win.destroy, fg_color=ORANGE,
                  text_color="#1a0e00").pack(side="left", expand=True, fill="x", padx=(4, 0))

# ---- navegación ----
VIEWS = {"play": view_play, "gfx": view_gfx, "pad": view_pad, "bios": view_bios, "saves": view_saves,
         "photos": view_photos}
TABS = {"play": tab_play, "gfx": tab_gfx, "pad": tab_pad, "bios": tab_bios, "saves": tab_saves,
        "photos": tab_photos}


def show_view(name):
    for v in VIEWS.values():
        v.pack_forget()
    VIEWS[name].pack(fill="both", expand=True, padx=0, pady=0)
    for n, btn in TABS.items():
        if n == name:
            btn.configure(fg_color=ORANGE, text_color="#1a0e00", border_width=0)
        else:
            btn.configure(fg_color="transparent", text_color=TEXT, border_width=1)
    if name == "gfx":
        refresh_gfx_form(get_graphics())
    elif name == "pad":
        reload_pad_form()
    elif name == "bios":
        refresh_bios_list()
    elif name == "saves":
        refresh_saves_list()
    elif name == "photos":
        refresh_photos(reset=True)
    elif name == "play":
        refresh_status()
        reload_cheat()


# ---- asistente inicial: el usuario aporta emulador, BIOS y juego ----
def open_setup():
    win = ctk.CTkToplevel(root)
    win.title("Primeros pasos — agrega tus archivos")
    win.geometry("600x560")
    win.resizable(False, False)
    win.configure(fg_color=BG)
    ctk.CTkLabel(win, text="📂  Agrega tus archivos",
                 font=ctk.CTkFont(size=15, weight="bold"), text_color=ORANGE).pack(pady=(14, 2))
    ctk.CTkLabel(win, text="El launcher no incluye emulador, BIOS ni juego: debes aportarlos. Ver tutorial.txt.",
                 font=ctk.CTkFont(size=11), text_color=DIM, wraplength=540).pack(pady=(0, 8))
    box = ctk.CTkFrame(win, fg_color="#0a0e18", border_color=EDGE, border_width=1, corner_radius=10)
    box.pack(fill="x", padx=16)

    rows = {}

    def add_row(key, title, hint):
        ctk.CTkLabel(box, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(box, text=hint, font=ctk.CTkFont(size=11),
                     text_color=DIM, anchor="w").pack(anchor="w", padx=12)
        r = ctk.CTkFrame(box, fg_color="transparent")
        r.pack(fill="x", padx=12, pady=(2, 6))
        pill = ctk.CTkLabel(r, text="…", font=ctk.CTkFont(family="Consolas", size=11),
                            text_color=DIM, anchor="w")
        pill.pack(side="left", expand=True, fill="x")
        rows[key] = pill
        return r

    r_emu = add_row("emu", "1 · Emulador DuckStation", "El archivo duckstation-qt-*.exe (descárgalo de duckstation.org).")
    r_bios = add_row("bios", "2 · BIOS de PlayStation", "Tu archivo .bin (512 KB). Se copia a la carpeta bios del emulador.")
    r_rom = add_row("rom", "3 · Juego", "Tu imagen: .cue, .iso, .chd, .m3u, .pbp o .ecm.")
    ctk.CTkButton(r_emu, text="Examinar…", width=110, fg_color=PANEL,
                  border_color=EDGE, border_width=1, text_color=TEXT,
                  command=lambda: pick_emu()).pack(side="right")
    ctk.CTkButton(r_bios, text="Importar…", width=110, fg_color=PANEL,
                  border_color=EDGE, border_width=1, text_color=TEXT,
                  command=lambda: pick_bios()).pack(side="right")
    ctk.CTkButton(r_rom, text="Examinar…", width=110, fg_color=PANEL,
                  border_color=EDGE, border_width=1, text_color=TEXT,
                  command=lambda: pick_rom()).pack(side="right")

    wmsg = ctk.CTkLabel(win, text="", font=ctk.CTkFont(size=12),
                        text_color=DIM, wraplength=540)
    wmsg.pack(pady=(8, 2))

    def refresh():
        emu = resolve_emu()
        rom = resolve_rom()
        names = bios_files()
        _set_row("emu", str(emu) if emu else "Sin elegir", emu is not None)
        _set_row("bios", ", ".join(names) if names else "Sin BIOS", len(names) > 0)
        _set_row("rom", str(rom) if rom else "Sin elegir", rom is not None)
        ok = all_ok()
        start_btn.configure(state="normal" if ok else "disabled")
        if ok:
            wmsg.configure(text="Todo listo. ¡A jugar!")
        return ok

    def _set_row(key, text, ok):
        short = text if len(text) <= 52 else "…" + text[-51:]
        rows[key].configure(text=("✓ " if ok else "✗ ") + short,
                            text_color=GREEN if ok else RED)

    def pick_emu():
        from pathlib import Path as _P
        f = filedialog.askopenfilename(title="Elige duckstation-qt-*.exe",
                                       filetypes=[("DuckStation", "*.exe"), ("Todos", "*.*")])
        if not f:
            return
        if not validate_emu(_P(f)):
            wmsg.configure(text="Ese archivo no parece el ejecutable de DuckStation.")
            return
        set_ruta("emu", f)
        wmsg.configure(text=f"Emulador guardado.")
        refresh()
        refresh_status()

    def pick_bios():
        f = filedialog.askopenfilename(title="Elige la BIOS (.bin)",
                                       filetypes=[("BIOS PS1", "*.bin"), ("Todos", "*.*")])
        if not f:
            return
        res = import_bios_file(f)
        wmsg.configure(text=res.get("message", res.get("error", "")))
        refresh()
        refresh_status()

    def pick_rom():
        from pathlib import Path as _P
        f = filedialog.askopenfilename(
            title="Elige tu juego",
            filetypes=[("Imágenes PS1", "*.cue *.iso *.chd *.m3u *.pbp *.ecm"), ("Todos", "*.*")])
        if not f:
            return
        if not validate_rom(_P(f)):
            wmsg.configure(text="Formato no soportado (usa .cue, .iso, .chd, .m3u, .pbp o .ecm).")
            return
        set_ruta("rom", f)
        wmsg.configure(text="Juego guardado.")
        refresh()
        refresh_status()

    start_btn = ctk.CTkButton(win, text="▶  Empezar", fg_color=ORANGE, text_color="#1a0e00",
                              font=ctk.CTkFont(size=14, weight="bold"),
                              command=win.destroy)
    start_btn.pack(fill="x", padx=16, pady=10)
    refresh()


tab_play.configure(command=lambda: show_view("play"))
tab_gfx.configure(command=lambda: show_view("gfx"))
tab_pad.configure(command=lambda: show_view("pad"))
tab_bios.configure(command=lambda: show_view("bios"))
tab_saves.configure(command=lambda: show_view("saves"))
tab_photos.configure(command=lambda: show_view("photos"))
show_view("play")

if not all(st.values()):
    msg.configure(text="Falta emulador, juego o BIOS: usa 📂 Mis archivos o el asistente.")

if not all_ok():
    open_setup()

root.mainloop()
