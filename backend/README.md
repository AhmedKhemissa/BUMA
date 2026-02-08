# BUMA Backend

Cloud backend for the BUMA voice assistant.  
Receives audio from the Raspberry Pi client, runs STT → LLM → TTS, and returns audio.

## Stack

| Component | Provider |
|-----------|----------|
| STT | Groq Whisper Large v3 |
| LLM | Groq Llama 3.1 70B |
| TTS | Piper (local subprocess) |
| DB | MongoDB Atlas (optional) |
| Hosting | Render free tier |

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

pip install -r requirements.txt

cp .env.example .env
# Fill in GROQ_API_KEY (required) and MONGODB_URI (optional)
```

Piper must be installed and on `PATH`.  
See https://github.com/rhasspy/piper for installation.

### Download a voice model (optional, for local path mode)

```bash
mkdir voices && cd voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json
```

Then set `TTS_VOICES_DIR=./voices` in `.env`.

## Run locally

```bash
python app.py
# Server starts on http://localhost:5000
```

## Test

```bash
curl http://localhost:5000/health

# With a WAV file:
curl -X POST -F "audio=@test.wav" -F "user_id=test" \
     http://localhost:5000/chat --output response.wav
```

## Deploy to Render

1. Push to GitHub.
2. Create a **Web Service** on [render.com](https://render.com) pointing at the repo.
3. Set environment variables `GROQ_API_KEY` and `MONGODB_URI`.
4. Render will use the `Dockerfile` or `render.yaml` automatically.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| POST | `/chat` | Audio in → audio out (main loop) |
| GET | `/stats/<user_id>` | Learning statistics |
| POST | `/teach` | Vocabulary lesson (JSON body: `category`, `count`) |
