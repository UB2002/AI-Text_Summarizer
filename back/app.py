from transformers import pipeline
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from celery import Celery
import torch
import redis
import time
import logging
import gc  # Garbage Collection

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# 🚀 Enable GPU Acceleration if available
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load the pre-trained Hugging Face summarizer pipeline (optimized for GPU if available)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=0 if device == "cuda" else -1)

# 🔹 Initialize Flask-Limiter (Rate Limiting)
limiter = Limiter(app, key_func=get_remote_address)

# 🔹 Initialize Flask-Caching (To Avoid Redundant Computation)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

# 🔹 Celery Configuration (for Asynchronous Processing)
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend="redis://localhost:6379",
        broker="redis://localhost:6379"
    )
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)

# 🔹 Setup Logging for API Performance Monitoring
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 🛠 Helper Functions
def sanitize_input(text):
    """Sanitizes input to remove special characters."""
    import re
    return re.sub(r'[^\w\s,.!?]', '', text)

def split_large_text(text, max_tokens=500):
    """Splits large text into chunks to avoid model token limits."""
    words = text.split()
    return [' '.join(words[i:i + max_tokens]) for i in range(0, len(words), max_tokens)]

def choose_device_based_on_input(text):
    """Uses GPU for large texts, CPU for small ones"""
    word_count = len(text.split())
    return "cuda" if word_count > 100 and torch.cuda.is_available() else "cpu"

# 🟢 Async Task: Runs Summarization in the Background
@celery.task
def summarize_task(text):
    """Handles large text summarization asynchronously"""
    chunks = split_large_text(text)
    summarized_chunks = [summarizer(chunk, max_length=150, min_length=30, do_sample=False)[0]['summary_text'] for chunk in chunks]
    return ' '.join(summarized_chunks)

# 🔷 API Endpoints
@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to AI Text Summarizer!"})

# 🔹 Summarization Endpoint with Caching, Rate Limiting & Large Text Handling
@app.route("/summarize", methods=["POST"])
@limiter.limit("5 per minute")  # ⏳ Limits 5 requests per minute per IP
@cache.cached(timeout=60, query_string=True)  # 🛑 Cache results for 60 seconds
def summarize():
    data = request.get_json()
    text = sanitize_input(data["text"])

    # Handle large text by splitting into chunks
    chunks = split_large_text(text)
    selected_device = choose_device_based_on_input(text)

    # Run the summarization task asynchronously
    task = summarize_task.delay(text)

    return jsonify({"task_id": task.id, "status": "Processing"})

# 🔹 Get Summarization Result (Fetch From Celery Task)
@app.route("/result/<task_id>", methods=["GET"])
def get_result(task_id):
    task = summarize_task.AsyncResult(task_id)
    if task.state == "PENDING":
        return jsonify({"status": "Processing"})
    elif task.state == "SUCCESS":
        return jsonify({"summary": task.result})
    else:
        return jsonify({"status": task.state})

# 🔹 Streaming Response for Large Text Summarization
@app.route("/stream_summarize", methods=["POST"])
def stream_summarize():
    data = request.get_json()
    text = sanitize_input(data["text"])
    chunks = split_large_text(text)

    def generate():
        for chunk in chunks:
            summary = summarizer(chunk, max_length=150, min_length=30, do_sample=False)[0]['summary_text']
            yield summary + "\n\n"

    return Response(generate(), mimetype="text/plain")

# 🔹 Monitoring API Performance & Memory Management
@app.before_request
def start_timer():
    request.start_time = time.perf_counter()

@app.after_request
def log_request(response):
    duration = time.perf_counter() - request.start_time
    logging.info(f"Processed in {duration:.3f} sec | Status: {response.status_code}")
    
    # Free up memory to prevent overload
    gc.collect()
    torch.cuda.empty_cache()
    
    return response

# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)


#################################################################################
                                                                               ##
                                                                               ##
#################################################################################
# from transformers import pipeline
# from flask import Flask, request, jsonify
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)

# # Load the pre-trained Hugging Face summarizer pipeline
# #summarizer = pipeline("summarization")
# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
# '''
# @app.route('/', methods=['GET'])
# def index():
#     #res.send
#     return"hello from backend"
# '''


# @app.route('/summarize', methods=['POST'])
# def summarize():
#     data = request.get_json()
#     text = data['text']
#     summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
#     return jsonify(summary[0])

# if __name__ == "__main__":
#     app.run(debug=True)
