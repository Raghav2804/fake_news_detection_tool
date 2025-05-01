from flask import Flask, render_template, request, jsonify
import os
import csv
import datetime
import shutil
from werkzeug.utils import secure_filename
import json

# Import custom modules
from text_processor import preprocess_text
from scraper import extract_content_from_url
from ocr import extract_text_from_image
from model import predict_fake_news
from news_api import get_trending_news

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
RESULTS_FOLDER = 'static/results'
PROCESSED_IMAGES_FOLDER = 'static/results/processed_images'
RESULTS_CSV = 'static/results/prediction_results.csv'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure directories exist - handle Windows paths properly
try:
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)

    if not os.path.exists(PROCESSED_IMAGES_FOLDER):
        os.makedirs(PROCESSED_IMAGES_FOLDER)
except Exception as e:
    print(f"Warning: Error creating directories: {e}")
    # Convert to Windows path format if needed
    if os.name == 'nt':  # Windows
        UPLOAD_FOLDER = UPLOAD_FOLDER.replace('/', '\\')
        RESULTS_FOLDER = RESULTS_FOLDER.replace('/', '\\')
        PROCESSED_IMAGES_FOLDER = PROCESSED_IMAGES_FOLDER.replace('/', '\\')
        RESULTS_CSV = RESULTS_CSV.replace('/', '\\')

        # Try again with Windows paths
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        if not os.path.exists(RESULTS_FOLDER):
            os.makedirs(RESULTS_FOLDER)

        if not os.path.exists(PROCESSED_IMAGES_FOLDER):
            os.makedirs(PROCESSED_IMAGES_FOLDER)

# Initialize CSV results file if it doesn't exist
if not os.path.exists(RESULTS_CSV):
    try:
        with open(RESULTS_CSV, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(
                ['timestamp', 'input_type', 'prediction', 'confidence', 'content_preview', 'source_url', 'image_path'])
    except Exception as e:
        print(f"Warning: Could not create results CSV file: {e}")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_result_to_csv(input_type, prediction, confidence, content_preview, source_url=None, image_path=None):
    """
    Save prediction result to CSV file

    Args:
        input_type: 'text', 'url', or 'image'
        prediction: 'real' or 'fake'
        confidence: prediction confidence score
        content_preview: preview of the content analyzed
        source_url: URL source (for URL analysis)
        image_path: path to the processed image (for image analysis)
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Truncate preview text if too long
        if content_preview and len(content_preview) > 500:
            content_preview = content_preview[:500] + "..."

        # Make sure directory exists
        os.makedirs(os.path.dirname(RESULTS_CSV), exist_ok=True)

        with open(RESULTS_CSV, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(
                [timestamp, input_type, prediction, confidence, content_preview, source_url or '', image_path or ''])
    except Exception as e:
        print(f"Error saving result to CSV: {e}")


@app.route('/', methods=['GET'])
def index():
    # Force model re-initialization on page load
    # This is for development to quickly see model updates
    # In production, this should be removed
    try:
        from model import initialize_model, model
        # Re-initialize the model
        model = initialize_model()
    except Exception as e:
        print(f"Warning: Could not re-initialize model: {e}")

    return render_template('index.html')


@app.route('/text', methods=['POST'])
def analyze_text():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text = data['text']
    if not text.strip():
        return jsonify({'error': 'Empty text provided'}), 400

    # Preprocess text
    processed_text = preprocess_text(text)

    # Make prediction
    prediction, confidence = predict_fake_news(processed_text)

    # Save result to CSV
    content_preview = text[:300] + '...' if len(text) > 300 else text
    save_result_to_csv('text', prediction, confidence, content_preview)

    return jsonify({
        'prediction': prediction,
        'confidence': confidence,
        'original_text': content_preview
    })


@app.route('/url', methods=['POST'])
def analyze_url():
    data = request.json
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400

    url = data['url']

    try:
        # Extract content from URL
        article_text = extract_content_from_url(url)
        if not article_text:
            return jsonify({'error': 'Could not extract content from URL'}), 400

        # Preprocess text
        processed_text = preprocess_text(article_text)

        # Make prediction
        prediction, confidence = predict_fake_news(processed_text)

        # Extract content preview
        content_preview = article_text[:300] + '...' if len(article_text) > 300 else article_text

        # Save result to CSV
        save_result_to_csv('url', prediction, confidence, content_preview, url)

        return jsonify({
            'prediction': prediction,
            'confidence': confidence,
            'extracted_text': content_preview,
            'source_url': url
        })
    except Exception as e:
        return jsonify({'error': f'Error processing URL: {str(e)}'}), 400


@app.route('/image', methods=['POST'])
def analyze_image():
    # Check if the post request has the file part
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']

    # If user does not select file, browser submits an empty file
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Extract text from image
            extracted_text = extract_text_from_image(filepath)
            if not extracted_text:
                return jsonify({'error': 'Could not extract text from image'}), 400

            # Preprocess text
            processed_text = preprocess_text(extracted_text)

            # Make prediction
            prediction, confidence = predict_fake_news(processed_text)

            # Create a copy of the image in results folder with prediction info
            try:
                filename_without_ext = os.path.splitext(os.path.basename(filepath))[0]
                result_filename = f"{filename_without_ext}_{prediction}_{int(confidence)}.jpg"
                result_filepath = os.path.join(PROCESSED_IMAGES_FOLDER, result_filename)

                # Copy the original image to results folder
                shutil.copy2(filepath, result_filepath)
            except Exception as e:
                print(f"Warning: Could not save result image: {e}")
                result_filepath = filepath  # Fallback to original path

            # Extract content preview
            content_preview = extracted_text[:300] + '...' if len(extracted_text) > 300 else extracted_text

            # Save result to CSV
            try:
                save_result_to_csv('image', prediction, confidence, content_preview, None, result_filepath)
            except Exception as e:
                print(f"Warning: Could not save to CSV: {e}")

            return jsonify({
                'prediction': prediction,
                'confidence': confidence,
                'extracted_text': content_preview,
                'image_path': filepath,
                'result_image_path': result_filepath
            })
        except Exception as e:
            return jsonify({'error': f'Error processing image: {str(e)}'}), 400
        finally:
            # Optionally: delete the file after processing
            # os.remove(filepath)
            pass
    else:
        return jsonify({'error': 'File type not allowed'}), 400


@app.route('/trending', methods=['GET'])
def trending_news():
    try:
        news = get_trending_news()
        return jsonify(news)
    except Exception as e:
        return jsonify({'error': f'Error fetching trending news: {str(e)}'}), 500


@app.route('/results', methods=['GET'])
def get_results():
    """
    API endpoint to get all saved prediction results
    """
    try:
        results = []
        if os.path.exists(RESULTS_CSV):
            with open(RESULTS_CSV, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    results.append(row)

        return jsonify(results)
    except Exception as e:
        return jsonify({'error': f'Error fetching results: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
