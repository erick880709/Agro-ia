# Voice Clone — Chatterbox Multilingual V3 (TT-06)

Servicio HTTP autoalojado que expone el contrato de clonación de voz consumido por
`agroia_backend.services.clonacion_voz`. Usa **Chatterbox Multilingual V3** (MIT), el
único motor de clonación elegido con **soporte nativo de español** (incluida variante
Latam Spanish para acento colombiano).

## Contrato

| Método | Ruta | Body | Respuesta |
|---|---|---|---|
| POST | `/clonar` | `{"usuario_email", "audio_base64"}` | `{"voice_id", "estado"}` |
| GET | `/voces/{id}` | — | `{"voice_id", "estado"}` |
| POST | `/sintetizar` | `{"voice_id", "texto", "velocidad"}` | audio/wav |
| GET | `/health` | — | `{"status": "ok"}` |

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `CHATTERBOX_T3_MODEL` | `v3` | Modelo V3 multilingüe. Para Latam Spanish, ver `ResembleAI/Chatterbox-Multilingual-es-mx-latam`. |
| `CHATTERBOX_LANGUAGE_ID` | `es` | Idioma de síntesis (código ISO de 2 letras). |

## Despliegue

### RunPod Serverless / Pod (recomendado)

1. Sube la imagen (build desde este `Dockerfile`) a Docker Hub o ghcr.
2. Crea un Serverless Endpoint o Pod con GPU L4/RTX 3090 (24 GB).
3. Expón el puerto `8000`.
4. En AgroIA configura:
   - `CLONACION_VOZ_URL=https://<tu-endpoint>` 
   - `CLONACION_VOZ_TOKEN=<token-opcional>`

### Hugging Face Spaces (PoC gratuito, ZeroGPU)

1. Crea un Space tipo Docker con este repositorio como carpeta.
2. Asegura que el contenedor escuche en `$PORT` (o mapea 8000).
3. ZeroGPU es compartido; suficiente para validar el PoC.

## Notas

- Chatterbox es **zero-shot**: la "clonación" guarda la muestra y la usa como prompt de
  audio en cada síntesis; no hay entrenamiento.
- La muestra llega como `webm/opus` (grabada por el navegador) y se convierte a wav
  24 kHz mono con `ffmpeg`.
- Incluye el watermark perceptual de Resemble AI (PerTh) en cada audio generado.
