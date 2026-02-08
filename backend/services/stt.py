"""
Speech-to-Text service using Groq Whisper.
Swap this module to change STT provider.
"""

from groq import Groq


class STTService:
    """Transcribe audio using Groq Whisper Large v3."""

    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> dict:
        """
        Transcribe raw audio bytes.

        Returns:
            dict with keys: text, language
        """
        transcription = self.client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3",
            language="fr",  # default; Whisper auto-detects well
            response_format="verbose_json",
        )

        text = transcription.text.strip()
        language = getattr(transcription, "language", "fr")

        return {"text": text, "language": language}
