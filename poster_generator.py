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

if sys.platform.startswith('win') or sys.platform.startswith('cygwin'):
    FONTDIRS = os.path.join(os.environ['WINDIR'], 'Fonts')
elif sys.platform.startswith('darwin'):
    FONTDIR = os.path.join(os.path.expanduser("~"), ".fonts")
else: # linux, *bsd and everything else
    FONTDIR = os.path.join(os.path.expanduser("~"), ".fonts")
    
print(FONTDIR)
if not os.path.exists(FONTDIR):
    os.mkdir(FONTDIR)

fonts = {'open-sans.bold.ttf':"", 'source-code-pro.light.ttf':""}

for font in fonts.keys():
    shutil.copy2(os.path.join(MAINPATH, "fonts", font), os.path.join(FONTDIR, font))
    fonts[font] = os.path.join(FONTDIR, font)
    

def generator(album, resolution) -> ImageDraw:

    with open(fonts['open-sans.bold.ttf'], 'rb') as f:
        open_sans = ImageFont.truetype(f)
        f.close()

    with open(fonts['source-code-pro.light.ttf'], 'rb') as f:
        source_code = ImageFont.truetype(f)
        f.close()

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
        open_sans = ImageFont.truetype(fonts['open-sans.bold.ttf'], i)
        text_size = open_sans.getlength(data['album_artist'])
        if text_size < (resolution[0]-200)/2:
            break

    poster_draw.text((100, y_position), data['album_artist'],(0,0,0), font=open_sans, language=langid.classify(data['album_artist'])[0])

    y_position += open_sans.getbbox(data['album_artist'])[3] + spacing

    # album name
    source_code_fontsize = 0
    for i in range(100, 1, -5):
        source_code = ImageFont.truetype(fonts['source-code-pro.light.ttf'], i)
        text_size = source_code.getlength(data['album_name'])
        if text_size <= (resolution[0]-2*spacing)/2:
            source_code_fontsize = i
            break

    poster_draw.text((spacing, y_position), data['album_name'], (0,0,0), font=source_code)

    # playtime
    source_code = ImageFont.truetype(fonts['source-code-pro.light.ttf'], source_code_fontsize//2)
    poster_draw.text((resolution[0] - spacing - source_code.getbbox(data['playtime'])[2], y_position), data['playtime'], (0,0,0), font=source_code)

    y_position += 2*spacing

    # color palette

    palette = dominant_colors(np.array(album_art))

    x_posn = spacing
    for color in palette:
        poster_draw.rectangle([x_posn, y_position, x_posn+(resolution[0] - 2*spacing)/10, y_position+50], fill=tuple(color), width=50)
        x_posn += (resolution[0] - 2*spacing)/10

    y_position += spacing

    # tracks

    source_code = ImageFont.truetype(fonts['source-code-pro.light.ttf'], source_code_fontsize)
    track_line = ""
    for track in data['tracks']:
        if source_code.getlength(track_line) < resolution[0] - spacing:
            track_line = track_line + track + " | "
            
        if source_code.getlength(track_line) >= resolution[0] - spacing:
            track_line = track_line[:len(track_line) - len(track + " | ")]
            poster_draw.text((spacing, y_position), track_line, (0,0,0), font=source_code)
            track_line = track + " | "
            y_position += source_code.getbbox(track_line)[3]

    poster_draw.text((spacing, y_position), track_line, (0,0,0), font=source_code)

    # NOTE: Replace with spotify scan code

    # record label
    source_code = ImageFont.truetype(fonts['source-code-pro.light.ttf'], source_code_fontsize//2)
    poster_draw.text((spacing, resolution[1] - 163), data['record'], (0,0,0), source_code)

    # release date
    poster_draw.text((spacing, resolution[1] - spacing), data['release_date'], (0,0,0), source_code)

    return(poster, data['album_name'])

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