"""
Spoti Overlay v2
================
Frameless, always-on-top desktop widget that mirrors whatever media is playing
(primarily Spotify) using the **Windows Media Session API** (winsdk) -- so no
Spotify developer credentials are required.

The settings window uses the image-based, frameless tkinter design from
test.py (bag2.png background + example.png position buttons) and has been
extended with background/font colors, opacity, overlay size, global hotkeys
and click-through support.

Controls
--------
* Left-click the overlay  -> toggle play / pause
* Right-click the overlay -> context menu (next / previous / overlay / settings)
* Global hotkeys (defaults, editable in Settings):
    Alt+H          show / hide the overlay
    Alt+O          toggle click-through (overlay mode)
    Alt+Right      next track
    Alt+Left       previous track
"""

import asyncio
import ctypes
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
from tkinter import colorchooser, font as tkfont
from io import BytesIO

import keyboard
import pyautogui
from PIL import Image, ImageTk
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
)
from winsdk.windows.storage.streams import Buffer, InputStreamOptions

# --------------------------------------------------------------------------- #
#  Helpers / asset loading
# --------------------------------------------------------------------------- #
def resource_path(name):
    """Return an absolute path to a bundled asset (works with PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, name)

# Windows extended window style constants (used for the click-through overlay)
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020


# --------------------------------------------------------------------------- #
#  Windows Media Session API (from Spoti-Wall.py)
# --------------------------------------------------------------------------- #
async def _get_media_info_async():
    """Return now-playing info dict (or None) via the Windows media session."""
    sessions = await MediaManager.request_async()
    current = sessions.get_current_session()
    if not current:
        return None

    try:
        info = await current.try_get_media_properties_async()
    except Exception:
        return None

    title = (info.title or "").strip()
    artist = (info.artist or "").strip()
    if not title and not artist:
        return None

    thumbnail = None
    if info.thumbnail:
        try:
            stream_ref = await info.thumbnail.open_read_async()
            content = await stream_ref.read_async(
                Buffer(stream_ref.size),
                stream_ref.size,
                InputStreamOptions.READ_AHEAD,
            )
            thumbnail = bytes(content)
        except Exception:
            thumbnail = None

    playback = current.get_playback_info()
    return {
        "title": title,
        "artist": artist,
        "thumbnail": thumbnail,
        "status": playback.playback_status,
    }


def get_media_info():
    """Synchronous wrapper around the async media-session lookup."""
    try:
        return asyncio.run(_get_media_info_async())
    except Exception as e:
        print(f"[Spoti] media lookup error: {e}")
        return None

# --------------------------------------------------------------------------- #
#  Overlay : the always-on-top now-playing widget
# --------------------------------------------------------------------------- #
class Overlay:
    def __init__(self, root, config, on_settings):
        self.root = root
        self.config = config
        self.on_settings = on_settings
        self.win = None
        self.photo = None
        self.running = True
        self.click_through = False
        self.borderless = True
        self._queue = queue.Queue()
        self._build()
        self._apply_position()
        self._register_hotkeys()
        threading.Thread(target=self._poll_loop, daemon=True).start()
        self.root.after(100, self._tick)

    # -- UI construction ------------------------------------------------ #
    def _build(self):
        size = self.config["size"]
        text_area = int(size * 0.55)
        w, h = size, size + text_area
        self._w, self._h = w, h

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", self.config["opacity"])
        win.configure(bg=self.config["bg_color"])
        self.win = win

        canvas = tk.Canvas(
            win,
            width=w,
            height=h,
            bg=self.config["bg_color"],
            highlightthickness=0,
        )
        canvas.pack()
        self.canvas = canvas

        self.album_id = canvas.create_image(0, 0, anchor="nw", image=None)
        self.title_font = tkfont.Font(size=max(13, int(size * 0.08)))
        self.artist_font = tkfont.Font(size=max(5, int(size * 0.05)))
        self.title_id = canvas.create_text(
            6, size + 2, anchor="nw", text="Loading..",
            fill=self.config["font_color"],
            font=self.title_font,
        )
        self.artist_id = canvas.create_text(
            6, size + int(size * 0.18), anchor="nw", text="",
            fill=self.config["font_color"],
            font=self.artist_font,
        )

        # whole overlay is interactive
        canvas.bind("<Button-1>", self.toggle_play_pause)
        canvas.bind("<Button-3>", self.show_menu)

    def _apply_position(self):
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        w, h = self._w, self._h
        pos = self.config["position"]
        if pos == "Top Right":
            x, y = sw - w + 35, 2
        elif pos == "Bottom Left":
            x, y = 2, sh - h - 97
        elif pos == "Bottom Right":
            x, y = sw - w + 35, sh - h - 150
        else:  # Top Left (default)
            x, y = 2, 2
        self.win.geometry(f"+{x}+{y}")

    # -- media polling (background thread + main-thread tick) ------------ #
    def _poll_loop(self):
        while self.running:
            info = get_media_info()
            if info is not None:
                self._queue.put(info)
            time.sleep(self.config["refresh_ms"] / 1000.0)

    def _tick(self):
        if not self.running:
            return
        try:
            while True:
                info = self._queue.get_nowait()
                if info is not None:
                    self._display(info)
        except queue.Empty:
            pass
        self.root.after(150, self._tick)

    def _display(self, info):
        title = info.get("title") or ""
        artist = info.get("artist") or ""

        if not title:
            self.canvas.itemconfigure(self.title_id, text="No song playing")
            self.canvas.itemconfigure(self.artist_id, text="")
            self.canvas.itemconfigure(self.album_id, image="")
            self.photo = None
            return

        title = re.split(r"[-(:]", title)[0].strip()
        title = self._fit_text(
            title, self.title_font, self.config["size"] - 12,
            self.config.get("max_words", 5), 60,
        )
        artist = self._fit_text(
            artist, self.artist_font, self.config["size"] - 12,
            self.config.get("max_artist_words", 10), 90,
        )
        self.canvas.itemconfigure(self.title_id, text=title)
        self.canvas.itemconfigure(
            self.artist_id, text=("- " + artist) if artist else ""
        )

        thumb = info.get("thumbnail")
        if thumb:
            try:
                img = Image.open(BytesIO(thumb)).convert("RGB")
                img = img.resize((self.config["size"], self.config["size"]))
                self.photo = ImageTk.PhotoImage(img)
                self.canvas.itemconfigure(self.album_id, image=self.photo)
                return
            except Exception as e:
                print(f"[Spoti] thumbnail error: {e}")
        self.canvas.itemconfigure(self.album_id, image="")
        self.photo = None

    def _fit_text(self, text, font, max_width, max_words, max_chars):
        """Truncate a string to a word limit that also fits in max_width px."""
        ellipsis = "..."
        text = (text or "").strip()
        if not text:
            return ""
        words = text.split()
        truncated = len(words) > max_words
        if truncated:
            text = " ".join(words[:max_words])
        # shrink character-by-character until it fits (with ellipsis shown)
        while font.measure(text + (ellipsis if truncated else "")) > max_width:
            if not text:
                break
            text = text[:-1].rstrip()
            truncated = True
        out = text + (ellipsis if truncated else "")
        # hard safety cap
        if len(out) > max_chars:
            out = out[:max_chars].rstrip() + ellipsis
        return out
    def toggle_play_pause(self, event=None):
        pyautogui.press("playpause")
        self._refresh()

    def next_track(self):
        pyautogui.press("nexttrack")
        self._refresh()

    def prev_track(self):
        pyautogui.press("prevtrack")
        self._refresh()

    def _refresh(self):
        threading.Thread(
            target=lambda: self._queue.put(get_media_info()), daemon=True
        ).start()

    def toggle_visible(self):
        if self.win.state() == "withdrawn":
            self.win.deiconify()
        else:
            self.win.withdraw()

    def toggle_click_through(self):
        self.click_through = not self.click_through
        self._set_layered(self.click_through)

    def toggle_borderless(self):
        """Turn the window's OS frame/border on or off (default: frameless)."""
        self.borderless = not self.borderless
        self.win.overrideredirect(self.borderless)
        self.win.update_idletasks()
        # re-map so the border change takes effect on Windows
        self.win.withdraw()
        self.win.deiconify()
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", self.config["opacity"])

    def _set_layered(self, enable):
        hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if enable:
            style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
        else:
            style &= ~(WS_EX_LAYERED | WS_EX_TRANSPARENT)
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    # -- context menu ---------------------------------------------------- #
    def show_menu(self, event):
        menu = tk.Menu(self.win, tearoff=0)
        menu.add_command(label="Next Track", command=self.next_track)
        menu.add_command(label="Previous Track", command=self.prev_track)
        menu.add_command(label="Play / Pause", command=self.toggle_play_pause)
        menu.add_separator()
        menu.add_command(label="Overlay Mode", command=self.toggle_borderless)
        menu.add_separator()
        menu.add_command(label="Settings", command=self.on_settings)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # -- hotkeys --------------------------------------------------------- #
    def _bind(self, hotkey, cb):
        """Register a hotkey, ignoring any that the keyboard lib can't parse."""
        if hotkey:
            try:
                keyboard.add_hotkey(hotkey, cb)
            except Exception as e:
                print(f"[Spoti] ignored bad hotkey {hotkey!r}: {e}")

    def _register_hotkeys(self):
        self._bind(self.config.get("hotkey_show", "alt+h"), self.toggle_visible)
        self._bind(self.config.get("hotkey_overlay"), self.toggle_click_through)
        self._bind(self.config.get("hotkey_next", "alt+right"), self.next_track)
        self._bind(self.config.get("hotkey_prev", "alt+left"), self.prev_track)

    def _remove_hotkeys(self):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

    def close(self):
        self.running = False
        self._remove_hotkeys()
        try:
            self.win.destroy()
        except Exception:
            pass
