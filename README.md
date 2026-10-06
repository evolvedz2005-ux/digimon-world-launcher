# Digimon World Vice PC

Launcher para jugar **Digimon World Vice** (hack 2.2 de Digimon World, PS1) en PC,
usando el emulador [DuckStation](https://www.duckstation.org/) que TÚ aportas.
Por Nyxen. ✦

## Descarga

Ve a [**Releases**](releases) y descarga `DigimonWorldVicePC-Launcher.zip`:
contiene el launcher (`Digimon World Vice PC.exe`), el `tutorial.txt` y el icono.
No incluye emulador, BIOS ni juego: debes aportarlos (ver tutorial).

## Primeros pasos

1. Descarga DuckStation **portable** (`duckstation-windows-x64-release.zip`) de
   [duckstation.org](https://www.duckstation.org/) y crea el archivo vacío
   `portable.txt` junto a su `.exe`.
2. Abre el launcher y completa el asistente: **Emulador → BIOS → Juego**.
   ⚠️ El juego tiene que ser región **USA** (SLUS-01032); otras regiones
   no están soportadas.
3. Pulsa **▶ JUGAR** una vez antes de tocar los gráficos (DuckStation debe
   crear su `settings.ini` primero).

Guía completa con rutas y solución de problemas en `tutorial.txt`.

## Funciones

- 🎮 Jugar con conteo "Entrando al mundo digital", pantalla completa (F11)
- 🎨 Gráficos: resolución, renderizador, filtros + presets (Rendimiento / Equilibrado / Ultra)
- 🎮 Mando: remapeo de teclado del Jugador 1 (mando USB vía DuckStation)
- 💾 BIOS: importar/cambiar tu `.bin` | 📦 Saves: respaldo y restauración
- 🔊 Volumen + turbo | 📷 Galería de capturas (F10) | 🔍 Diagnóstico del sistema

## Compilar desde el código

Necesitas Windows + Python 3.12+ (ver `COMPILAR.txt`):

```bat
cd launcher-py
pip install customtkinter pyinstaller pillow
pyinstaller DigimonWorldVicePC.spec --noconfirm
```

El `.exe` sale en `launcher-py\dist\`.

## Estructura

```
launcher-py/   código del launcher (ui.py + módulos)
tutorial.txt   guía de usuario
COMPILAR.txt   cómo compilar
```

## Créditos y legal

- Emulador: **DuckStation**, de Connor McLaughlin ([@stenzek](https://github.com/stenzek))
  y colaboradores. Licencia CC-BY-NC-ND 4.0: binarios originales sin
  modificar, uso no comercial. https://www.duckstation.org/
- Launcher: **Nyxen** — desarrollado 100% con inteligencia artificial,
  como prueba del desarrollo de programas con IA.
- "PlayStation" es marca de Sony Interactive Entertainment. Sin afiliación.
- Este proyecto **no incluye** emulador, BIOS ni juegos: todo lo aporta el
  usuario. No nos hacemos responsables del mal uso.
