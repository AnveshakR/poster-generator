"""
     This file is part of poster-gen.

    poster-gen is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

    poster-gen is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with poster-gen. If not, see <https://www.gnu.org/licenses/>.
"""

from PIL import ImageFont, ImageDraw
from skimage import io
from utils import *
import os
import re
from download_fonts import download_fonts
import requests
import re

# gets path of current script
MAINPATH = os.path.dirname(os.path.realpath(__file__))

# adds font directory to path
FONTDIR = os.path.join(MAINPATH, 'fonts')

if not os.path.exists(FONTDIR):
    download_fonts(FONTDIR)

# list of fonts that will be used
fonts = {'NotoSansJP-Bold.ttf':"",
         'NotoSansJP-Thin.ttf':"",
         'open-sans.bold.ttf':"",
         'source-code-pro.light.ttf':"",
         'NotoSansTC-Thin.ttf': "",
         'NotoSansTC-Bold.ttf': ""}

# assigns absolute path to each font
for font in fonts.keys():
    fonts[font] = os.path.join(FONTDIR, font)


# takes the langid language classification and text type and returns appropriate font path
def get_font_by_lang(langid_classify, text_type):

    if text_type == "bold":
        if langid_classify[0] == 'ja':
            return fonts['NotoSansJP-Bold.ttf']
        elif langid_classify[0] == 'zh':
            return fonts['NotoSansTC-Bold.ttf']
        else:
            return fonts['open-sans.bold.ttf']
    elif text_type == "thin":
        if langid_classify[0] == 'ja':
            return fonts['NotoSansJP-Thin.ttf']
        elif langid_classify[0] == 'zh':
            return fonts['NotoSansTC-Thin.ttf']
        else:
            return fonts['source-code-pro.light.ttf']


