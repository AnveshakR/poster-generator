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
from io import BytesIO
from PIL import Image
import langid

load_dotenv()

def get_access_token():
    SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
    SPOTIFY_ID = os.getenv('SPOTIFY_ID')
    AUTH_URL = r'https://accounts.spotify.com/api/token'

    auth_response = requests.post(AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_ID,
        'client_secret': SPOTIFY_SECRET,
    }).json()
    
    access_token = auth_response['access_token']
    
    return access_token


def spotify_data_pull(id, link_type='albums'):

    access_token = get_access_token()
    
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    if link_type == 'tracks':
        print(id)
        print("\n----------------\n")
        tracks_get = f'https://api.spotify.com/v1/tracks/{id}'
        r = requests.get(tracks_get, headers=headers)
        r = r.json()
        id = r['album']['id']

    album_get = f'https://api.spotify.com/v1/albums/{id}'

    r = requests.get(album_get, headers=headers)
    r = r.json()

    # ensure that response from Spotify contains necessary data
    if 'tracks' not in r:
        return None

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
    
    date_str = r['release_date'].replace('-', '')

    # handle release date precision
    if r['release_date_precision'] == 'day':
        format_str = r'%Y%m%d'
    elif r['release_date_precision'] == 'month':
        format_str = r'%Y%m'
    elif r['release_date_precision'] == 'year':
        format_str = r'%Y'

    release_date = datetime.datetime.strptime(date_str, format_str).strftime(r'%B %d, %Y')


    data = {}

    data.update({'album_id': id})
    data.update({'album_name': [r['name'], langid.classify(r['name'])]})
    data.update({'album_artist': [r['artists'][0]['name'], langid.classify(r['artists'][0]['name'])]})
    data.update({'record' : [r['label'], langid.classify(r['label'])]})
    data.update({'release_date' : release_date})
    data.update({'playtime' : playtime})
    data.update({'tracks' : tracks})
    data.update({'album_art': album_art})

    return data


def rounded_rectangle(src, top_left, bottom_right, radius=1, color=255, thickness=1, line_type=cv2.LINE_AA):

    #  crners:
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

def dominant_colors(image):

    image = np.resize(image, (3*(image.shape[0])//4, 3*(image.shape[1])//4, image.shape[2]))
    ar = np.asarray(image)
    shape = ar.shape
    ar = ar.reshape(np.prod(shape[:2]), shape[2]).astype(float)

    kmeans = sklearn.cluster.MiniBatchKMeans(
        n_clusters=10,
        init="k-means++",
        max_iter=20,
        n_init=3
    ).fit(ar)
    codes = kmeans.cluster_centers_

    vecs, _dist = scipy.cluster.vq.vq(ar, codes)         # assign codes
    counts, _bins = np.histogram(vecs, len(codes))    # count occurrences

    colors = []
    for index in np.argsort(counts)[::-1]:
        colors.append([int(code) for code in codes[index]])
    return colors                    # returns colors in order of dominance


def image_from_url(url: str):
    r = requests.get(url, stream=True)
    if r.ok is True:
        # Load the image using BytesIO and open it with PIL
        image_data = BytesIO(r.content)
        return Image.open(image_data)
    else:
        return None
