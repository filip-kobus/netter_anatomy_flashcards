from flask import Flask, request, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
import json
from vision_ai_solution import VisionAI

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['IMAGES_LIST_FILE'] = 'uploaded_images.json'


def load_uploaded_images():
    if os.path.exists(app.config['IMAGES_LIST_FILE']):
        with open(app.config['IMAGES_LIST_FILE'], 'r') as f:
            images = json.load(f)
            if isinstance(images, list) and all(isinstance(img, dict) for img in images):
                return images
    return []


def save_uploaded_images(images):
    with open(app.config['IMAGES_LIST_FILE'], 'w') as f:
        json.dump(images, f)


@app.route('/')
def index():
    uploaded_images = load_uploaded_images()
    return render_template('index.html', uploaded_images=uploaded_images, grouped_boxes=None)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    caption = request.form.get('caption', '')
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        vision_ai = VisionAI(filepath)
        grouped_boxes = vision_ai.grouped_boxes

        uploaded_images = load_uploaded_images()
        image_details = {'filename': filename, 'caption': caption, 'grouped_boxes': grouped_boxes}
        if not any(img['filename'] == filename for img in uploaded_images):
            uploaded_images.append(image_details)
            save_uploaded_images(uploaded_images)

        return render_template('index.html', uploaded_images=uploaded_images, filename=filename,
                               grouped_boxes=grouped_boxes)


@app.route('/file/<filename>', endpoint='uploaded_file')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/image/<filename>')
def show_image(filename):
    uploaded_images = load_uploaded_images()
    image = next((img for img in uploaded_images if img['filename'] == filename), None)
    if image:
        return render_template('index.html', uploaded_images=uploaded_images, filename=filename,
                               grouped_boxes=image.get('grouped_boxes'))
    else:
        return 'Image not found', 404


if __name__ == "__main__":
    app.run(debug=True)
