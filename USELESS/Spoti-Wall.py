import asyncio
import os
import ctypes
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.storage.streams import Buffer, InputStreamOptions
from datetime import datetime
import threading
import tempfile
import json
import sys
import re
import random
from pystray import Icon, Menu, MenuItem

def get_random_quote():
    quotes = [
        "A true measure of a Shinobi is not how he lives but how he dies.",
        "Those who do not understand true pain, can never understand True Peace.",
        "I shut my eyes a long time ago…. The things I seek now lie in the Darkness.",
        "Hard work is worthless for those that don't believe in themselves.",
        "Growth occurs when one goes beyond one's limits.",
        "Don't Try To Shoulder Everything Alone.",
        "One's Reality Might Be Another's Illusion.",
        "You Are Weak Because You Don't Have Enough Hate.",
        "You Will Become A Rival To Measure My Vessel Against.",
        "Sorry, Sasuke... This Is The Last Time.",
        "Any Technique Is Worthless Before My Eyes.",
        "It Is Foolish To Fear What We Have Yet To See And Know.",
        "It Is Not Wise To Judge Others Based On Your Own Perceptions And By Their Appearances.",
        "Even The Strongest Of Opponents Always Have A Weakness.",
        "Those Who Cannot Acknowledge Themselves Will Eventually Fail.",
        "Knowledge And Awareness Are Vague, And Perhaps Better Called Illusions.",
        "However Strong You Become, Never Seek To Bear Everything Alone. If You Do, Failure Is Certain.",
        "Change Is Impossible In This Fog Of Ignorance.",
        "Those Who Turn Their Heads Against Their Comrades Are Sure To Die A Terrible Death. Be Prepared.",
        "He Who Forgives And Acknowledges Himself, That Is What It Truly Means To Be Strong!"
    ]
    return random.choice(quotes)

delay = 5 
def set_delay(icon, item, new_delay):
    global delay
    delay = new_delay
    print(f"Wallpaper check delay set to {delay} seconds.")

async def get_media_info():
    try:
        sessions = await MediaManager.request_async()
        current_session = sessions.get_current_session()

        if not current_session:
            print("No active media session found.")
            return None

        info = await current_session.try_get_media_properties_async()
        title = info.title
        artist = info.artist
        thumbnail = info.thumbnail
        playback_info = current_session.get_playback_info()
        playback_status = playback_info.playback_status  

        image_bytes = None
        if thumbnail:
            stream_ref = await thumbnail.open_read_async()
            content = await stream_ref.read_async(Buffer(stream_ref.size), stream_ref.size, InputStreamOptions.READ_AHEAD)
            image_bytes = bytes(content)

        return {"title": title, "artist": artist, "thumbnail": image_bytes, "status": playback_status}

    except Exception as e:
        print(f"Error extracting media info: {e}")
        return None

