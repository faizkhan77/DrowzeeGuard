import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    Response,
    send_from_directory,
)
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import cv2
import numpy as np
import subprocess
import shutil
import zipfile
import time


app = Flask(__name__)

# Define paths for uploads and outputs
# Define paths for uploads and outputs
UPLOAD_FOLDER = "static/uploads/"
OUTPUT_FOLDER = "static/outputs/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

model = YOLO("best.pt")


# Route for the home page
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files and "folder" not in request.files:
        return redirect(request.url)

    file = request.files.get("file")  # Single file upload
    folder_files = request.files.getlist("folder")  # Folder upload

    if file and file.filename != "":  # Handling single image/video upload
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        # Perform detection for an image
        if file_path.endswith(("png", "jpg", "jpeg", "JPG", "JPEG")):
            results = model.predict(file_path, save=True)
            output_dir = results[0].save_dir  # YOLO's output directory
            filename_without_ext = os.path.splitext(filename)[0]
            filename = f"{filename_without_ext}.jpg"  # Append .jpg as the new extension
            detected_image_path = os.path.join(output_dir, filename)
            destination_path = os.path.join(
                app.config["OUTPUT_FOLDER"], "images", filename
            )
            shutil.copy(detected_image_path, destination_path)

            return redirect(url_for("display_image", filename=filename))

        # Perform detection for a video
        elif file_path.endswith(("mp4",)):
            results = model.predict(file_path, save=True)
            output_dir = results[0].save_dir  # YOLO's output directory
            filename = filename.replace(".mp4", ".avi")
            detected_video_path = os.path.join(output_dir, filename)

            # Define path for the re-encoded MP4 video
            reencoded_filename = filename.rsplit(".", 1)[0] + "_processed.mp4"
            reencoded_video_path = os.path.join(
                app.config["OUTPUT_FOLDER"], "videos", reencoded_filename
            )
            ffmpeg_command = [
                "ffmpeg",
                "-y",  # Overwrite output file without asking
                "-i",
                detected_video_path,  # Input file
                "-vcodec",
                "libx264",  # H.264 for video encoding
                "-acodec",
                "aac",  # AAC for audio encoding
                "-strict",
                "experimental",  # Strict flag for FFmpeg
                reencoded_video_path,
            ]
            subprocess.run(ffmpeg_command, check=True)
            os.remove(detected_video_path)

            return redirect(url_for("display_video", filename=reencoded_filename))

    elif folder_files:  # Handling folder upload
        folder_path = os.path.join(app.config["UPLOAD_FOLDER"], "uploaded_folder")
        os.makedirs(folder_path, exist_ok=True)

        # Save all files from the folder
        for folder_file in folder_files:
            if folder_file.filename == "":
                continue
            filename = secure_filename(folder_file.filename)
            file_path = os.path.join(folder_path, filename)
            folder_file.save(file_path)

        # Perform detection for all images in the folder
        results = model.predict(source=folder_path, save=True)
        output_dir = results[0].save_dir  # YOLO's output directory

        # Create a unique folder for this specific upload to store detected files
        unique_folder_name = f"detected_folder_{int(time.time())}"  # Unique folder name based on timestamp
        detected_folder_path = os.path.join(
            app.config["OUTPUT_FOLDER"], "detected_folders", unique_folder_name
        )
        os.makedirs(detected_folder_path, exist_ok=True)

        # Save detected images from the folder
        for detected_file in os.listdir(output_dir):
            detected_file_path = os.path.join(output_dir, detected_file)
            if detected_file.endswith(("png", "jpg", "jpeg", "JPG", "JPEG")):
                destination_path = os.path.join(detected_folder_path, detected_file)
                shutil.copy(detected_file_path, destination_path)

        # Create a zip file of the detected folder
        zip_filename = f"{unique_folder_name}.zip"
        zip_filepath = os.path.join(app.config["OUTPUT_FOLDER"], zip_filename)

        # Zip the detected folder
        with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(detected_folder_path):
                for file in files:
                    zipf.write(
                        os.path.join(root, file),
                        os.path.relpath(os.path.join(root, file), detected_folder_path),
                    )
        print("doneeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        # Provide the path for the download
        return render_template(
            "display_folder_detection.html", zip_filename=zip_filename
        )

    return redirect(url_for("index"))


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(
        app.config["OUTPUT_FOLDER"], filename, as_attachment=True
    )


@app.route("/display/image/<filename>")
def display_image(filename):
    return render_template("display_image.html", filename=filename)


@app.route("/display/video/<filename>")
def display_video(filename):
    return render_template("display_video.html", filename=filename)


# Route to serve the live detection page
@app.route("/live_detection")
def live_detection():
    return render_template("live_detection.html")


# Route to handle the live camera stream
@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# def generate_frames():
#     camera = cv2.VideoCapture(1)  # Use the webcam

#     while True:
#         success, frame = camera.read()
#         if not success:
#             break
#         else:
#             # Perform detection
#             results = model(frame)

#             # Extract the first result and plot the detections on the frame
#             result = results[0]  # Access the first element of the results list
#             frame_with_detections = result.plot()  # Plot the detections on the frame

#             # Convert the frame to JPEG format
#             ret, buffer = cv2.imencode(".jpg", frame_with_detections)
#             frame = buffer.tobytes()

#             # Yield the frame to be used in the Response
#             yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

#     camera.release()


def generate_frames():
    camera = cv2.VideoCapture(2)  # Use the webcam

    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Perform detection
            results = model(frame)

            # Extract the first result and plot the detections on the frame
            result = results[0]  # Access the first element of the results list
            frame_with_detections = result.plot()  # Plot the detections on the frame

            # Convert the frame to JPEG format
            ret, buffer = cv2.imencode(".jpg", frame_with_detections)
            frame = buffer.tobytes()

            # Yield the frame to be used in the Response
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

    camera.release()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
