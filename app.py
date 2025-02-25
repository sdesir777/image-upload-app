from flask import Flask, render_template, request, redirect, send_from_directory
from google.cloud import storage
import google.generativeai as genai
import os
import json
import re

app = Flask(__name__)

BUCKET_NAME = "image-upload-sd-12345"

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT = "Generate a JSON object with 'title' and 'description' for this image."

def generate_image_description(image_path):
    """Uploading the image to Gemini and generates a title and description."""
    try:
        file = genai.upload_file(image_path, mime_type="image/jpeg")
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content([file, PROMPT])

        print("Raw response from GEMINI AI:", response.text)

        json_match = re.search(r"```json\n(.*?)\n```", response.text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            json_text = response.text

        try:
            json_response = json.loads(json_text)
        except json.JSONDecodeError:
            print("ERROR: Gemini did not return valid JSON.")
            json_response = {}

        if isinstance(json_response, dict) and "title" in json_response and "description" in json_response:
            title = json_response["title"]
            description = json_response["description"]
        else:
            print("ERROR: Unexpected response format from Gemini AI")
            title, description = "No Title Generated", "No Description Available"

    except Exception as e:
        print(f"ERROR: {e}")
        title, description = "No Title Generated", "No Description Available"
    
    return title, description 

@app.route("/")
def index():
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs()

    images = []
    descriptions = {}

    for blob in blobs:
        if blob.name.endswith((".png", ".jpg", ".jpeg")):
            images.append(blob.name)

            json_filename = blob.name.rsplit(".", 1)[0] + ".json"
            json_blob = bucket.blob(json_filename)

            if json_blob.exists():
                try: 
                    json_data = json_blob.download_as_text()
                    descriptions[blob.name] = json.loads(json_data)
                except ValueError:
                    descriptions[blob.name] = {"title": "Error", "description": "Invalid JSON format"}


    return render_template("upload.html", images=images, descriptions=descriptions)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files['image']
    if file:
        filename = file.filename
        local_path = os.path.join("uploads", filename)

        os.makedirs("uploads", exist_ok=True)
        file.save(local_path)

        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_filename(local_path)

        title, description = generate_image_description(local_path)

        metadata = {"title": title, "description": description}
        json_filename = filename.rsplit(".", 1)[0] + ".json"
        json_blob = bucket.blob(json_filename)
        json_blob.upload_from_string(json.dumps(metadata))

    return redirect("/")

@app.route("/uploads/<filename>")
def serve_file(filename):
    return send_from_directory("uploads", filename)

if __name__ == "__main__":
    app.run(debug=True)
