# BUMA Client (Raspberry Pi)

Voice client that runs on a Raspberry Pi.  
Listens for the **"BUMA"** wake word, records the child's question,
sends it to the cloud backend, and plays the response.

## Requirements

- Raspberry Pi (3B+ or newer) with a microphone and speaker
- Python 3.9+
- Picovoice account + custom "BUMA" wake word `.ppn` file

## Setup

```bash
cd client

pip install -r requirements.txt
sudo apt install -y portaudio19-dev   # for PyAudio
```

### Environment variables

Set these before running (or export in your shell profile):

```bash
export PORCUPINE_KEY="your_picovoice_access_key"
export WAKE_WORD_PATH="BUMA_raspberry-pi.ppn"
export BACKEND_URL="https://buma-backend.onrender.com"
export RECORD_SECONDS=5          # optional, default 5
export BUMA_USER_ID=child1       # optional, auto-generated if omitted
```

### Get your wake word file

1. Go to https://console.picovoice.ai
2. Create a custom wake word **"BUMA"** for Raspberry Pi (Cortex-A)
3. Download the `.ppn` file into this directory

## Run

```bash
python buma_client.py
```

Say **"BUMA"** → speak your question → hear the response.  
Press `Ctrl+C` to quit.

## How it works

1. Porcupine listens for the wake word locally (zero latency).
2. Records 5 seconds of audio.
3. Sends the WAV file to the backend `/chat` endpoint.
4. Backend returns a WAV response (STT → LLM → TTS).
5. Client plays the audio via `aplay`.

A background keep-alive thread pings the backend every 10 minutes
to prevent Render free-tier cold starts.
