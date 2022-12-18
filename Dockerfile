FROM python:3.8-slim-buster
COPY . /app
WORKDIR /app
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 -y
RUN pip install -r requirements.txt
CMD ["gunicorn", "--workers 5", "--threads 2", "webapp:app"]