"""
     This file is part of poster-gen.

    poster-gen is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

    poster-gen is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with poster-gen. If not, see <https://www.gnu.org/licenses/>.
"""

import numpy as np
from PIL import Image, ImageFont, ImageDraw
from skimage import io
from utils import *
import langid
import sys
import shutil
import os

MAINPATH = os.path.dirname(os.path.realpath(__file__))

FONTDIR = os.path.join(MAINPATH, 'fonts')

fonts = {'NotoSansJP-Bold.ttf':"", 
         'NotoSansJP-Thin.ttf':"", 
         'open-sans.bold.ttf':"", 
         'source-code-pro.light.ttf':"", 
         'NotoSansTC-Thin.otf': "",
         'NotoSansTC-Bold.otf': ""}

for font in fonts.keys():
    fonts[font] = os.path.join(FONTDIR, font)
    
def get_font_by_lang(langid_classify, text_type):
    
    if text_type == "bold":
        if langid_classify[0] == 'ja':
            return fonts['NotoSansJP-Bold.ttf']
        elif langid_classify[0] == 'zh':
            return fonts['NotoSansTC-Bold.otf']
        else:
            return fonts['open-sans.bold.ttf']
    elif text_type == "thin":
        if langid_classify[0] == 'ja':
            return fonts['NotoSansJP-Thin.ttf']
        elif langid_classify[0] == 'zh':
            return fonts['NotoSansTC-Thin.otf']
        else:
            return fonts['source-code-pro.light.ttf']


def generator(album, resolution) -> ImageDraw:

    data = spotify_data_pull(album)

    # ensure that album data could be fetched
    if data is None:
        return None, None

    spacing = 100
    y_position = 0

    # define poster
    poster = Image.new('RGBA', resolution, color=(255,255,255,255))

    # album art
    album_art = io.imread(data['album_art'])
    album_art = Image.fromarray(album_art)
    album_art = album_art.resize((resolution[0]-200, resolution[0]-200))

    mask = np.zeros(album_art.size, np.uint8)
    mask = rounded_rectangle(mask, (0,0), album_art.size, 0.1, color=(255,255,255), thickness=-1)
    mask = Image.fromarray(mask)

    poster.paste(album_art, (spacing, spacing), mask)

    y_position += resolution[0] + spacing

    # make the poster drawable
    poster_draw = ImageDraw.Draw(poster, 'RGBA')

    # album artist
    for i in range(200, 1, -5):
        bold_font = ImageFont.truetype(get_font_by_lang(data['album_artist'][1], "bold"), i)
            
        text_size = bold_font.getlength(data['album_artist'][0])
        if text_size < (resolution[0]-200)/2:
            break

    poster_draw.text((100, y_position), data['album_artist'][0],(0,0,0), font=bold_font)

    y_position += bold_font.getbbox(data['album_artist'][0])[3] + spacing

    # album name
    thin_font_size = 0
    for i in range(100, 1, -5):
        thin_font = ImageFont.truetype(get_font_by_lang(data['album_name'][1], "thin"), i)
        text_size = thin_font.getlength(data['album_name'][0])
        if text_size <= (resolution[0]-2*spacing)/2:
            thin_font_size = i
            break

    poster_draw.text((spacing, y_position), data['album_name'][0], (0,0,0), font=thin_font)

    # playtime
    thin_font = ImageFont.truetype(fonts['source-code-pro.light.ttf'], thin_font_size//2)
    poster_draw.text((resolution[0] - spacing - thin_font.getbbox(data['playtime'])[2], y_position), data['playtime'], (0,0,0), font=thin_font)

    y_position += 2*spacing

    # color palette
    palette = dominant_colors(np.array(album_art))

    x_posn = spacing
    for color in palette:
        poster_draw.rectangle([x_posn, y_position, x_posn+(resolution[0] - 2*spacing)/len(palette), y_position+50], fill=tuple(color), width=50)
        x_posn += (resolution[0] - 2*spacing)/len(palette)

    y_position += spacing

    # tracks
    thin_font = ImageFont.truetype(fonts['NotoSansJP-Thin.ttf'], thin_font_size)
    track_line = ""
    for track in data['tracks']:
        if thin_font.getlength(track_line) < resolution[0] - spacing:
            track_line = track_line + track + " | "

        if thin_font.getlength(track_line) >= resolution[0] - spacing:
            track_line = track_line[:len(track_line) - len(track + " | ")]
            poster_draw.text((spacing, y_position), track_line, (0,0,0), font=thin_font)
            track_line = track + " | "
            y_position += thin_font.getbbox(track_line)[3]

    poster_draw.text((spacing, y_position), track_line, (0,0,0), font=thin_font)

    # spotify scan code
    size = round(resolution[1] / 5)  # absolute width of requested spotify code
    spotify_code_url = f'https://scannables.scdn.co/uri/plain/jpeg/FFFFFF/black/{size}/spotify:album:{data["album_id"]}'
    spotify_code = image_from_url(spotify_code_url)

    if spotify_code is not None:
        scale = 0.16  # relative width of displayed spotify code
        space_from_sides = int(resolution[0] * 0.015)  # amount of added padding
        code_dimensions = (int(resolution[0] * scale), int(resolution[0] * scale / 4))
        code_position = (resolution[0] - code_dimensions[0] * 2 - space_from_sides, resolution[1] - code_dimensions[1] * 2 - space_from_sides)
        spotify_code.resize(code_dimensions)
        poster.paste(spotify_code, code_position)

    # record label
    thin_font = ImageFont.truetype(get_font_by_lang(data['record'][1], "thin"), thin_font_size//2)
    poster_draw.text((spacing, resolution[1] - spacing - 63), data['record'][0], (0,0,0), thin_font)

    # release date
    poster_draw.text((spacing, resolution[1] - spacing), data['release_date'], (0,0,0), thin_font)

    return poster, data['album_name'][0]


if __name__ == '__main__':

    album = input("Enter Spotify Album link: ")
    if album.find('https://open.spotify.com/album/') == -1:
        print("Enter valid Spotify album link.")
        exit(1)

    resolution = input("Enter height, width in pixels: ")
    if resolution == '':
        resolution = (3300, 5100)
    else:
        resolution = list(map(int, resolution.strip().split(',')))
        resolution.append(2)

    poster, album_name = generator(album, resolution)

    poster.save(f"{album_name}_poster.png")

    poster.show()
