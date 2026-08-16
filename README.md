# 🎵 Spoti Overlay

An always-on-top, frameless desktop overlay that shows the **currently playing Spotify track**, artist, and album art — right on top of whatever you're doing.

Built with Python, **PyQt5**, and **Spotipy**.

---

## Description

Spoti Overlay is a lightweight Windows desktop widget that mirrors the now-playing info from your Spotify account using the Spotify Web API. It solves the problem of having to switch windows or check the Spotify title bar just to see what song is playing.
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

- ⬆️ **Always-on-top, frameless overlay** that stays visible while you work or play

- 🎵 Displays the **current track, artist, and album artwork**
- 🖱️ **Left-click** the album art to toggle play / pause
- 📋 **Right-click** menu with Next Track, Previous Track, Overlay toggle, and Settings
- 🎨 Configurable **position** (top-left, top-right, bottom-left, bottom-right)
- 🎨 Configurable **background color, font color, and opacity**
- ⌨️ Global hotkeys:
  - `Alt+H` — show / hide the overlay
  - `Alt+Right` — next track
  - `Alt+Left` — previous track
- 🔁 Auto-refreshes the now-playing info every 5 seconds
- 🧱 Packageable as a Windows `.exe` with PyInstaller (`spoti.spec`)

## Requirements

- **OS:** Windows (playback control uses system/global media keys)
- **Python:** 3.8+ (developed on 3.11)
- **A Spotify account** (Premium is required for Spotify playback-control scopes)
- **A Spotify Developer app** for API credentials — free at <https://developer.spotify.com/dashboard>

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

1. Create a Spotify app at <https://developer.spotify.com/dashboard> and add `http://localhost:8888/callback` as a **Redirect URI**.
2. Copy the example environment file and fill in your credentials:

```bash
copy .env.example .env         # Windows
```

3. Edit `.env` and set your Spotify app's Client ID and Client Secret:

```
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
```

> ⚠️ **Never commit `.env`.** It is already listed in `.gitignore`. The first launch opens a browser to authorize the app with Spotify.

### Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `SPOTIPY_CLIENT_ID` | ✅ | Spotify app client ID |
| `SPOTIPY_CLIENT_SECRET` | ✅ | Spotify app client secret |
| `SPOTIPY_REDIRECT_URI` | ✅ | Must match the Redirect URI in your Spotify app |
| `SPOTIFY_SCOPE` | Optional | Space-separated OAuth scopes (a sensible default is provided) |

## Usage

Run the app:

```bash
python spoti.py
```

A settings dialog appears first so you can choose the overlay position, colors, and opacity. Confirm it and the overlay appears. Authorize Spotify in the browser window that opens on first run.

The first time you authorize, Spotify saves a `.cache-{username}` file locally (this is your token — keep it private and do not commit it).

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
├── .env.example      # Example environment configuration
├── .gitignore
├── icon.ico          # Application icon
├── bag.png           # UI asset
├── bag2.png          # UI asset
├── example.png       # UI asset
├── ok.png            # UI asset
├── screen.png        # UI asset
├── top_left_image.png# UI asset
└── test.py           # Earlier standalone tkinter prototype
```

## Troubleshooting

**"Application error" / browser doesn't open on first run**
Make sure `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` are set in `.env`, and that the Redirect URI exactly matches the one configured in your Spotify Developer app.

**Play control (play/pause/next) doesn't work**
Playback-modification scopes work best with a Spotify **Premium** account. Also confirm media keys aren't intercepted by another app.

**The overlay stays in the way**
Use the right-click menu → **Overlay** to toggle it, or press `Alt+H` to hide/show it.

**HTTP redirect / localhost permission prompt isn't accepted**
Use a plain `http://localhost:8888/callback` as shown. If the port is busy, update both the Spotify app and `SPOTIPY_REDIRECT_URI`.

## License

No license has been added yet. If you would like to license this project, add a `LICENSE` file and reference it here. Contact the maintainer to choose a license.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.
