from transformers import pipeline
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load the pre-trained Hugging Face summarizer pipeline
#summarizer = pipeline("summarization")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
'''
@app.route('/', methods=['GET'])
def index():
    #res.send
    return"hello from backend"
'''


@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.get_json()
    text = data['text']
    summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
    return jsonify(summary[0])

if __name__ == "__main__":
    app.run(debug=True, port= 3001)
