from flask import Flask, request, jsonify
import os
import logging
from faster_whisper import WhisperModel
from pymongo import MongoClient
import time
import json
from datetime import datetime
import subprocess
from flask_cors import CORS

# Встановлення logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )

setup_logging()

app = Flask(__name__)
CORS(app)  # Додає підтримку CORS для всіх маршрутів

# Максимальний розмір файлів 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Підключення до MongoDB
client = MongoClient('mongodb://mongo:27017/')
db = client['transcriptions_db']
collection = db['transcriptions']
collectionFiles = db['not_processed']

@app.route('/process', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    audio_file = request.files['audio']
    audio_path = f"./uploads/{audio_file.filename}"
    audio_file.save(audio_path)

    result = {
        'fileName': audio_file.filename,
        'status': 'not_processed',
        'created': int(time.time()),
        'edited': int(time.time())
    }

    # Збереження до MongoDB
    collectionFiles.insert_one(result)

    return jsonify({'message': 'file save'})


@app.route('/search', methods=['GET'])
def search_transcriptions():
    query = request.args.get('query', '')

    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    try:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
    except ValueError:
        return jsonify({'error': 'Offset and limit must be integers'}), 400

    regex_query = {"segments.text": {"$regex": query, "$options": "i"}}
    matching_transcriptions = list(collection.find(regex_query, {'_id': 0}).sort('time', -1).skip(offset).limit(limit))
    count = matching_transcriptions_count = collection.count_documents({"info.text": {"$regex": ".*", "$options": "i"}})

    # Видалення поля ObjectId
    for transcription in matching_transcriptions:
        transcription.pop('_id', None)

    return jsonify({
        'list': matching_transcriptions,
        'count': count
    })

@app.route('/files', methods=['GET'])
def fetch_files():
    try:
        records = collectionFiles.find()
        files_list = []
        for record in records:
            record.pop('_id', None)
            files_list.append(record)
        return jsonify(files_list), 200
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
