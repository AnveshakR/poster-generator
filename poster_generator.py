"""
     This file is part of poster-gen.

    poster-gen is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

    poster-gen is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with poster-gen. If not, see <https://www.gnu.org/licenses/>. 
"""

import numpy as np
from PIL import Image
import cv2
from skimage import io
from utils import *
from spotify_data import data_pull


def generator(album, resolution):

    data = data_pull(album)

    y_position = 200

    # define poster size
    poster = np.ones(resolution, np.uint8)
    poster = poster*255

    # album art
    album_art = io.imread(data['album_art'])
    album_art = cv2.resize(album_art, (resolution[1]-200, resolution[1]-200), cv2.INTER_AREA)
    album_art = cv2.cvtColor(album_art, cv2.COLOR_RGB2BGR)

    mask = np.zeros((album_art.shape[0], album_art.shape[1]), np.uint8)

    mask = rounded_rectangle(mask, (0,0), (album_art.shape[0], album_art.shape[1]), 0.1, color=(255,255,255), thickness=-1)

    art_inv = cv2.bitwise_not(album_art)

    album_art = cv2.bitwise_not(cv2.bitwise_and(art_inv, art_inv, mask=mask))

    x_offset = y_offset = 100

    poster[y_offset:y_offset+album_art.shape[0], x_offset:x_offset+album_art.shape[1]] = album_art

    y_position += album_art.shape[0] + 200

    # album artist
    font_scale = 0
    for i in range(200, 50, -5):
        i = i/100
        textsize = cv2.getTextSize(data['album_artist'], cv2.FONT_HERSHEY_TRIPLEX, i*10, 15)
      
        if textsize[0][0] <= (resolution[1]-200):
            font_scale = i*10

    cv2.putText(poster, data['album_artist'], (100, y_position), cv2.FONT_HERSHEY_TRIPLEX, font_scale, (0,0,0), 15)

    y_position += 200

    # album name
    font_scale = 0
    for i in range(200, 50, -5):
        i = i/100
        textsize = cv2.getTextSize(data['album_artist'], cv2.FONT_HERSHEY_TRIPLEX, i*10, 5)
        
        if textsize[0][0] <= (resolution[1]-200):
            font_scale = i*10

    cv2.putText(poster, data['album_name'], (100, y_position), cv2.FONT_HERSHEY_PLAIN, font_scale, (0,0,0), 5)

    # playtime
    cv2.putText(poster, data['playtime'], (resolution[1]-200-x_offset, y_position), cv2.FONT_HERSHEY_PLAIN, 3.5, (0,0,0), 5)

    y_position += 100

    # color palette

    palette = dominant_colors(album_art)

    num_colors = 10
    color_palette = np.ones((5, num_colors*100, 3), np.uint8)
    for i in range(num_colors):
        section = 100*(i+1)
        cv2.rectangle(color_palette, (section-100,0), (section, 100), palette[i], -1)

    color_palette = cv2.resize(color_palette, (resolution[1]-200, 50), cv2.INTER_AREA)

    poster[y_position:y_position+color_palette.shape[0], x_offset:x_offset+color_palette.shape[1]] = color_palette

    y_position += 200

    # tracks

    track_line = ""
    for track in data['tracks']:
        if cv2.getTextSize(track_line, cv2.FONT_HERSHEY_PLAIN, 5, 10)[0][0] < resolution[1]-100:
            track_line = track_line + track + " | "
            
        if cv2.getTextSize(track_line, cv2.FONT_HERSHEY_PLAIN, 5, 10)[0][0] >= resolution[1]-100:
            track_line = track_line[:len(track_line) - len(track + " | ")]
            cv2.putText(poster, track_line, (100, y_position), cv2.FONT_HERSHEY_PLAIN, 5, (0,0,0), 5)
            track_line = track + " | "
            y_position += cv2.getTextSize(track_line, cv2.FONT_HERSHEY_PLAIN, 5, 10)[0][1] + 50
    cv2.putText(poster, track_line, (100, y_position), cv2.FONT_HERSHEY_PLAIN, 5, (0,0,0), 5)

    #spotify logo
    scale = 0.04
    creditslogo = cv2.imread("spotifylogo.jpg")
    creditslogo = cv2.resize(creditslogo, (int(resolution[0]*scale), int(resolution[0]*scale)))
    poster[resolution[0]-100-creditslogo.shape[0]:resolution[0]-100, resolution[1]-100-creditslogo.shape[1]:resolution[1]-100] = creditslogo
    
    # record label
    cv2.putText(poster, data['record'], (100, resolution[0]-163), cv2.FONT_HERSHEY_PLAIN, 3.5, (0,0,0), 5)

    # release date
    cv2.putText(poster, data['release_date'], (100, resolution[0]-100), cv2.FONT_HERSHEY_PLAIN, 3.5, (0,0,0), 5)

    poster = cv2.cvtColor(poster, cv2.COLOR_BGR2RGB)

    return(poster, data['album_name'])

if __name__ == '__main__':

    album = input("Enter Spotify Album link: ")
    if album.find('https://open.spotify.com/album/') == -1:
        print("Enter valid Spotify album link.")
        exit(1)

    resolution = input("Enter height, width in pixels: ")
    if resolution == '':
        resolution = (5100, 3300, 3)
    else:
        resolution = list(map(int, resolution.strip().split(',')))
        resolution.append(3)

    poster, album_name = generator(album, resolution)

    poster = cv2.cvtColor(poster, cv2.COLOR_RGB2BGR)

    cv2.imwrite("{}_poster.jpg".format(album_name), poster)

    Image.open("{}_poster.jpg".format(album_name)).show()
 