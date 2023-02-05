import gc
import glob
import imp
import os
import shutil
import tempfile
from datetime import datetime

import cv2
import requests
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "./uploads/"
ALLOWED_EXTENSIONS = {"mp3", "mp4", "mpg"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 2 * 1000 * 1000 * 1000
bootstrap = Bootstrap(app)

app.secret_key = "9KStWezC"


# from apps.crud import views as crud_views
# app.register_blueprint(crud_views.crud, url_prefix="/crud")

# スペースでなくタブを使うとエラーとなる
# ffmpeg、ffmpegを使用するmoviepyはlolipopサーバーで使用不可
# tmpdir = tempfile.mkdtemp()は外部からアクセス不能
# タイムアウトを防ぐため処理を分割


@app.route("/", methods=["GET", "POST"])
def editor():
    if request.method == "POST":
        dir = "./uploads/driving"
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

        video = request.files["video"]
        music = request.files["music"]
        url = request.form.get("youtube")

        if video.filename == "":
            flash("動画が選択されていません")
            return redirect(request.url)

        if not allowed_file(video.filename):
            flash("ファイル形式が違います")
            return redirect(request.url)

        if music.filename == "" and url == "":
            flash("音楽が選択されていません")
            return redirect(request.url)

        if music.filename != "" and url != "":
            flash("音楽はファイルまたはYouTubeのどちらかのみを選択してください")
            return redirect(request.url)

        if music.filename != "" and not allowed_file(music.filename):
            flash("ファイル形式が違います")
            return redirect(request.url)

        if url != "" and not url.startswith("https://www.youtube.com/"):
            flash("YouTubeのURLを入力してください")
            return redirect(request.url)

        video_name = secure_filename(video.filename)
        video.save("./uploads/video/" + video_name)

        if music.filename == "":
            data = {
                "url": url,
                # "upload_url": "https://iut-b.main.jp/driving_app/up2",
                "upload_url": "http://iut-b.main.jp/driving_app/up2",
            }
            r = requests.post(
                # "https://detector-app-20221031-3-22-d6ljr4zrfa-an.a.run.app/classification",
                "https://detector-app-20221031-3-40-d6ljr4zrfa-an.a.run.app/classification",
                json=data,
            )
            music_name = "ytmusic.mp3"
        else:
            music_name = secure_filename(music.filename)
            music.save("./uploads/music/" + music_name)

        session["video_name"] = video_name
        session["music_name"] = music_name
        return redirect("/driving_app/sampling")
    else:
        return render_template("index.html")


@app.route("/sampling", methods=["GET"])
def sampling():
    if request.method == "GET":
        # flash('sampling...')
        video_name = session["video_name"]

        # 動画のフレームのサンプリング間隔
        sampling_sec = 5
        # 動画のフレームのサンプリング
        video = cv2.VideoCapture("./uploads/video/" + video_name)
        fps = int(sampling_sec * video.get(cv2.CAP_PROP_FPS))
        i = 0
        while video.isOpened():
            ret, frame = video.read()
            if ret == False:
                break
            if i % fps == 0:
                # pathに日本語を含めないこと
                cv2.imwrite("./uploads/frames/" + "img_%s.png" % str(i).zfill(6), frame)
            i += 1
        video.release()

        session["sampling_sec"] = sampling_sec
        return redirect("/driving_app/selecting")


@app.route("/selecting", methods=["GET"])
def selecting():
    if request.method == "GET":

        # サンプリングしたフレームの分類
        scene = selecting_scene()

        session["scene"] = scene
        return redirect("/driving_app/classifying")


@app.route("/classifying", methods=["GET"])
def classifying():
    if request.method == "GET":
        video_name = session["video_name"]
        scene = session["scene"]
        sampling_sec = session["sampling_sec"]

        video = cv2.VideoCapture("./uploads/video/" + video_name)
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        size = (width, height)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_rate = int(video.get(cv2.CAP_PROP_FPS))
        fmt = cv2.VideoWriter_fourcc("m", "p", "4", "v")

        # ワンシーンの時間
        Ts = 25
        scene2 = [0]
        for i in range(len(scene) - 1):
            if scene[i] * sampling_sec + Ts / 2 < scene[i + 1] * sampling_sec - Ts / 2:
                scene2.append(scene[i + 1])

        new_video_sec = (len(scene2) - 1 / 2) * Ts
        music_sec = 600

        x = 1
        if new_video_sec > music_sec:
            x = new_video_sec / music_sec
        elif new_video_sec <= music_sec:
            music_sec = new_video_sec
        # 切り出し動画の保存先
        new_video_name = video_name.rsplit(".", 1)[0] + "_edited.mp4"
        cutout_path = "./uploads/video/" + new_video_name
        writer = cv2.VideoWriter(cutout_path, fmt, int(x * frame_rate), size)

        # 動画の切り出し
        for s in scene2:
            start = s * sampling_sec - Ts / 2
            if start < 0:
                start = 0

            end = s * sampling_sec + Ts / 2
            if end > frame_count * frame_rate:
                end = frame_count * frame_rate

            i = start * frame_rate
            video.set(cv2.CAP_PROP_POS_FRAMES, i)
            while i <= end * frame_rate:
                ret, frame = video.read()
                writer.write(frame)
                i = i + 1

        writer.release()
        video.release()
        cv2.destroyAllWindows()

        session["new_video_name"] = new_video_name
        return redirect("/driving_app/generating")


@app.route("/generating", methods=["GET"])
def generating():
    if request.method == "GET":
        new_video_name = session["new_video_name"]
        music_name = session["music_name"]

        # video_path="http://iut-b.main.jp/uploads/video/"+new_video_name
        # music_path="http://iut-b.main.jp/uploads/music/"+music_name
        video_path = "http://iut-b.main.jp/driving_app/uploads/video/" + new_video_name
        music_path = "http://iut-b.main.jp/driving_app/uploads/music/" + music_name

        data = {
            "video_path": video_path,
            "music_path": music_path,
            "new_video_path": new_video_name,
            # "upload_url": "https://iut-b.main.jp/driving_app/up",
            "upload_url": "http://iut-b.main.jp/driving_app/up",
        }
        r = requests.post(
            # "https://detector-app-20221031-2-15-d6ljr4zrfa-an.a.run.app/classification",
            "https://detector-app-20221031-2-31-d6ljr4zrfa-an.a.run.app/classification",
            json=data,
        )

        session["new_video_name"] = new_video_name

        gc.collect()
        dir = "./uploads/video"
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

        dir = "./uploads/music"
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

        dir = "./uploads/frames"
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

        return redirect("/driving_app/driving_finished")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def selecting_scene():
    images = [f for f in os.listdir("./uploads/frames") if f[-4:] in [".png", ".jpg"]]
    data = {
        # "url": "http://iut-b.main.jp/uploads/frames/",
        "url": "http://iut-b.main.jp/driving_app/uploads/frames/",
        "images": images,
        "Nc": 5,
    }
    r = requests.post(
        "https://detector-app-20221031-14-d6ljr4zrfa-an.a.run.app/classification",
        json=data,
    )
    d = r.json()
    scene = d["scene"]

    return scene


@app.route("/driving_finished", methods=["GET", "POST"])
def driving_finished():
    if request.method == "POST":
        name = session["new_video_name"]
        return send_file(
            "./uploads/driving/" + name, as_attachment=True, mimetype="video/mp4"
        )
    else:
        return render_template("driving_finished.html")


@app.route("/up", methods=["POST"])
def up():
    if request.method == "POST":
        upload_file = request.files["file"]
        upload_file.save("./uploads/driving/" + upload_file.filename)
        return 201


@app.route("/up2", methods=["POST"])
def up2():
    if request.method == "POST":
        upload_file = request.files["file"]
        upload_file.save("./uploads/music/" + upload_file.filename)
        return 201


@app.route("/processing", methods=["POST"])
def processing():
    return render_template("processing.html")
