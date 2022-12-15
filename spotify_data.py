from dotenv import load_dotenv
import os
import requests
import datetime

load_dotenv()
SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
SPOTIFY_ID = os.getenv('SPOTIFY_ID')
album_url_base = r'https://open.spotify.com/album/'
AUTH_URL = r'https://accounts.spotify.com/api/token'
album_get = 'https://api.spotify.com/v1/albums/{id}'

def data_pull(album):

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