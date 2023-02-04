import os

import ffmpeg
import requests
import youtube_dl
from flask import jsonify


def classification(request):
    url = request.json["url"]
    upload_url = request.json["upload_url"]
    music_path = "ytmusic.mp3"

    # 既存ファイルがあるとスキップされる？同じURLがダウンロードされる？ダウロード失敗がある？プロセスに時間がかかる？
    is_file = os.path.isfile(music_path)
    if is_file:
        os.remove(music_path)

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": "./" + music_path,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # url = "https://iut-b.main.jp/up2"
    url = upload_url
    files = {"file": open(music_path, "rb")}
    res = requests.post(url, files=files)

    return jsonify({"new_video_path": res.status_code}), 201
