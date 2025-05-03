import os
import io
import asyncio
from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
import edge_tts
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),              # Sentry DSN
    integrations=[FlaskIntegration()],                # Flask integration
    traces_sample_rate=0.1,                           # adjust sample rate
    send_default_pii=False
)

app = Flask(__name__)

# Secure CORS: read allowed origins from environment variable
# FRONTEND_ORIGINS should be a comma-separated list of origins, e.g. "http://localhost:8080,http://127.0.0.1:8080"
allowed_origins = os.getenv("FRONTEND_ORIGINS", "").split(",")
# Ensure non-empty list; default to localhost if not set
if not allowed_origins or allowed_origins == ['']:
    allowed_origins = ["http://127.0.0.1:8080/", "https://iodv.netlify.app" ,"https://rxt.pages.dev"]

# Apply CORS only to /tts, allow POST and OPTIONS, and required headers
CORS(app, resources={
    r"/tts": {
        "origins": allowed_origins,
        "methods": ["OPTIONS", "POST", "GET"],
        "allow_headers": ["Content-Type", "X-API-KEY"]
    }
})

# Auth & preflight handling
@app.before_request
def authenticate_and_method_check():
    # Let the CORS preflight through
    if request.method == "OPTIONS":
        return make_response("", 204)

    # Only allow POST for actual requests
    if request.method != "POST":
        return jsonify({"error": "Method Not Allowed"}), 405

    # Validate API key
    api_key = request.headers.get("X-API-KEY", "")
    expected = os.getenv("API_KEY", "")
    if api_key != expected:
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/tts', methods=['OPTIONS', 'POST'])
def text_to_speech():
    data = request.get_json(force=True)
    text = data.get('text', '')

    # Validate input
    if not isinstance(text, str) or not text.strip():
        return jsonify({'error': 'Invalid text'}), 400

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
        # Capture in Sentry and return generic error
        sentry_sdk.capture_exception(e)
        return jsonify({'error': 'Internal Server Error'}), 500

    return send_file(audio_stream, mimetype='audio/mpeg', as_attachment=True, download_name='output.mp3')

# Gunicorn entry point
if __name__ != "__main__":
    application = app