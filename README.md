# Spotify Poster Generator

https://spotifyposters.live/

Does what it says on the tin.

Enter a (valid) Spotify album/song URL, receive a poster!

## Examples!

<p float="center">
  <img src="images/Honestly,_Nevermind_dark_poster.png" width="49%" />
  <img src="images/結束バンド_light_poster.png" width="49%" /> 
</p>

---

### Issues/Ideas
- [ ] Tracks vertical length scaling
- [ ] Drop down menu in main webpage to search for album
- [ ] No error propagation from util functions
  
### Fixed Issues 🎉
- [x] Choose poster size
- [x] Special characters not supported
- [x] Better font
- [x] No checking for validity of URL
---
To run this for yourself locally, you'll need a .env file with the following values:
- SPOTIFY_SECRET = `your spotify secret code`
- SPOTIFY_ID = `your spotify client id`
- FLASK_SECRET = `your flask secret code`

The main runfile is poster_generator.py.

If you want to run the Flask webapp.py, you might need a few more env variables, which you can email me about.

---
Big thanks to @sudmike for contributing to the repository and coming up with ideas!
> The website probably wont be up all the time, just email me if you need one.
