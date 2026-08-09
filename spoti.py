import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMenu, QAction, QPushButton, QRadioButton, QButtonGroup, QDialog, QHBoxLayout, QColorDialog, QSlider, QLineEdit
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor, QIcon
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import re
import pyautogui
import requests
import keyboard
import tkinter as tk
import os
from dotenv import load_dotenv

load_dotenv()

class ColorButton(QPushButton):
    def __init__(self, color, parent=None):
        super(ColorButton, self).__init__(parent)
        self.color = color
        self.setAutoFillBackground(True)
        self.setFixedWidth(50)
        self.setFixedHeight(25)
        self.update_color()

    def update_color(self):
        palette = self.palette()
        palette.setColor(QPalette.Button, self.color)
        self.setPalette(palette)

class ConfigDialog(QDialog):
    color_changed = pyqtSignal(QColor)
    hotkey_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent)

        self.setWindowTitle("PRO | Spoti")
        self.setGeometry(0, 0, 300, 200)
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())

        layout = QVBoxLayout(self)

        # Position selection
        position_label = QLabel("Select Position:")
        top_left = QRadioButton("Top Left")
        top_right = QRadioButton("Top Right")
        down_left = QRadioButton("Down Left")
        down_right = QRadioButton("Down Right")
        self.position_group = QButtonGroup()
        self.position_group.addButton(top_left)
        self.position_group.addButton(top_right)
        self.position_group.addButton(down_left)
        self.position_group.addButton(down_right)

        layout.addWidget(position_label)
        layout.addWidget(top_left)
        layout.addWidget(top_right)
        layout.addWidget(down_left)
        layout.addWidget(down_right)

        # Color pickers
        background_color_label = QLabel("Background Color:")
        self.background_color_button = ColorButton(QColor(0, 0, 0))
        font_color_label = QLabel("Font Color:")
        self.font_color_button = ColorButton(QColor(255, 255, 255))

        layout.addWidget(background_color_label)
        layout.addWidget(self.background_color_button)
        layout.addWidget(font_color_label)
        layout.addWidget(self.font_color_button)

        # Opacity slider
        opacity_label = QLabel("Opacity:")
        opacity_slider = QSlider(Qt.Horizontal)
        opacity_slider.setMaximum(100)
        opacity_slider.setValue(100)

        layout.addWidget(opacity_label)
        layout.addWidget(opacity_slider)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)

        layout.addWidget(ok_button)
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        # Connect color pickers and slider to functions
        self.background_color_button.clicked.connect(self.pick_background_color)
        self.font_color_button.clicked.connect(self.pick_font_color)
        opacity_slider.valueChanged.connect(self.change_opacity)

        # Initialize color variables
        self.background_color = QColor(0, 0, 0)
        self.font_color = QColor(255, 255, 255)

    def pick_background_color(self):
        color = QColorDialog.getColor(self.background_color, self, "Select Background Color")
        if color.isValid():
            self.background_color = color
            self.background_color_button.color = color
            self.background_color_button.update_color()
            self.color_changed.emit(color)

    def pick_font_color(self):
        color = QColorDialog.getColor(self.font_color, self, "Select Font Color")
        if color.isValid():
            self.font_color = color
            self.font_color_button.color = color
            self.font_color_button.update_color()
            self.color_changed.emit(color)

    def change_opacity(self, value):
        opacity = value / 100.0
        self.parent().setWindowOpacity(opacity)

