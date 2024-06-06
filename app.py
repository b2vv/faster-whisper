from flask import Flask, request, jsonify
import os
import logging
from faster_whisper import WhisperModel
from pymongo import MongoClient
import time
import json
from datetime import datetime


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

# Максимальний розмір файлів 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Підключення до MongoDB
client = MongoClient('mongodb://mongo:27017/')
db = client['transcriptions_db']
collection = db['transcriptions']

# Шлях до попередньо завантаженої моделі
model_name = os.environ.get('MODEL_NAME', "small")
model_path = f"./models/{model_name}"

# Завантаження моделі Faster Whisper з float32
model = WhisperModel(model_path, compute_type="float32")


@app.route('/process', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    audio_file = request.files['audio']
    audio_path = f"./uploads/{audio_file.filename}"
    audio_file.save(audio_path)

    # Обробка аудіо файлу
    segments, info = model.transcribe(audio_path)

    # Форматування результатів
    result = {
        'segments': [
            {'start': seg.start, 'end': seg.end, 'text': seg.text}
            for seg in segments
        ],
        'info': {
            'language': info.language,
            'duration': info.duration
        },
        'file-name': audio_file.filename,
        'time': int(time.time())
    }

    # Збереження до MongoDB
    collection.insert_one(result)

    # Видалення поля ObjectId
    result.pop('_id', None)

    # Збереження до файлу
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_filename = f"./transcriptions/{audio_file.filename}_transcription_{timestamp}.json"
    os.makedirs(os.path.dirname(result_filename), exist_ok=True)

    fileText = "\n".join(seg['text'] for seg in result['segments'])

    with open(result_filename, 'w') as f:
        f.write(fileText)

    # Видалення тимчасового файлу
    os.remove(audio_path)

    return jsonify(result)


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
