import os

import cv2
import ffmpeg

# import google.cloud.storage
import requests
from flask import jsonify
from google.oauth2 import service_account

# import shlex
# import subprocess


def classification(request):
    # 結合する動画のパス
    video_path = request.json["video_path"]
    # 結合する音楽のパス
    music_path = request.json["music_path"]
    # 結合した動画のパス
    new_video_path = request.json["new_video_path"]
    # 結合した動画のパス
    upload_url = request.json["upload_url"]

    # 動画の再生時間
    video = cv2.VideoCapture(video_path)
    video_frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
    video_fps = video.get(cv2.CAP_PROP_FPS)
    video_sec = video_frame_count / video_fps
    # 音楽の再生時間
    music_info = ffmpeg.probe(
        music_path,
    )
    # music_sec = float(music_info["streams"][0]["duration"])
    music_sec = float(music_info["format"]["duration"])

    # 音楽の再生時間が動画の再生時間より長いときは動画の再生時間に合わせる
    if video_sec <= music_sec:
        music_sec = video_sec

    # 動画と音楽の結合
    instream1 = ffmpeg.input(video_path)
    instream2 = ffmpeg.input(music_path, t=music_sec)
    stream = ffmpeg.output(
        # instream1, instream2, new_video_path, vcodec="copy", acodec="aac"
        instream1,
        instream2,
        new_video_path,
        # acodec="aac",
    )
    ffmpeg.run(stream, overwrite_output=True)
    # 動画の音が残る
    # Dockerの隔離性のため外部から参照不可？

    # url = "https://iut-b.main.jp/up"
    url = upload_url
    files = {"file": open(new_video_path, "rb")}
    res = requests.post(url, files=files)

    # with open(new_video_path, "rb") as file:
    #     requests.post(url, data=file)

    # os.environ[
    #     "GOOGLE_APPLICATION_CREDENTIALS"
    # ] = "C:/Users/bte/OneDrive/flaskbook-app-20221031-cb2333f040b6.json"

    # key_path = "C:/Users/bte/OneDrive/flaskbook-app-20221031-cb2333f040b6.json"
    # credential = service_account.Credentials.from_service_account_file(key_path)

    # client = google.cloud.storage.Client(credentials=credential)
    # bucket_name = "flaskbook-app-20221031-bucket"
    # bucket = client.get_bucket(bucket_name)

    # ffmpeg_cmd = "ffmpeg -i " + video_path + " -ac 1 -ar 16000 -f wav " + new_video_path
    # ffmpeg_cmd = "ffmpeg -ss 0:10 -to 1:10 -i" + video_path + "-c copy" + new_video_path
    # command1 = shlex.split(ffmpeg_cmd)
    # subprocess.run(command1)

    # new_video_name = os.path.split(new_video_path)[1]

    # blob = bucket.blob(new_video_name)
    # blob.upload_from_filename(new_video_path)
    # blob.make_public()
    # gs_uri = "gs://" + bucket_name + "/" + new_video_name

    # return jsonify({"new_video_path": new_video_path}), 201
    # return jsonify({"gs_uri": gs_uri}), 201
    return jsonify({"new_video_path": res.status_code}), 201
