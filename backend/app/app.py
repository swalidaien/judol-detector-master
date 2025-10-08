from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
import cv2, tempfile, easyocr, pickle, os

app = Flask(__name__)
CORS(app)

# ====== Load model ======
MODEL_PATH = os.path.abspath("rnn_model.h5")
model = tf.keras.models.load_model(MODEL_PATH)

# ====== Load tokenizer ======
TOKENIZER_PATH = os.path.abspath("tokenizer.pkl")
with open(TOKENIZER_PATH, 'rb') as f:
    tokenizer = pickle.load(f)

MAX_SEQUENCE_LENGTH = 100 

# ====== Init EasyOCR  ======
reader = easyocr.Reader(['id', 'en'])

# ====== Preprocess Text Function ======
def preprocess_text(text):
    sequence = tokenizer.texts_to_sequences([text])
    padded = pad_sequences(sequence, maxlen=MAX_SEQUENCE_LENGTH, padding="post", truncating="post")
    return padded

@app.route('/', methods=['GET'])
def index():
    return "Running";

# ====== Endpoint untuk teks langsung ======
@app.route('/api/detect-text', methods=['POST'])
def detect_text():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'Text tidak boleh kosong'}), 400

    processed = preprocess_text(text)
    prediction = model.predict(processed)[0][0]

    result = {
        'status': 'Terdeteksi Iklan Judi' if prediction > 0.5 else 'Tidak Terindikasi Iklan Judi',
        'confidence': f'{prediction * 100:.2f}%',
        'raw_confidence': float(prediction)
    }

    return jsonify(result)

# ====== Endpoint untuk gambar dengan OCR ======
@app.route('/api/detect-image', methods=['POST'])
def detect_image():
    if 'image' not in request.files:
        return jsonify({'error': 'File gambar tidak ditemukan'}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()

    # OCR menggunakan easyocr
    ocr_result = reader.readtext(image_bytes, detail=0)
    extracted_text = ' '.join(ocr_result)

    if not extracted_text.strip():
        return jsonify({'error': 'Teks tidak ditemukan di dalam gambar'}), 400

    # Prediksi
    processed = preprocess_text(extracted_text)
    prediction = model.predict(processed)[0][0]

    result = {
        'ocr_text': extracted_text,
        'status': 'Terdeteksi Iklan Judi' if prediction > 0.5 else 'Tidak Terindikasi Iklan Judi',
        'confidence': f'{prediction * 100:.2f}%',
        'raw_confidence': float(prediction)
    }

    return jsonify(result)

# ====== Endpoint untuk video ======
@app.route('/api/detect-video', methods=['POST'])
def detect_video():
    file = request.files.get('video')
    if not file:
        return jsonify({'error': 'No video uploaded'}), 400

    # Simpan video sementara
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        file.save(temp_video.name)
        video_path = temp_video.name

    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    detected = False
    final_prediction = 0.0
    max_frames = 300 

    try:
        while cap.isOpened() and frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % 30 == 0: 
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_frame:
                    frame_path = temp_frame.name
                    cv2.imwrite(frame_path, frame)

                # OCR
                ocr_result = reader.readtext(frame_path, detail=0)
                os.remove(frame_path)  # Hapus frame setelah dipakai

                combined_text = ' '.join(ocr_result)
                if combined_text.strip():
                    processed = preprocess_text(combined_text)
                    prediction = model.predict(processed)[0][0]
                    final_prediction = prediction

                    if prediction > 0.5:
                        detected = True
                        break

            frame_count += 1
    finally:
        cap.release()
        os.remove(video_path) 

    return jsonify({
        'status': 'Terdeteksi Iklan Judi' if detected else 'Tidak Terindikasi Iklan Judi',
        'confidence': f'{final_prediction * 100:.2f}%' if detected else '0.00%',
        'raw_confidence': float(final_prediction) if detected else 0.0,
        'checked_frames': frame_count
    })
    
if __name__ == '__main__':
    app.run()


