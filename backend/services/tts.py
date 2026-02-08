"""
Text-to-Speech service using Piper TTS (subprocess).
Swap this module to change TTS provider.
"""

import subprocess
from pathlib import Path

# Default voice model.  Override via constructor.
DEFAULT_VOICE = "fr_FR-siwis-medium"


class TTSService:
    """Synthesise speech with Piper (runs as a subprocess)."""

    def __init__(self, voice_model: str = DEFAULT_VOICE, voices_dir: str | None = None):
        self.voice_model = voice_model
        self.voices_dir = voices_dir  # optional: path to local .onnx files

    def _build_command(self) -> list[str]:
        cmd = ["piper", "--output_file", "-"]
        if self.voices_dir:
            model_path = str(Path(self.voices_dir) / f"{self.voice_model}.onnx")
            cmd += ["--model", model_path]
        else:
            cmd += ["--model", self.voice_model]
        return cmd

    def synthesise(self, text: str) -> bytes:
        """
        Convert *text* to WAV audio bytes.

        Raises RuntimeError if Piper fails.
        """
        cmd = self._build_command()

        result = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            capture_output=True,
        )

        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Piper TTS failed (rc={result.returncode}): {err}")

        return result.stdout
