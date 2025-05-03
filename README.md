# Flask API with Edge TTS (Real-time Audio Streaming)

This is a simple and lightweight Flask API that uses **Microsoft Edge TTS** to convert text to speech in real-time — **without saving audio files**. It streams the audio directly with adjustable bitrate for smooth performance.

## ⚙️ Tech Stack
- **Backend:** Python (Flask)
- **TTS Engine:** Edge TTS (via `edge-tts`)
- **Audio:** Streamed response (e.g., `audio/mpeg`)
- **Storage:** No file saved — fully in-memory

## 🚀 Features
- Convert text to speech instantly
- Real-time audio streaming with adjustable bitrate
- No file system usage — audio is streamed on-the-fly
- Simple API structure — ideal for integration with frontends, bots, or assistants

## 📦 API Example

**Endpoint:** `POST /speak`  
**Payload:**
```json
{
  "text": "String",
  "voice": "String",
  "bitrate": "48k" // default formate
}