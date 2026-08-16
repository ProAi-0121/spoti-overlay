# 🎵 Spoti Overlay

An always-on-top desktop overlay that shows the **currently playing media** (Spotify, YouTube, browsers, games, etc.), artist, and album art — right on top of whatever you're doing.

Built with Python and **tkinter**, using the **Windows Media Session API** (`winsdk`). No Spotify account or API keys required.

---

## Description

Spoti Overlay is a lightweight Windows desktop widget that mirrors whatever is currently playing on your system using the **Windows Media Session API**. It solves the problem of having to switch windows or check the app title bar just to see what song is playing — and it works with **any** media app (Spotify, YouTube, etc.), no authentication needed.
The overlay stays on top of your other windows, is configurable in position, colors, and opacity, and responds to global hotkeys and mouse clicks so you can control playback without leaving your current screen.

## IMAGES
- Settings/Home Page
<img width="1462" height="955" alt="image" src="https://github.com/user-attachments/assets/0ca2d332-a4b4-465a-ae81-6627d555d9ed" />

- Position Choosing
<img width="1338" height="850" alt="image" src="https://github.com/user-attachments/assets/8930dfea-3d1a-464d-bc51-bbb7a67b64cf" />

- Main OVERLAY
<img width="2461" height="1439" alt="image" src="https://github.com/user-attachments/assets/e15f84f6-d645-45f6-8a5d-8b6db3f677b1" />

- Right-Click On Overlay
<img width="720" height="510" alt="image" src="https://github.com/user-attachments/assets/dd6fb791-6743-473d-b1f7-52b97a590062" />


## Features

- ⬆️ **Always-on-top overlay** that stays visible while you work or play (borderless/frameless by default)
- 🎵 Shows the **current track, artist, and album artwork** from any app via the **Windows Media Session API** — no Spotify login
- 🖱️ **Left-click** the album art to toggle play / pause
- 📋 **Right-click** menu with Next Track, Previous Track, Overlay Mode, and Settings
  - **Overlay Mode** toggles the window border on/off (move it by the title bar when bordered)
- 🖥️ **Position picker** on a monitor image — click a corner to place the overlay (top-left, top-right, bottom-left, bottom-right)
- 🎴 **Settings window** organized into low-opacity, rounded category cards (POSITION, APPEARANCE, HOTKEYS)
- 🎨 Configurable **background color, font color, opacity, and overlay size**
- ⌨️ Global hotkeys (editable in Settings):
  - `Alt+H` — show / hide the overlay
  - `Alt+Right` — next track
  - `Alt+Left` — previous track
  - **Click-through hotkey** — optional, disabled by default; toggles mouse click-through
- 🔁 Auto-refreshes the now-playing info every few seconds
- 🧱 Packageable as a Windows `.exe` with PyInstaller (`spoti.spec`)

## Requirements

- **OS:** Windows (reads system media info via the Media Session API; playback control uses global media keys)
- **Python:** 3.8+ (developed on 3.11)

Python dependencies (see `requirements.txt`):

- `winsdk`
- `Pillow`
- `pyautogui`
- `keyboard`

## Installation

```bash
git clone https://github.com/ProAi-0121/spoti-overlay.git
cd spoti-overlay
```

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Configuration

Everything is configured in-app — you don't need any API keys or environment variables.

1. On the **Settings** window, choose where the overlay sits with **POSITION → Choose on monitor**, then click a corner.
2. Under **APPEARANCE** adjust the background color, font color, opacity, and overlay size.
3. Under **HOTKEYS** set your shortcuts (Show/Hide, Click-through, Next track, Prev track).
4. Click **OK** and the overlay appears.

> 💡 Long song titles are automatically cut off with an ellipsis so they never overflow the box. You can adjust how many words are shown with the *Title words* slider.

## Usage

Run the app:

```bash
python spoti.py
```

The settings window opens first so you can pick a position, colors, opacity, size, and hotkeys. Confirm it and the overlay appears — there is no login or OAuth step.

### Build a stand-alone Windows executable

```bash
pyinstaller spoti.spec
```

The executable is written to `dist/`.

## Project Structure

```
spoti-overlay/
├── spoti.py          # Main application (entry point)
├── spoti.spec        # PyInstaller build configuration
├── requirements.txt  # Python dependencies
├── .gitignore
├── icon.ico          # Application icon
├── bag.png           # UI asset (settings background)
├── bag2.png          # UI asset
├── example.png       # UI asset (position button icon)
├── monitor.png       # UI asset (position-picker monitor image)
├── ok.png            # UI asset
├── screen.png        # UI asset
└── top_left_image.png# UI asset
```

## Troubleshooting

**Nothing is shown on the overlay**
Make sure something is currently playing (in any app — Spotify, YouTube, a browser, etc.). If the media session is closed or paused, the overlay may show "No song playing".

**Play control (play/pause/next) doesn't work**
Confirm the global media keys aren't intercepted by another app (e.g. a laptop with a media-key Fn overlay or another media controller).

**The overlay stays in the way**
Right-click the overlay → **Overlay Mode** to turn on the window border so you can move it by the title bar, or press `Alt+H` to hide/show it.

**A hotkey doesn't do anything**
Hotkeys are validated and unparseable ones are skipped (and printed to the console). Make sure no other app has reserved that shortcut.

## License

No license has been added yet. If you would like to license this project, add a `LICENSE` file and reference it here. Contact the maintainer to choose a license.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.
