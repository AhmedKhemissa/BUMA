# BUMA – Voice Language Assistant for Kids

A Raspberry Pi + cloud voice assistant that teaches children (5-7 years)
French, English and Arabic through playful conversation.

Built entirely on **free-tier services** — $0/month.

## Architecture

```
Raspberry Pi (client)          Cloud (backend on Render)
┌─────────────────┐           ┌──────────────────────┐
│ Porcupine wake  │──audio──▶│ Groq Whisper (STT)   │
│ word detection   │           │ Groq Llama 3.1 (LLM)│
│ Audio record     │◀─audio──│ Piper TTS            │
│ Audio playback   │           │ MongoDB Atlas (DB)   │
└─────────────────┘           └──────────────────────┘
```

## Quick start

See individual READMEs:

- [backend/README.md](backend/README.md) — deploy the cloud API
- [client/README.md](client/README.md) — run on the Raspberry Pi

## Project structure

```
backend/
  services/
    stt.py          # Speech-to-text (Groq Whisper)
    llm.py          # Language model (Groq Llama)
    tts.py          # Text-to-speech (Piper)
  app.py            # Flask routes
  requirements.txt
  .env.example
  Dockerfile
  render.yaml

client/
  buma_client.py    # Raspberry Pi wake-word + audio loop
  requirements.txt
```

## Free tier limits

| Service | Free Limit |
|---------|-----------|
| Groq | 14 400 req/day |
| Piper TTS | Unlimited |
| Porcupine | 1 custom wake word |
| Render | 750 hrs/month |
| MongoDB Atlas | 512 MB |