def create_wallpaper(song_info, script_dir):
    back_image_path = os.path.join(script_dir, 'back.png')
    back_image = Image.open(back_image_path)

    back_width = 3840 
    back_height = 2160
    back_image = back_image.resize((back_width, back_height))

    if song_info['thumbnail']:
        album_cover_image = Image.open(BytesIO(song_info['thumbnail']))
    else:
        album_cover_image = Image.new('RGB', (500, 500), color=(0, 0, 0)) 

    new_width = 1118
    new_height = 1115
    album_cover_image = album_cover_image.resize((new_width, new_height))

    mask = Image.new('L', (new_width, new_height), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, new_width, new_height), fill=255)
    album_cover_image.putalpha(mask)

    top_image_path = os.path.join(script_dir, 'top.png')
    top_image = Image.open(top_image_path)
    top_image = top_image.resize((back_width, back_height))

    moon_image_path = os.path.join(script_dir, 'moon.png')
    moon_image = Image.open(moon_image_path)
    moon_image = moon_image.resize((back_width, back_height))

    alpha = album_cover_image.convert("RGBA").split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(0.60)
    album_cover_image.putalpha(alpha)

    alpha = moon_image.convert("RGBA").split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(0.6)
    moon_image.putalpha(alpha)

    wallpaper = Image.new('RGB', (back_width, back_height))
    wallpaper.paste(back_image, (0, 0))
    wallpaper.paste(album_cover_image, (int((back_width - album_cover_image.width + 25) / 2), 432), mask=album_cover_image)
    wallpaper.paste(moon_image, (0, 0), mask=moon_image)
    wallpaper.paste(top_image, (0, 0), mask=top_image)

    draw = ImageDraw.Draw(wallpaper)
    if len(song_info['title']) > 30:
        title_font_size = 80
    elif len(song_info['title']) > 60:
        title_font_size = 50
    else:
        title_font_size = 110
    artist_font_size = 50
    quote_font_size = 50
    ct_font_size = 35

    custom_font_path = os.path.join(script_dir, 'font3.ttf')
    title_font = ImageFont.truetype(custom_font_path, title_font_size)
    artist_font = ImageFont.truetype(custom_font_path, artist_font_size)
    quote_font = ImageFont.truetype(custom_font_path, quote_font_size)
    ct_font = ImageFont.truetype(custom_font_path, ct_font_size )

    song_name = song_info['title']
    title_text = re.split(r'[-(:]', song_name)[0].strip()
    title_text_length = draw.textlength(title_text, font=title_font)
    title_position = ((back_width - title_text_length) / 2, 228)
    draw.text(title_position, title_text, (255, 255, 255), font=title_font)

    artist_name = song_info['artist']
    artist_text = f"-{artist_name}"
    artist_text_length = draw.textlength(artist_text, font=artist_font)
    artist_position = ((back_width - artist_text_length) / 2, 350)
    draw.text(artist_position, artist_text, (255, 255, 255), font=artist_font)

    quote = get_random_quote()
    quote_text_length = draw.textlength(quote, font=quote_font)
    quotes_position = ((back_width - quote_text_length) / 2, 1980)
    draw.text(quotes_position, f"-{quote}", (255, 255, 255), font=quote_font)

    c_t = datetime.now().strftime("%I:%M %p")
    ct_text_length = draw.textlength(c_t, font=ct_font)
    ct_position = ((back_width - ct_text_length - 15) // 1, 2000)
    draw.text(ct_position, c_t, (255, 255, 255), font=ct_font)

    return wallpaper

def update_wallpaper_periodically(icon, temp_wallpaper_path, script_dir):
    last_song_id = None
    global delay

    while True:
        try:
            song_info = asyncio.run(get_media_info())

            if song_info and song_info["status"] == 4:
                current_song_id = song_info['title']

                if current_song_id != last_song_id:
                    wallpaper = create_wallpaper(song_info, script_dir)
                    wallpaper.save(temp_wallpaper_path)
                    ctypes.windll.user32.SystemParametersInfoW(20, 0, temp_wallpaper_path, 0)
                    last_song_id = current_song_id
                    print("Wallpaper changed successfully.")

            time.sleep(delay)
        except:
            time.sleep(delay)

def nothing(icon, item):
    pass

def run_updater(icon, temp_wallpaper_path, script_dir):
    threading.Thread(target=update_wallpaper_periodically, args=(icon, temp_wallpaper_path, script_dir)).start()

def on_exit(icon, item):
    icon.stop()
    os._exit(0)

if __name__ == '__main__':
    script_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    temp_wallpaper_path = os.path.join(tempfile.gettempdir(), 'spotify_wallpaper_temp.png')
    temp_wallpaper_path = os.path.join(tempfile.gettempdir(), 'spotify_wallpaper_temp.png')
    icon_path = os.path.join(script_dir, 'icon.ico')

    delay_menu = Menu(
        MenuItem('1s', lambda icon, item: set_delay(icon, item, 1)),
        MenuItem('3s', lambda icon, item: set_delay(icon, item, 3)),
        MenuItem('5s', lambda icon, item: set_delay(icon, item, 5)),
        MenuItem('10s', lambda icon, item: set_delay(icon, item, 10))
    )

    icon = Icon("Spoti Wall", Image.open(icon_path), menu=Menu(
        MenuItem('Spoti Wall (v3)', nothing),
        MenuItem('Set Delay', delay_menu),
        MenuItem('Exit', on_exit)
    ))
    threading.Thread(target=update_wallpaper_periodically, args=(icon, temp_wallpaper_path, script_dir)).start()
    icon.run()