# --------------------------------------------------------------------------- #
#  SettingsWindow : frameless, image-based configuration UI (test.py style)
# --------------------------------------------------------------------------- #
class SettingsWindow:
    WIDTH, HEIGHT = 1200, 700

    def __init__(self, root, config, on_confirm):
        self.root = root
        self.config = dict(config)
        self.on_confirm = on_confirm

        self.win = tk.Toplevel(root)
        self.win.title("PRO | Spoti")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x = (sw - self.WIDTH) // 2
        y = (sh - self.HEIGHT) // 2
        self.win.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self.bg = ImageTk.PhotoImage(
            Image.open(resource_path("./assets/bag.png")).resize(
                (self.WIDTH, self.HEIGHT)))
        self.canvas = tk.Canvas(
            self.win, width=self.WIDTH, height=self.HEIGHT, highlightthickness=0)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg)

        # top-center title
        self.canvas.create_text(
            self.WIDTH // 2 + 1, 40, text="S P O T I", anchor="n",
            fill="#89EC7C", font=tkfont.Font(size=26, weight="bold"))
        self.canvas.create_text(
            self.WIDTH // 2, 37, text="S P O T I", anchor="n",
            fill="#1ed760", font=tkfont.Font(size=26, weight="bold"))

        # draggable window (test.py behaviour) -- only on the empty canvas
        self._drag_offset = None
        self.canvas.bind("<ButtonPress-1>", self._start_move)
        self.canvas.bind("<ButtonRelease-1>", self._stop_move)
        self.canvas.bind("<B1-Motion>", self._on_motion)

        # chosen position is shared with the position page
        self.position_var = tk.StringVar(value=self.config["position"])
        self.pos_page = None
        self.settings_items = []
        self._build_options_panel()
        self._build_close_button()

    # -- window dragging ------------------------------------------------- #
    def _start_move(self, event):
        self._drag_offset = (event.x_root - self.win.winfo_x(),
                             event.y_root - self.win.winfo_y())

    def _stop_move(self, event):
        self._drag_offset = None

    def _on_motion(self, event):
        if self._drag_offset is None:
            return
        ox, oy = self._drag_offset
        self.win.geometry(f"+{event.x_root - ox}+{event.y_root - oy}")

    # -- settings / position page switching --------------------------------- #
    def _set_settings_visible(self, visible):
        state = "normal" if visible else "hidden"
        for iid in self.settings_items:
            self.canvas.itemconfigure(iid, state=state)

    def _show_settings_page(self):
        if self.pos_page is not None:
            self.pos_page.place_forget()
        self._set_settings_visible(True)
        self.canvas.itemconfigure(self.close_win_id, state="normal")

    def _show_position_page(self):
        self._set_settings_visible(False)
        self.canvas.itemconfigure(self.close_win_id, state="hidden")
        if self.pos_page is None:
            self._build_position_page()
        self.pos_page.place(x=0, y=0, relwidth=1, relheight=1)

    def _build_position_page(self):
        page = tk.Frame(self.win, bg="#000000")
        monitor = Image.open(resource_path("./assets/monitor.png")).resize(
            (self.WIDTH, self.HEIGHT))
        self._mon = ImageTk.PhotoImage(monitor)
        cv = tk.Canvas(page, width=self.WIDTH, height=self.HEIGHT,
                       highlightthickness=0)
        cv.pack(fill="both", expand=True)
        cv.create_image(0, 0, anchor="nw", image=self._mon)

        # top-center title
        cv.create_text(
            self.WIDTH // 2 + 1, 41, text="CHOOSE POSITION", anchor="n",
            fill="#000000", font=tkfont.Font(size=24, weight="bold"))
        cv.create_text(
            self.WIDTH // 2, 40, text="CHOOSE POSITION", anchor="n",
            fill="#ffffff", font=tkfont.Font(size=24, weight="bold"))

        btn_w, btn_h = 46, 65
        self._pb_img = ImageTk.PhotoImage(
            Image.open(resource_path("./assets/example.png")).resize((btn_w, btn_h)))
        m = 14
        corners = [
            ("Top Left", m, m),
            ("Top Right", self.WIDTH - btn_w - m, m),
            ("Bottom Left", m, self.HEIGHT - btn_h - m - 18),
            ("Bottom Right", self.WIDTH - btn_w - m, self.HEIGHT - btn_h - m - 18),
        ]
        selected = self.position_var.get()
        for name, x, y in corners:
            b = tk.Button(
                page, image=self._pb_img, bd=0, relief="flat",
                activebackground="#222222",
                command=lambda n=name: self._pick_position(n),
            )
            cv.create_window(x, y, anchor="nw", window=b)
            if name == selected:
                cv.create_rectangle(
                    x - 5, y - 5, x + btn_w + 5, y + btn_h + 5,
                    outline="#d71e1e", width=3)

        back = tk.Button(
            page, text="Back", bd=0, relief="flat", width=14,
            bg="#2a2a2a", fg="#ffffff", activebackground="#3a3a3a",
            activeforeground="#ffffff", pady=6,
            font=tkfont.Font(size=12, weight="bold"),
            command=self._show_settings_page)
        cv.create_window(
            self.WIDTH // 2 - 2, self.HEIGHT - 24, anchor="s", window=back)

        self.pos_page = page

    def _pick_position(self, name):
        self.position_var.set(name)
        self._refresh_position_label()
        self._show_settings_page()
    # -- options panel (controls placed straight on the background) ---------- #
    # -- options panel: low-opacity rounded category cards ---------------- #
    def _build_options_panel(self):
        C = "#1a1a1a"

        def place(w, x, y, anchor="w"):
            self.settings_items.append(
                self.canvas.create_window(x, y, anchor=anchor, window=w))

        def card(x1, y1, x2, y2, r=20, fill="#15171a", stipple="gray25",
                 outline="#41474f"):
            # smooth rounded-rectangle polygon (stipple => low-opacity card)
            pts = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
                   x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
                   x1, y2, x1, y2-r, x1, y1+r, x1, y1]
            self.settings_items.append(
                self.canvas.create_polygon(
                    pts, smooth=True, fill=fill, stipple=stipple,
                    outline=outline, width=2))

        def lbl(text, x, y, fg="#e6e6e6", size=12, bold=False):
            place(tk.Label(self.win, text=text, fg=fg, bg=C,
                           font=tkfont.Font(size=size,
                                            weight="bold" if bold else "normal")),
                  x, y)

        def hdr(text, x, y):
            lbl(text, x, y, fg="#ffffff", size=13, bold=True)

        def btn(text, cmd, x, y, w=14):
            place(tk.Button(self.win, text=text, command=cmd, width=w,
                            bd=0, relief="flat", bg="#2a2a2a", fg="#ffffff",
                            activebackground="#3a3a3a", activeforeground="#ffffff",
                            pady=5), x, y)

        def scale(var, lo, hi):
            return tk.Scale(self.win, from_=lo, to=hi, orient="horizontal",
                            variable=var, showvalue=True, length=150, bg=C,
                            fg="#ffffff", troughcolor="#2a2a2a",
                            activebackground="#1ed760", highlightthickness=0,
                            bd=0)

        def swtch(color):
            return tk.Canvas(self.win, width=26, height=20, bg=color,
                             highlightthickness=1, highlightbackground="#555555")

        # ---------- POSITION card ---------- #
        card(100, 150, 570, 262)
        hdr("POSITION", 145, 188)
        self.position_label = tk.Label(self.win, text="", fg="#cfcfcf",
                                       bg=C, font=tkfont.Font(size=12))
        place(self.position_label, 145, 220)
        btn("Choose on monitor", self._show_position_page, 320, 219, w=17)

        # ---------- APPEARANCE card ---------- #
        card(100, 298, 570, 595)
        hdr("APPEARANCE", 145, 334)
        y = 378
        self.bg_swatch = swtch(self.config["bg_color"])
        lbl("Background", 145, y)
        place(self.bg_swatch, 145 + 125, y)
        btn("Pick", lambda: self._pick_color("bg_color", self.bg_swatch),
            145 + 175, y, w=7)
        y += 46
        self.fg_swatch = swtch(self.config["font_color"])
        lbl("Font", 145, y)
        place(self.fg_swatch, 145 + 125, y)
        btn("Pick", lambda: self._pick_color("font_color", self.fg_swatch),
            145 + 175, y, w=7)
        y += 46
        self.opacity_var = tk.IntVar(value=int(self.config["opacity"] * 100))
        lbl("Opacity", 145, y)
        place(scale(self.opacity_var, 20, 100), 145 + 125, y)
        y += 46
        self.size_var = tk.IntVar(value=self.config["size"])
        lbl("Size", 145, y)
        place(scale(self.size_var, 120, 260), 145 + 125, y)
        y += 46
        self.words_var = tk.IntVar(value=self.config.get("max_words", 5))
        lbl("Title words", 145, y)
        place(scale(self.words_var, 2, 8), 145 + 125, y)

        # ---------- HOTKEYS card ---------- #
        card(720, 150, 1140, 470)
        hdr("HOTKEYS", 765, 188)
        self.hot_show = tk.StringVar(value=self.config["hotkey_show"])
        self.hot_overlay = tk.StringVar(value=self.config["hotkey_overlay"])
        self.hot_next = tk.StringVar(value=self.config["hotkey_next"])
        self.hot_prev = tk.StringVar(value=self.config["hotkey_prev"])
        hy = 245
        for lab, var in (("Show / Hide", self.hot_show),
                         ("Click-through", self.hot_overlay),
                         ("Next track", self.hot_next),
                         ("Prev track", self.hot_prev)):
            lbl(lab, 765, hy)
            place(tk.Entry(self.win, textvariable=var, width=16, bg="#2a2a2a",
                           fg="#ffffff", insertbackground="#ffffff",
                           relief="flat", font=tkfont.Font(size=12)),
                  765 + 150, hy)
            hy += 55

        self._refresh_position_label()

        # ---------- OK (centered bottom) ---------- #
        card(self.WIDTH // 2 - 110, 610, self.WIDTH // 2 + 110, 665, r=14)
        place(tk.Button(self.win, text="OK", bd=0, relief="flat", width=16,
                        fg="#08130c", bg="#1ed760", activeforeground="#ffffff",
                        activebackground="#17b54f",
                        font=tkfont.Font(size=16, weight="bold"), pady=7,
                        command=self._confirm),
              self.WIDTH // 2, 632, anchor="center")

    def _refresh_position_label(self):
        try:
            self.position_label.config(
                text=f"Position: {self.position_var.get()}")
        except Exception:
            pass

    def _pick_color(self, key, swatch):
        chosen = colorchooser.askcolor(
            color=self.config[key], title=f"Select {key}", parent=self.win)[1]
        if chosen:
            self.config[key] = chosen
            swatch.config(bg=chosen)

    def _confirm(self):
        self.config.update({
            "position": self.position_var.get(),
            "opacity": self.opacity_var.get() / 100.0,
            "size": self.size_var.get(),
            "max_words": max(2, self.words_var.get()),
            "hotkey_show": self.hot_show.get().strip() or "alt+h",
            "hotkey_overlay": self.hot_overlay.get().strip() or "alt+o",
            "hotkey_next": self.hot_next.get().strip() or "alt+right",
            "hotkey_prev": self.hot_prev.get().strip() or "alt+left",
        })
        self.win.destroy()
        self.on_confirm(self.config)
# -- small top-right close button ------------------------------------ #
    def _build_close_button(self):
        close_btn = tk.Button(
            self.win, text="x", fg="#ffffff", bg="#161616", bd=0,
            font=tkfont.Font(size=13, weight="bold"),
            activebackground="#ff3b30", activeforeground="#ffffff",
            command=self._cancel,
        )
        self.close_win_id = self.canvas.create_window(
            self.WIDTH - 30, 10, anchor="ne", window=close_btn)

    def _cancel(self):
        self.win.destroy()


# --------------------------------------------------------------------------- #
#  Controller : ties the settings window and the overlay together
# --------------------------------------------------------------------------- #
class SpotiApp:
    DEFAULT_CONFIG = {
        "position": "Top Left",
        "bg_color": "#000000",
        "font_color": "#ffffff",
        "opacity": 1.0,
        "size": 160,
        "max_words": 5,
        "hotkey_show": "alt+h",
        "hotkey_overlay": "",
        "hotkey_next": "alt+right",
        "hotkey_prev": "alt+left",
        "refresh_ms": 3000,
    }

    def __init__(self, root):
        self.root = root
        self.config = dict(self.DEFAULT_CONFIG)
        self.overlay = None
        self.show_settings()

    def show_settings(self):
        if self.overlay is not None:
            self.overlay.close()
            self.overlay = None
        SettingsWindow(self.root, self.config, self.on_confirm)

    def on_confirm(self, config):
        self.config = config
        # overlay always re-anchors to its chosen corner (recomputed for size)
        self.overlay = Overlay(self.root, self.config, self.show_settings)


def main():
    root = tk.Tk()
    root.withdraw()
    app = SpotiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()