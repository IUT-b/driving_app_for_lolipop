FROM python:3.10.1

# RUN apt-get update && apt-get install -y sqlite3 && apt-get install -y libsqlite3-dev && apt-get install -y libgl1-mesa-dev
RUN apt-get update && apt-get install -y libgl1-mesa-dev && apt-get -y install ffmpeg libavcodec-extra

WORKDIR /usr/src/

COPY ./api /usr/src/api
COPY ./requirements.txt /usr/src/requirements.txt
COPY ./__init__.py /usr/src/__init__.py
COPY ./run.py /usr/src/run.py


RUN pip install --upgrade pip

RUN pip install -r requirements.txt

RUN echo "building..."

# ENV FLASK_APP "apps.app:create_app('local')"
ENV FLASK_APP "run.py"
ENV FLASK_ENV "development"
# ENV IMAGE_URL "/storage/images/"

EXPOSE 5000

CMD ["flask","run","-h","0.0.0.0"]