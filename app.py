from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from faster_whisper import WhisperModel

app = Flask(__name__)
CORS(app)

# Максимальний розмір файлів 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

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
        }
    }

    # Видалення тимчасового файлу
    os.remove(audio_path)

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
