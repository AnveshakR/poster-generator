FROM debian:bullseye-slim
ENV PYTHON_VERSION 3.10.6
COPY . /app
WORKDIR /app
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 -y
RUN pip install -r requirements.txt
CMD ["gunicorn", "--conf", "gunicorn_conf.py", "webapp:app"]