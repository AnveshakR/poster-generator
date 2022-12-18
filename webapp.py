from flask import Flask, render_template, request 
from poster_generator import generator
from PIL import Image
import io
from base64 import b64encode
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"]=os.getenv('FLASK_SECRET')

@app.route('/')
def index():
        return render_template('mainpage.html', PageTitle="Spotify Poster Generator")

@app.route('/', methods = ['POST', 'GET'])
def display_poster():
    return render_template("mainpage.html")


@app.route('/', methods = ['POST', 'GET'])
def result():
    if request.method == 'POST':
        album_link = request.form["album_input"]

        poster = generator(album_link, (5100, 3300, 3))
        poster = Image.fromarray(poster)
        poster_bytes = io.BytesIO()
        poster.save(poster_bytes, "png")
        poster_bytes.seek(0)
        poster_byte64 = b64encode(poster_bytes.getvalue()).decode('ascii')

        return render_template("mainpage.html", poster_base64 = poster_byte64)


if __name__ == '__main__':
    app.run(debug=True)