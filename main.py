import os
import io
import asyncio
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import edge_tts
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),              # Sentry DSN 
    integrations=[FlaskIntegration()],            # Flask integration 
    traces_sample_rate=0.1,                       # adjust sample rate 
    send_default_pii=False
)

app = Flask(__name__)

# Secure CORS
allowed_origins = os.getenv("FRONTEND_ORIGINS", "").split(",")
CORS(app, origins=allowed_origins)

# Auth & Method enforcement
@app.before_request
def authenticate_and_method_check():
    if request.method != "POST":
        return jsonify({"error": "Method Not Allowed"}), 405  # 
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != os.getenv("API_KEY", ""):
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json(force=True)
    text = data.get('text', '')

    # Validate input
    if not isinstance(text, str) or not text.strip():
        return jsonify({'error': 'Invalid text'}), 400
    if len(text) > 5000:
        return jsonify({'error': 'Text too long'}), 400

    async def generate_speech(txt):
        communicate = edge_tts.Communicate(txt, 'en-US-AnaNeural')
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                buf.write(chunk['data'])
        buf.seek(0)
        return buf

    try:
        audio_stream = asyncio.run(generate_speech(text))
    except Exception as e:
        # Sentry will capture this
        raise

    return send_file(audio_stream, mimetype='audio/mpeg', as_attachment=True, download_name='output.mp3')

if __name__ != "__main__":
    # Gunicorn will serve the app
    application = app