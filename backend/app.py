"""
BUMA Backend – Flask application.

Endpoints:
  GET  /health          → service status
  POST /chat            → audio in, audio out (main conversation loop)
  GET  /stats/<user_id> → learning statistics
  POST /teach           → structured vocabulary lesson (audio out)
"""

import io
import os
from datetime import datetime

from flask import Flask, jsonify, request, send_file
from dotenv import load_dotenv
from pymongo import MongoClient

from services.stt import STTService
from services.llm import LLMService
from services.tts import TTSService

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
load_dotenv()

app = Flask(__name__)

# Services
stt = STTService(api_key=os.environ["GROQ_API_KEY"])
llm = LLMService(api_key=os.environ["GROQ_API_KEY"])
tts = TTSService(
    voice_model=os.getenv("TTS_VOICE", "fr_FR-siwis-medium"),
    voices_dir=os.getenv("TTS_VOICES_DIR"),
)

# Database (optional — falls back to in-memory if no URI provided)
_mongo_uri = os.getenv("MONGODB_URI")
if _mongo_uri:
    _mongo = MongoClient(_mongo_uri)
    db = _mongo["buma"]
else:
    db = None  # graceful degradation: skip persistence

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_history(user_id: str, limit: int = 4) -> list[dict]:
    """Return recent conversation turns for context (newest last)."""
    if db is None:
        return []
    docs = list(
        db.conversations.find({"user_id": user_id})
        .sort("timestamp", -1)
        .limit(limit)
    )
    docs.reverse()
    return docs


def _save_turn(user_id: str, question: str, response: str, language: str) -> None:
    if db is None:
        return
    db.conversations.insert_one(
        {
            "user_id": user_id,
            "question": question,
            "response": response,
            "language": language,
            "timestamp": datetime.utcnow(),
        }
    )

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "BUMA Backend",
            "db_connected": db is not None,
        }
    )


@app.route("/chat", methods=["POST"])
def chat():
    """Main conversation endpoint: audio in → audio out."""
    start = datetime.utcnow()

    audio_file = request.files.get("audio")
    user_id = request.form.get("user_id", "default")

    if not audio_file:
        return jsonify({"error": "No audio file provided"}), 400

    try:
        # 1. STT
        audio_bytes = audio_file.read()
        transcript = stt.transcribe(audio_bytes)
        user_text = transcript["text"]
        language = transcript["language"]
        print(f"[{user_id}] STT ({language}): {user_text}")

        # 2. LLM
        history = _get_history(user_id)
        buma_text = llm.respond(user_text, history)
        print(f"[{user_id}] LLM: {buma_text}")

        # 3. Persist
        _save_turn(user_id, user_text, buma_text, language)

        # 4. TTS
        audio_out = tts.synthesise(buma_text)

        duration = (datetime.utcnow() - start).total_seconds()
        print(f"[{user_id}] Done in {duration:.2f}s")

        return send_file(
            io.BytesIO(audio_out),
            mimetype="audio/wav",
            as_attachment=True,
            download_name="response.wav",
        )

    except Exception as exc:
        print(f"[{user_id}] ERROR: {exc}")
        return jsonify({"error": str(exc)}), 500


@app.route("/stats/<user_id>", methods=["GET"])
def stats(user_id: str):
    if db is None:
        return jsonify({"error": "Database not configured"}), 503

    total = db.conversations.count_documents({"user_id": user_id})
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
    ]
    lang_stats = list(db.conversations.aggregate(pipeline))

    return jsonify(
        {
            "user_id": user_id,
            "total_conversations": total,
            "languages": {s["_id"]: s["count"] for s in lang_stats},
        }
    )


@app.route("/teach", methods=["POST"])
def teach():
    """Return a short vocabulary lesson as audio."""
    VOCABULARY = {
        "animals": {
            "fr": ["chat", "chien", "oiseau", "poisson", "lapin"],
            "en": ["cat", "dog", "bird", "fish", "rabbit"],
            "ar": ["قط", "كلب", "طائر", "سمكة", "أرنب"],
        },
        "colors": {
            "fr": ["rouge", "bleu", "vert", "jaune", "orange"],
            "en": ["red", "blue", "green", "yellow", "orange"],
            "ar": ["أحمر", "أزرق", "أخضر", "أصفر", "برتقالي"],
        },
    }

    data = request.get_json(silent=True) or {}
    category = data.get("category", "animals")
    count = min(data.get("count", 3), 5)

    if category not in VOCABULARY:
        return jsonify({"error": f"Unknown category: {category}"}), 400

    words = VOCABULARY[category]
    lesson = f"Hoot hoot! Today we learn {category}! "
    for i in range(count):
        lesson += (
            f"Number {i + 1}: {words['en'][i]} in English, "
            f"{words['fr'][i]} in French, "
            f"{words['ar'][i]} in Arabic. "
        )
    lesson += "Can you repeat them? Peux-tu répéter?"

    try:
        audio = tts.synthesise(lesson)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return send_file(
        io.BytesIO(audio),
        mimetype="audio/wav",
        as_attachment=True,
        download_name="lesson.wav",
    )


# ---------------------------------------------------------------------------
# Entry point (local dev)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
