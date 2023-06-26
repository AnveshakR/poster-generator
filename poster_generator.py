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

# gets path of current script
MAINPATH = os.path.dirname(os.path.realpath(__file__))

# adds font directory to path
FONTDIR = os.path.join(MAINPATH, 'fonts')

# list of fonts that will be used
fonts = {'NotoSansJP-Bold.ttf':"",
         'NotoSansJP-Thin.ttf':"",
         'open-sans.bold.ttf':"",
         'source-code-pro.light.ttf':"",
         'NotoSansTC-Thin.otf': "",
         'NotoSansTC-Bold.otf': ""}

# assigns absolute path to each font
for font in fonts.keys():
    fonts[font] = os.path.join(FONTDIR, font)

# takes the langid language classification and text type and returns appropriate font path
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

    spacing = int(resolution[0] * 0.03)
    y_position = 0

    #
    # define poster
    #
    poster = Image.new('RGBA', resolution, color=(255,255,255,255))

    #
    # album art
    #
    album_art = io.imread(data['album_art'])
    album_art = Image.fromarray(album_art)
    album_art = album_art.resize((resolution[0]-(spacing*2), resolution[0]-(spacing*2)))  # size is poster width - spacing from both sides (square)

    mask = np.zeros(album_art.size, np.uint8)
    mask = rounded_rectangle(mask, (0,0), album_art.size, 0.1, color=(255,255,255), thickness=-1)
    mask = Image.fromarray(mask)

    poster.paste(album_art, (spacing, spacing), mask)

    y_position += resolution[0] + spacing

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

    poster_draw.text((spacing, y_position), data['album_artist'][0],(0,0,0), font=artist_font)

    y_position += artist_font.getbbox(data['album_artist'][0])[3] + spacing

    #
    # album name
    #
    max_text_length = int((resolution[0] - 2 * spacing) * 0.5)  # 50% of width is maximum
    album_font_size = int(max_text_length / 18)  # constant 18 calculated based on width of 3300 and font size 80
    album_font = ImageFont.truetype(get_font_by_lang(data['album_name'][1], "thin"), album_font_size)

    text_length = album_font.getlength(data['album_name'][0])
    if text_length > max_text_length:
        reduce_factor = max_text_length / text_length  # calculate factor to get precise font size if too large
        album_font = ImageFont.truetype(get_font_by_lang(data['album_name'][1], "thin"), int(album_font_size * reduce_factor))

    poster_draw.text((spacing, y_position), data['album_name'][0], (0,0,0), font=album_font)

    #
    # playtime
    #
    playtime_font_size = int(album_font_size//1.5)
    playtime_font = ImageFont.truetype(fonts['source-code-pro.light.ttf'], playtime_font_size)
    playtime_y_position = y_position + int(artist_font.size/2.25) - playtime_font.size  # align playtime with bottom of album name instead of top
    poster_draw.text((resolution[0] - spacing - playtime_font.getbbox(data['playtime'])[2], playtime_y_position), data['playtime'], (0,0,0), font=playtime_font)

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
        if track_font.getlength(track_line) < resolution[0] - spacing:
            track_line = track_line + track + " | "

        if track_font.getlength(track_line) >= resolution[0] - spacing:
            track_line = track_line[:len(track_line) - len(track + " | ")]
            poster_draw.text((spacing, y_position), track_line, (0,0,0), font=track_font)
            track_line = track + " | "
            y_position += track_font.getbbox(track_line)[3]

    poster_draw.text((spacing, y_position), track_line, (0,0,0), font=track_font)

    #
    # spotify scan code
    #
    code_size = max(round(resolution[1] / 5), 256)  # absolute width of requested spotify code
    spotify_code_url = f'https://scannables.scdn.co/uri/plain/jpeg/FFFFFF/black/{code_size}/spotify:album:{data["album_id"]}'
    print(spotify_code_url)
    spotify_code = image_from_url(spotify_code_url)

    if spotify_code is not None:
        code_scale = 0.16  # relative width of displayed spotify code
        spotify_code.resize((int((resolution[0] - 2 * spacing) * code_scale), int((resolution[0] - 2 * spacing) * code_scale / 4)))
        code_width, code_height = spotify_code.size
        code_position = (resolution[0] - int(spacing/2) - code_width, resolution[1] - int(spacing/2) - code_height)
        poster.paste(spotify_code, code_position)

    #
    # record label and release date
    #
    label_font_size = playtime_font_size
    label_font = ImageFont.truetype(get_font_by_lang(data['record'][1], "thin"), label_font_size)
    label_offset = label_font.getbbox(data['release_date'])[3]  # offset to set label text over date text
    poster_draw.text((spacing, resolution[1] - 1.5*spacing - label_offset), data['record'][0], (0,0,0), label_font)

    poster_draw.text((spacing, resolution[1] - 1.5*spacing), data['release_date'], (0,0,0), label_font)

    # return final poster
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
