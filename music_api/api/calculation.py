import ffmpeg
from flask import jsonify


def classification(request):
    # 音楽のパス
    music_path = request.json["music_path"]

    # 音楽の再生時間
    music_info = ffmpeg.probe(
        music_path,
    )
    music_sec = float(music_info["streams"][0]["duration"])

    return jsonify({"music_sec": music_sec}), 201
