"""
     This file is part of poster-gen.

    poster-gen is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

    poster-gen is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with poster-gen. If not, see <https://www.gnu.org/licenses/>. 
"""

import cv2
import numpy as np
import scipy.cluster
import sklearn.cluster
from dotenv import load_dotenv
import os
import requests
import datetime

def spotify_data_pull(album):

    load_dotenv()
    SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
    SPOTIFY_ID = os.getenv('SPOTIFY_ID')
    album_url_base = r'https://open.spotify.com/album/'
    AUTH_URL = r'https://accounts.spotify.com/api/token'
    album_get = 'https://api.spotify.com/v1/albums/{id}'

    album = album[:album.find('?')]
    id = album[album.find(album_url_base)+len(album_url_base):]

    auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': SPOTIFY_ID,
    'client_secret': SPOTIFY_SECRET,
    })

    auth_response_data = auth_response.json()
    access_token = auth_response_data['access_token']
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    r = requests.get(album_get.format(id=id), headers=headers)
    r = r.json()

    playtime = 0
    for i in r['tracks']['items']:
        playtime += i['duration_ms']

    playtime = str(datetime.timedelta(seconds=playtime//1000))
    if playtime[0] == '0':
        playtime = playtime[2:]
    
    tracks = []
    for i in r['tracks']['items']:
        tracks.append(i['name'])
    
    album_art = r['images'][0]['url']

    data = {}
    
    data.update({'album_name': r['name']})
    data.update({'album_artist': r['artists'][0]['name']})
    data.update({'record' : r['label']})
    data.update({'release_date' : datetime.datetime.strptime(r['release_date'].replace('-',''), r'%Y%m%d').strftime(r'%B %d, %Y')})
    data.update({'playtime' : playtime})
    data.update({'tracks' : tracks})
    data.update({'album_art': album_art})

    return data

def rounded_rectangle(src, top_left, bottom_right, radius=1, color=255, thickness=1, line_type=cv2.LINE_AA):

    #  corners:
    #  p1 - p2
    #  |     |
    #  p4 - p3

    p1 = top_left
    p2 = (bottom_right[1], top_left[1])
    p3 = (bottom_right[1], bottom_right[0])
    p4 = (top_left[0], bottom_right[0])

    height = abs(bottom_right[0] - top_left[1])

    if radius > 1:
        radius = 1

    corner_radius = int(radius * (height/2))

    if thickness < 0:

        #big rect
        top_left_main_rect = (int(p1[0] + corner_radius), int(p1[1]))
        bottom_right_main_rect = (int(p3[0] - corner_radius), int(p3[1]))

        top_left_rect_left = (p1[0], p1[1] + corner_radius)
        bottom_right_rect_left = (p4[0] + corner_radius, p4[1] - corner_radius)

        top_left_rect_right = (p2[0] - corner_radius, p2[1] + corner_radius)
        bottom_right_rect_right = (p3[0], p3[1] - corner_radius)

        all_rects = [
        [top_left_main_rect, bottom_right_main_rect], 
        [top_left_rect_left, bottom_right_rect_left], 
        [top_left_rect_right, bottom_right_rect_right]]

        [cv2.rectangle(src, rect[0], rect[1], color, thickness) for rect in all_rects]

    # draw straight lines
    cv2.line(src, (p1[0] + corner_radius, p1[1]), (p2[0] - corner_radius, p2[1]), color, abs(thickness), line_type)
    cv2.line(src, (p2[0], p2[1] + corner_radius), (p3[0], p3[1] - corner_radius), color, abs(thickness), line_type)
    cv2.line(src, (p3[0] - corner_radius, p4[1]), (p4[0] + corner_radius, p3[1]), color, abs(thickness), line_type)
    cv2.line(src, (p4[0], p4[1] - corner_radius), (p1[0], p1[1] + corner_radius), color, abs(thickness), line_type)

    # draw arcs
    cv2.ellipse(src, (p1[0] + corner_radius, p1[1] + corner_radius), (corner_radius, corner_radius), 180.0, 0, 90, color ,thickness, line_type)
    cv2.ellipse(src, (p2[0] - corner_radius, p2[1] + corner_radius), (corner_radius, corner_radius), 270.0, 0, 90, color , thickness, line_type)
    cv2.ellipse(src, (p3[0] - corner_radius, p3[1] - corner_radius), (corner_radius, corner_radius), 0.0, 0, 90,   color , thickness, line_type)
    cv2.ellipse(src, (p4[0] + corner_radius, p4[1] - corner_radius), (corner_radius, corner_radius), 90.0, 0, 90,  color , thickness, line_type)

    return src


def font_scale_finder(text, scale, limit, thickness):
    print(text)
    for i in range(200, 50, -5):
        i = i/100
        textsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_TRIPLEX, i*scale, thickness*scale)
        print(textsize[0][0])
        if textsize[0][0] <= limit*scale:
            return i

def dominant_colors(image):

    image = np.resize(image, (3*(image.shape[0])//4, 3*(image.shape[1])//4, image.shape[2]))
    ar = np.asarray(image)
    shape = ar.shape
    ar = ar.reshape(np.product(shape[:2]), shape[2]).astype(float)

    kmeans = sklearn.cluster.MiniBatchKMeans(
        n_clusters=10,
        init="k-means++",
        max_iter=20,
        random_state=1000
    ).fit(ar)
    codes = kmeans.cluster_centers_

    vecs, _dist = scipy.cluster.vq.vq(ar, codes)         # assign codes
    counts, _bins = np.histogram(vecs, len(codes))    # count occurrences

    colors = []
    for index in np.argsort(counts)[::-1]:
        colors.append([int(code) for code in codes[index]])
    return colors                    # returns colors in order of dominance