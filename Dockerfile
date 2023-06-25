FROM python:3.10-slim
COPY . /app
WORKDIR /app
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 -y
RUN pip install -r requirements.txt
CMD ["gunicorn", "--preload", "--conf", "gunicorn_conf.py", "webapp:app"]