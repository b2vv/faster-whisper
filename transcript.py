from flask import Flask, request, jsonify
import os
import logging
from faster_whisper import WhisperModel
from pymongo import MongoClient
import time
import json
from datetime import datetime
import sys

main_dir = '/app'

# Підключення до MongoDB
client = MongoClient('mongodb://mongo:27017/')
db = client['transcriptions_db']
collection = db['transcriptions']
collectionFiles = db['not_processed']

record = collectionFiles.find_one({'status': {'$ne': 'removed'}})

if not record:
    print("No record found. Exiting script.")
    sys.exit(1)

record = collectionFiles.find_one({'status': 'processing'})

def format_duration(seconds):
    """Converts seconds to a human-readable format."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))

if record and (int(time.time()) - record['edited']) < (15 * 60):
    print("Found Record:", record)
    sys.exit(1)

startTime = datetime.now()
# Шлях до попередньо завантаженої моделі
model_name = os.environ.get('MODEL_NAME', "small")
model_path = f"{main_dir}/models/{model_name}"

# Завантаження моделі Faster Whisper з float32
model = WhisperModel(model_path, compute_type="float32")

if record and ((int(time.time()) - record['edited']) > (15 * 60)):
    file = record
    print('Get old file')
else:
    print('Get new file')
    file = collectionFiles.find_one({'status': 'not_processed'})

collectionFiles.update_one(
    {'_id': file['_id']},
    {'$set': {'status': 'processing', 'edited': int(time.time())}}
)
audio_path = f"{main_dir}/uploads/{file['fileName']}"
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
    'file-name': file['fileName'],
    'time': int(time.time())
}

# Збереження до MongoDB
collection.insert_one(result)

duration = datetime.now() - startTime
duration_human = format_duration(duration.total_seconds())
collectionFiles.update_one({'_id': file['_id']}, {'$set': {'status': 'removed', 'edited': int(time.time()), 'duration': duration_human}})

# Збереження до файлу
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
result_filename = f"{main_dir}/transcriptions/{file['fileName']}_transcription_{timestamp}.json"
os.makedirs(os.path.dirname(result_filename), exist_ok=True)

fileText = "\n".join(seg['text'] for seg in result['segments'])

with open(result_filename, 'w') as f:
    f.write(fileText)

# Видалення тимчасового файлу
os.remove(audio_path)