class SpotifyNowPlayingApp(QWidget):
    def __init__(self):
        super(SpotifyNowPlayingApp, self).__init__()
        self.setWindowTitle("Spoti")
        self.config_dialog = ConfigDialog(self)
        self.config_dialog.color_changed.connect(self.update_colors)

        if self.config_dialog.exec_() == QDialog.Rejected:
            sys.exit()

        self.apply_configurations()

        # Set a custom font for the QLabel
        self.font = QFont()
        self.font.setPointSize(9)

        artist_font = QFont()
        artist_font.setPointSize(7)

        # Add QLabel for displaying the album image
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setPixmap(QPixmap('default_image.png'))  # Replace with your default image

        # Set up a clickable image
        self.image_label.mousePressEvent = self.toggle_play_pause

        self.label = QLabel("Loading..", self)
        self.label.setFont(self.font)
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.artist_label = QLabel("", self)
        self.artist_label.setFont(artist_font)
        self.artist_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label)
        layout.addWidget(self.label)
        layout.addWidget(self.artist_label)

        # Set the window to always stay on top
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.FramelessWindowHint)
        
        self.click_through_enabled = False

        # Set up a timer to update the song information every 5 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_song_info)
        self.hotkey = "Alt+h"
        self.timer.start(5000)
        self.setWindowIcon(QIcon('icon.ico'))
        # Initialize spotipy Spotify client using credentials from the environment (.env)
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
            scope=os.getenv("SPOTIFY_SCOPE", "user-read-currently-playing user-read-playback-state user-modify-playback-state"),
        ))
        keyboard.add_hotkey(self.hotkey, self.toggle_hide_show)
        keyboard.add_hotkey("Alt+Right", self.nexttrack)
        keyboard.add_hotkey("Alt+Left", self.prevtrack)

    def toggle_hide_show(self):
        # Toggle the visibility of the window
        self.setVisible(not self.isVisible())
    def nexttrack(self):
        pyautogui.press("nexttrack")
    def prevtrack(self):
        pyautogui.press("prevtrack")

    def apply_configurations(self):
    # Apply position configuration
      position_button = self.config_dialog.position_group.checkedButton()

      if position_button is not None:
        if position_button.text() == "Top Left":
            self.setGeometry(0, 25, 100, 100)
        elif position_button.text() == "Top Right":
            screen_geometry = QApplication.desktop().screenGeometry()
            self.setGeometry(screen_geometry.width() - 110, 24, 100, 100)
        elif position_button.text() == "Down Left":
            screen_geometry = QApplication.desktop().screenGeometry()
            self.setGeometry(0, screen_geometry.height() - 125, 100, 100)
        elif position_button.text() == "Down Right":
            screen_geometry = QApplication.desktop().screenGeometry()
            self.setGeometry(screen_geometry.width() - 110, screen_geometry.height() - 125, 100, 100)
      else:
        # Handle the case where no radio button is checked
        print("No position selected. Using default position.")

      # Apply background color and font color
      palette = QPalette()
      palette.setColor(QPalette.Window, self.config_dialog.background_color)
      palette.setColor(QPalette.WindowText, self.config_dialog.font_color)
      self.setPalette(palette)
      

    def update_colors(self, color):
        palette = QPalette()
        palette.setColor(QPalette.Window, self.config_dialog.background_color)
        palette.setColor(QPalette.WindowText, self.config_dialog.font_color)
        self.setPalette(palette)
    
    def update_song_info(self):
        try:
            # Get the currently playing song from Spotify API
            current_track = self.sp.current_playback()

            if current_track is not None:
                song_name = current_track['item']['name']
                song_name = re.split(r'[-(:]', song_name)[0].strip()
                artist_name = current_track['item']['artists'][0]['name']

                # Display song information
                song_info = f" {song_name}"
                self.label.setText(song_info)

                # Display album image
                album_image_url = current_track['item']['album']['images'][0]['url']
                image_data = requests.get(album_image_url).content
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                self.image_label.setPixmap(pixmap.scaledToWidth(100))

                # Display artist's name
                self.artist_label.setText(f"-{artist_name}")

                # Adjust the window size
                self.setGeometry(self.geometry().x(), self.geometry().y(), 100, 100)

            else:
                self.label.setText("No song playing")
                self.image_label.setPixmap(QPixmap('default_image.png'))  # Replace with your default image

        except Exception as e:
            print(f"Error: {e}")
            self.label.setText("Error fetching song information")

    def toggle_play_pause(self, event):
        try:
            if event.button() == Qt.LeftButton:
                # Toggle play/pause using pyautogui
                pyautogui.press("playpause")  # Adjust the key based on your system

                # Update the display
                self.update_song_info()
            elif event.button() == Qt.RightButton:
                # Show context menu for next, previous, and settings options
                self.show_context_menu(event)

        except Exception as e:
            print(f"Error toggling play/pause: {e}")

    def show_context_menu(self, event):
        menu = QMenu(self)
        next_action = menu.addAction("Next Track")
        prev_action = menu.addAction("Previous Track")
        click_through_action = menu.addAction("Overlay")
        settings_action = menu.addAction("Settings")

        # Check the menu item if click-through is enabled
        click_through_action.setCheckable(True)
        click_through_action.setChecked(self.click_through_enabled)

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == next_action:
            # Trigger next track action
            pyautogui.press("nexttrack")
        elif action == prev_action:
            # Trigger previous track action
            pyautogui.press("prevtrack")
        elif action == click_through_action:
            # Toggle click-through state
            self.click_through_enabled = not self.click_through_enabled
            self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)  # Toggle 'stay on top'
            self.setWindowFlags(self.windowFlags() ^ Qt.FramelessWindowHint)  # Toggle 'frameless'
            self.show()  # Show the changes
        elif action == settings_action:
            # Open settings dialog
            self.config_dialog.show()

class FramelessApp:
    def __init__(self, master):
        self.master = master
        self.master.title("PRO | Spoti")
        
        # Set window dimensions
        self.width = 1000
        self.height = 563
        
        # Calculate center position
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        
        # Set window geometry
        self.master.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Set window background
        self.bg_image = tk.PhotoImage(file="bag2.png")
        self.canvas = tk.Canvas(self.master, width=self.width, height=self.height)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
        
        # Create image buttons
        self.button_image = tk.PhotoImage(file="example.png").subsample(2)  # Adjust subsample factor as needed
        
        button_positions = [(27, 188), (27, 307), (275, 188), (275, 307)]  # Adjust button positions here
        button_commands = [self.task1, self.task2, self.task3, self.task4]  # Assign tasks to buttons
        
        for button_position, command in zip(button_positions, button_commands):
            button_x, button_y = button_position
            button = tk.Button(self.master, image=self.button_image, bd=0, command=command, compound=tk.LEFT)
            button_window = self.canvas.create_window(button_x, button_y, anchor="nw", window=button)
        
        # Keep window on top
        self.master.attributes("-topmost", True)
        
        # Make window frameless
        self.master.overrideredirect(True)
        
        # Bind events for dragging the window
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<B1-Motion>", self.on_motion)
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
        
    def stop_move(self, event):
        self.x = None
        self.y = None
        
    def on_motion(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.master.winfo_x() + deltax
        y = self.master.winfo_y() + deltay
        self.master.geometry(f"+{x}+{y}")
        
    def task1(self):
        print("Task 1")
        
    def task2(self):
        print("Task 2")
        
    def task3(self):
        print("Task 3")
        
    def task4(self):
        print("Task 4")

if __name__ == "__main__":
    root = tk.Tk()
    #app = FramelessApp(root)
    #root.mainloop()
    app = QApplication(sys.argv)
    window = SpotifyNowPlayingApp()
    window.show()
    sys.exit(app.exec_())
