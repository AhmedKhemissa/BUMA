"""
BUMA Raspberry Pi Client

Listens for the "BUMA" wake word via Porcupine, records the child's
question, sends it to the cloud backend, and plays the audio response.
"""

import os
import struct
import subprocess
import threading
import time
import uuid
import wave

import pyaudio
import pvporcupine
import requests

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

PORCUPINE_KEY = os.getenv("PORCUPINE_KEY", "YOUR_PICOVOICE_KEY")
WAKE_WORD_PATH = os.getenv("WAKE_WORD_PATH", "BUMA_raspberry-pi.ppn")
BACKEND_URL = os.getenv("BACKEND_URL", "https://buma-backend.onrender.com")
RECORD_SECONDS = int(os.getenv("RECORD_SECONDS", "5"))
SAMPLE_RATE = 16000
USER_ID = os.getenv("BUMA_USER_ID", str(uuid.uuid4())[:8])

CHAT_ENDPOINT = f"{BACKEND_URL}/chat"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"

# ──────────────────────────────────────────────
# Keep-alive thread (prevents Render cold starts)
# ──────────────────────────────────────────────

def _keep_warm():
    """Ping the backend every 10 minutes so Render doesn't sleep."""
    while True:
        time.sleep(600)
        try:
            requests.get(HEALTH_ENDPOINT, timeout=5)
        except Exception:
            pass

threading.Thread(target=_keep_warm, daemon=True).start()

# ──────────────────────────────────────────────
# Audio helpers
# ──────────────────────────────────────────────

pa = pyaudio.PyAudio()


def record_audio(duration: int = RECORD_SECONDS, filename: str = "question.wav") -> str:
    """Record from the default mic and save to a WAV file."""
    CHUNK = 1024
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print("\n  Recording", end="", flush=True)
    frames: list[bytes] = []
    ticks = int(SAMPLE_RATE / CHUNK * duration)
    half_sec = int(SAMPLE_RATE / CHUNK * 0.5)

    for i in range(ticks):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        if half_sec and i % half_sec == 0:
            print(".", end="", flush=True)

    print(" done")

    stream.stop_stream()
    stream.close()

    wf = wave.open(filename, "wb")
    wf.setnchannels(1)
    wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    return filename


def send_to_backend(audio_path: str) -> str | None:
    """POST the recorded WAV to the backend; return path to response audio."""
    print("  Sending to BUMA...", end="", flush=True)
    start = time.time()

    try:
        with open(audio_path, "rb") as f:
            resp = requests.post(
                CHAT_ENDPOINT,
                files={"audio": f},
                data={"user_id": USER_ID},
                timeout=20,
            )

        elapsed = time.time() - start

        if resp.status_code == 200:
            print(f" ok ({elapsed:.1f}s)")
            out = "response.wav"
            with open(out, "wb") as f:
                f.write(resp.content)
            return out

        print(f" error {resp.status_code}")
        return None

    except requests.exceptions.Timeout:
        print(" timeout (server may be waking up)")
        return None
    except Exception as exc:
        print(f" {exc}")
        return None


def play_audio(filename: str) -> None:
    """Play a WAV file through the default output device."""
    print("  BUMA is speaking...")
    # aplay is standard on Raspberry Pi OS
    subprocess.run(["aplay", "-q", filename])

# ──────────────────────────────────────────────
# Main loop
# ──────────────────────────────────────────────

def main() -> None:
    print(
        "\n"
        "========================================\n"
        "   BUMA Voice Assistant\n"
        "   100% Free  |  4-6s response\n"
        "========================================\n"
    )
    print(f"  Device ID : {USER_ID}")
    print(f"  Backend   : {BACKEND_URL}")
    print(f"  Record    : {RECORD_SECONDS}s\n")
    print("  Initialising wake word engine...")

    porcupine = pvporcupine.create(
        access_key=PORCUPINE_KEY,
        keyword_paths=[WAKE_WORD_PATH],
    )

    wake_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length,
    )

    print('  Ready — say "BUMA" to talk\n')

    count = 0

    try:
        while True:
            pcm = wake_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            if porcupine.process(pcm) >= 0:
                count += 1
                print(f"--- Conversation #{count} ---")

                audio_file = record_audio()
                response_file = send_to_backend(audio_file)

                if response_file:
                    play_audio(response_file)
                    os.remove(response_file)
                else:
                    print("  Could not reach BUMA — try again.")

                os.remove(audio_file)
                print()

    except KeyboardInterrupt:
        print(f"\n  Bye! {count} conversations today.\n")
    finally:
        wake_stream.close()
        pa.terminate()
        porcupine.delete()


if __name__ == "__main__":
    main()
