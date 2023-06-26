"""
     This file is part of poster-gen.

    poster-gen is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

    poster-gen is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with poster-gen. If not, see <https://www.gnu.org/licenses/>.
"""

from flask import Flask, render_template, request, send_file, redirect
from poster_generator import generator
import io
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"]=os.getenv('FLASK_SECRET')


@app.route('/')
def index():
    return render_template('mainpage.html')


@app.route('/result', methods = ['POST', 'GET'])
def result():
    if request.method == 'POST':
        album_link = request.form["album_input"]
        width = 3300 if 'width' not in request.form else int(request.form["width"])
        height = 5100 if 'height' not in request.form else int(request.form["height"])

        # check that input is not empty
        if album_link == "" or album_link is None:
            return render_template('mainpage.html', warning_notification='Input field cannot be empty')

        # generate poster
        poster, album_name = generator(album_link, (width, height))

        # check that album data was fetched
        if poster is None or album_name is None:
            return render_template('mainpage.html', warning_notification=f'Failed to get album data based on input "{album_link}"')

        poster_bytes = io.BytesIO()
        poster.save(poster_bytes, "png")
        poster_bytes.seek(0)

        return send_file(
            poster_bytes,
            mimetype='image/png',
            download_name="{}_poster.jpg".format(album_name),
            as_attachment=True
        )

    else:
        # redirect to home screen if result page is called in browser
        return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