def generator(album, resolution, options) -> ImageDraw:

    data = spotify_data_pull(album)

    # ensure that album data could be fetched
    if data is None:
        return None, None

    spacing = int(resolution[0] * 0.03)
    y_position = 0

    #
    # define color scheme based on theme variable
    #
    theme = options['theme']
    if theme == "light":
        background_color = (255, 255, 255, 255) # white background
        text_color = (0, 0, 0) # black text
    elif theme == "dark":
        background_color = (10, 10, 10, 255) # dark background
        text_color = (255, 255, 255) # white text

    #
    # define poster
    #
    poster = Image.new('RGBA', resolution, color=background_color)

    #
    # album art
    #
    album_art = io.imread(data['album_art'])
    album_art = Image.fromarray(album_art)
    album_art_size = min(resolution[0] - 2 * spacing, int((resolution[1] - 2 * spacing) * 0.6))  # full width but no larger than 60% of height
    album_art = album_art.resize((album_art_size, album_art_size))

    mask = np.zeros(album_art.size, np.uint8)
    mask = rounded_rectangle(mask, (0,0), album_art.size, 0.1, color=(255,255,255), thickness=-1)
    mask = Image.fromarray(mask)

    poster.paste(album_art, (int(0.5 * resolution[0] - 0.5 * album_art_size), spacing), mask)

    y_position += album_art_size + 2 * spacing

    #
    # make the poster drawable
    #
    poster_draw = ImageDraw.Draw(poster, 'RGBA')

    #
    # album artist
    #
    max_text_length = int((resolution[0] - 2 * spacing) * 0.65)  # 65% of width is maximum
    artist_font_size = int(max_text_length / 9)  # constant 9 calculated based on width of 3300 and font size 170
    artist_font = ImageFont.truetype(get_font_by_lang(data['album_artist'][1], "bold"), artist_font_size)

    text_length = artist_font.getlength(data['album_artist'][0])
    if text_length > max_text_length:
        reduce_factor = max_text_length / text_length  # calculate factor to get precise font size if too large
        artist_font = ImageFont.truetype(get_font_by_lang(data['album_artist'][1], "bold"), int(artist_font_size * reduce_factor))

    poster_draw.text((spacing, y_position), data['album_artist'][0],text_color, font=artist_font)

    y_position += artist_font.getbbox(data['album_artist'][0])[3] + spacing

    #
    # album name
    #
    max_text_length = int((resolution[0] - 2 * spacing) * 0.75)  # 75% of width is maximum
    album_font_size = int(max_text_length / 27)  # constant 27 calculated based on width of 3300 and font size 80
    album_font = ImageFont.truetype(get_font_by_lang(data['album_name'][1], "thin"), album_font_size)

    text_length = album_font.getlength(data['album_name'][0])
    if text_length > max_text_length:
        reduce_factor = max_text_length / text_length  # calculate factor to get precise font size if too large
        album_font = ImageFont.truetype(get_font_by_lang(data['album_name'][1], "thin"), int(album_font_size * reduce_factor))

    poster_draw.text((spacing, y_position), data['album_name'][0], text_color, font=album_font)

    #
    # playtime
    #
    playtime_font_size = int(album_font_size//1.5)
    playtime_font = ImageFont.truetype(fonts['source-code-pro.light.ttf'], playtime_font_size)
    playtime_y_position = y_position + int(artist_font.size/2.25) - playtime_font.size  # align playtime with bottom of album name instead of top
    poster_draw.text((resolution[0] - spacing - playtime_font.getbbox(data['playtime'])[2], playtime_y_position), data['playtime'], text_color, font=playtime_font)

    y_position += 2*spacing

    #
    # color palette
    #
    palette = dominant_colors(np.array(album_art))

    x_posn = spacing
    line_height = resolution[1] * 0.01
    for color in palette:
        poster_draw.rectangle([x_posn, y_position, x_posn+(resolution[0] - 2*spacing)/len(palette), y_position+line_height], fill=tuple(color), width=50)
        x_posn += (resolution[0] - 2*spacing)/len(palette)

    y_position += spacing

    #
    # tracks
    #
    track_font_size = album_font_size
    track_font = ImageFont.truetype(fonts['NotoSansJP-Thin.ttf'], track_font_size)
    track_line = ""
    for track in data['tracks']:
        if options['remove_featured_artists']:
            # remove anything inside parentheses including the parentheses
            track = re.sub(r'\([^)]*\)', '', track)
            track = re.sub(r'\[[^)]*\]', '', track)
            track = track.strip()

        if track_font.getlength(track_line) < resolution[0] - spacing:
            track_line = track_line + track + " | "

        if track_font.getlength(track_line) >= resolution[0] - spacing:
            track_line = track_line[:len(track_line) - len(track + " | ")]
            poster_draw.text((spacing, y_position), track_line, text_color, font=track_font)
            track_line = track + " | "
            y_position += track_font.getbbox(track_line)[3]

    poster_draw.text((spacing, y_position), track_line, text_color, font=track_font)

    #
    # spotify scan code
    #
    code_size = max(round(resolution[1] / 5), 256)  # absolute width of requested spotify code
    if theme == 'light':
        spotify_code_url = f'https://scannables.scdn.co/uri/plain/jpeg/FFFFFF/black/{code_size}/spotify:album:{data["album_id"]}'
    elif theme == 'dark':
        spotify_code_url = f'https://scannables.scdn.co/uri/plain/jpeg/101010/white/{code_size}/spotify:album:{data["album_id"]}'
    spotify_code = image_from_url(spotify_code_url)

    if spotify_code is not None:
        code_scale = 0.16  # relative width of displayed spotify code
        spotify_code.resize((int((resolution[0] - 2 * spacing) * code_scale), int((resolution[0] - 2 * spacing) * code_scale / 4)))
        code_width, code_height = spotify_code.size
        code_position = (resolution[0] - int(spacing/2) - code_width, resolution[1] - int(spacing/2) - code_height)
        if theme == 'dark':
            spotify_code_array = np.array(spotify_code)
            spotify_code_array[spotify_code_array == 16] = 10
            spotify_code = Image.fromarray(spotify_code_array)
        poster.paste(spotify_code, code_position)

    #
    # record label and release date
    #
    label_font_size = playtime_font_size
    label_font = ImageFont.truetype(get_font_by_lang(data['record'][1], "thin"), label_font_size)
    label_offset = label_font.getbbox(data['release_date'])[3]  # offset to set label text over date text
    poster_draw.text((spacing, resolution[1] - 1.5*spacing - label_offset), data['record'][0], text_color, label_font)

    poster_draw.text((spacing, resolution[1] - 1.5*spacing), data['release_date'], text_color, label_font)

    # return final poster and filename friendly album name (no special characters)
    invalid_chars = r"#%&{}\\<>*?\ $!'\":@+`|="
    pattern = "[" + re.escape(invalid_chars) + "]"
    filename_friendly_album_name = re.sub(pattern, "_", data['album_name'][0])
    
    return poster, filename_friendly_album_name


if __name__ == '__main__':

    album = input("Enter Spotify Album link: ")

    if re.match(r'https://spotify.link/([a-zA-Z0-9]+)', album):
        album = requests.get(album).url

    patterns = [
        (r'^https://open\.spotify\.com/album/([a-zA-Z0-9]+)'),
        (r'^spotify:album:([a-zA-Z0-9]+)'),
        ]
    
    if not any(re.match(pattern, album) for pattern in patterns):
        print("Invalid Spotify Album link")
        exit()

    resolution = input("Enter height, width in pixels: ")

    theme = input("Enter theme (light/dark): ")
    
    if resolution == '':
        resolution = (3300, 5100)
    else:
        resolution = tuple(map(int, resolution.strip().split(',')))

    if theme == '':
        theme = 'light'

    poster, album_name = generator(album, resolution, theme)

    poster.save(f"{album_name}_{theme}_poster.png")

    poster.show()
