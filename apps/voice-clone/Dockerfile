# Imagen del servicio de clonación de voz (Chatterbox Multilingual V3, MIT).
# Uso en GPU cloud:
#   RunPod / HF Spaces: expone el puerto 8000; el backend consume el contrato HTTP.
#   Local sin GPU (PoC, lento):  docker build -t agroia-voice-clone . && docker run -p 8000:8000 agroia-voice-clone
FROM python:3.11-slim

# ffmpeg convierte la muestra webm del navegador a wav 24 kHz mono.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# torch 2.6.0 (cu124) se instala como dependencia de chatterbox.
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV CHATTERBOX_T3_MODEL=v3 \
    CHATTERBOX_LANGUAGE_ID=es

EXPOSE 8000
# Respeta $PORT para plataformas que lo inyectan (p. ej. HF Spaces usa 7860).
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
