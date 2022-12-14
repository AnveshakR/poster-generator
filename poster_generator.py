from dotenv import load_dotenv
import os
import requests
from skimage import io
import numpy as np
from PIL import Image
import datetime
import cv2

from utils import *

load_dotenv()
SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
SPOTIFY_ID = os.getenv('SPOTIFY_ID')
album_url_base = r'https://open.spotify.com/album/'
AUTH_URL = r'https://accounts.spotify.com/api/token'
album_get = 'https://api.spotify.com/v1/albums/{id}'

album = input("Enter Spotify Album link: ")
if album.find(album_url_base) == -1:
    print("Enter valid Spotify album link.")
    exit(1)

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

album_name = r['name']

album_artist = r['artists'][0]['name']
# print(len(album_artist))
# album_artist = album_artist.replace('ł','l')

record = r['label']


release_date = r['release_date']
release_date = datetime.datetime.strptime(release_date.replace('-',''), r'%Y%m%d').strftime(r'%B %d, %Y')


playtime = 0
for i in r['tracks']['items']:
    playtime += i['duration_ms']

print(playtime)
playtime = str(datetime.timedelta(seconds=playtime//1000))
# playtime = str(playtime//60000)+":"+str(round((playtime/60000%1)*60))


tracks = []
for i in r['tracks']['items']:
    tracks.append(i['name'])


image = io.imread(r['images'][0]['url'])

palette = dominant_colors(image)


for i in range(len(palette)):
    palette[i] = palette[i][::-1]


n = 10
img = np.ones((10, n*100, 3))
for i in range(n):
    y = 100*(i+1)
    cv2.rectangle(img, (y-100,0), (y, 100), [j/255 for j in palette[i]], -1)

# cv2.imshow("img", img)
# cv2.waitKey(0)


scale = 10

# define poster size
poster = np.ones((540*scale,360*scale,3), np.uint8)
poster = poster*255

# album art
album_art = cv2.resize(image, (340*scale, 340*scale), cv2.INTER_AREA)
album_art = cv2.cvtColor(album_art, cv2.COLOR_RGB2BGR)

mask = np.zeros((340*scale,340*scale), np.uint8)

mask = rounded_rectangle(mask, (0,0), (340*scale,340*scale), 0.1, color=(255,255,255), thickness=-1)

art_inv = cv2.bitwise_not(album_art)

album_art = cv2.bitwise_not(cv2.bitwise_and(art_inv, art_inv, mask=mask))

x_offset = y_offset = 10*scale

poster[y_offset:y_offset+album_art.shape[0], x_offset:x_offset+album_art.shape[1]] = album_art

# album artist
font_scale = 0
for i in range(200, 50, -5):
    i = i/100
    textsize = cv2.getTextSize(album_artist, cv2.FONT_HERSHEY_TRIPLEX, i*scale, 2*scale)

    if textsize[0][0] <= 340*scale:
        font_scale = i

cv2.putText(poster, album_artist, (10*scale,380*scale), cv2.FONT_HERSHEY_TRIPLEX, font_scale*scale, (0,0,0), 2*scale)

# album name
font_scale = 0
for i in range(200, 50, -5):
    i = i/100
    textsize = cv2.getTextSize(album_artist, cv2.FONT_HERSHEY_TRIPLEX, i*scale, 1*scale//2)
    
    if textsize[0][0] <= 340*scale:
        font_scale = i

cv2.putText(poster, album_name, (10*scale, 400*scale), cv2.FONT_HERSHEY_PLAIN, font_scale*scale, (0,0,0), 1*scale//2)

# playtime
cv2.putText(poster, playtime, (340*scale-x_offset, 400*scale), cv2.FONT_HERSHEY_PLAIN, 0.35*scale, (0,0,0), 1*scale//2)

# color palette
n = 10
color_palette = np.ones((5, n*100, 3), np.uint8)
for i in range(n):
    y = 100*(i+1)
    cv2.rectangle(color_palette, (y-100,0), (y, 100), palette[i], -1)

color_palette = cv2.resize(color_palette, (340*scale, 5*scale), cv2.INTER_AREA)

y_offset = 410*scale

poster[y_offset:y_offset+color_palette.shape[0], x_offset:x_offset+color_palette.shape[1]] = color_palette

# tracks
track_position = 440
track_line = ""
for track in tracks:
    if cv2.getTextSize(track_line, cv2.FONT_HERSHEY_PLAIN, 0.5*scale, 1*scale)[0][0] < 340*scale:
        track_line = track_line + track + " | "
        
    if cv2.getTextSize(track_line, cv2.FONT_HERSHEY_PLAIN, 0.5*scale, 1*scale)[0][0] >= 340*scale:
        track_line = track_line[:len(track_line) - len(track + " | ")]
        cv2.putText(poster, track_line, (10*scale, track_position*scale), cv2.FONT_HERSHEY_PLAIN, 0.5*scale, (0,0,0), 1*scale//2)
        track_line = track + " | "
        track_position += int(1.5*scale)
cv2.putText(poster, track_line, (10*scale, track_position*scale), cv2.FONT_HERSHEY_PLAIN, 0.5*scale, (0,0,0), 1*scale//2)

# record label
cv2.putText(poster, record, (10*scale, 527*scale), cv2.FONT_HERSHEY_PLAIN, 0.35*scale, (0,0,0), 1*scale//2)

# release date
cv2.putText(poster, release_date, (10*scale, 535*scale), cv2.FONT_HERSHEY_PLAIN, 0.35*scale, (0,0,0), 1*scale//2)

cv2.imwrite("poster.jpg", poster)

Image.open("poster.jpg").show()