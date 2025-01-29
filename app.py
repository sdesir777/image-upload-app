from flask import Flask, render_template, request, redirect, send_from_directory
from google.cloud import storage
import os

app = Flask(__name__)

BUCKET_NAME = "image-upload-bucket-sd"

@app.route("/")
def index():
    images = []
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    for filename in os.listdir(upload_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            images.append({"name": filename, "url": f"/uploads/{filename}"})
    return render_template("upload.html", images=images)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files['image']
    if file:
        upload_path = os.path.join("uploads", file.filename)
        os.makedirs("uploads", exist_ok=True)
        file.save(upload_path)
    return redirect("/")

@app.route("/uploads/<filename>")
def serve_file(filename):
    return send_from_directory("uploads", filename)

if __name__ == "__main__":
    app.run(debug=True)