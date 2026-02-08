FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends wget && \
    pip install --no-cache-dir piper-tts && \
    apt-get purge -y wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pre-download voice model so first request isn't slow.
# Uncomment and add .onnx + .onnx.json to a voices/ directory if needed.
# COPY voices/ ./voices/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--timeout", "120"]
