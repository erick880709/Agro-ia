# Guía de despliegue — Servicio de clonación de voz (Chatterbox V3)

> Objetivo: publicar el wrapper de `apps/voice-clone` en GPU cloud (RunPod) y
> conectarlo al backend de AgroIA (Render) para habilitar "Mi voz".

---

## 0. Prerrequisitos

- Docker Desktop instalado y con sesión iniciada.
- Cuenta en **Docker Hub** (gratis) o acceso a **GitHub Container Registry (ghcr)**.
- Cuenta en **RunPod** (https://runpod.io) con saldo (unos USD 5 bastan para el PoC).
- Acceso al dashboard de **Render** del servicio `agroia-backend`.

---

## 1. Construir la imagen local

```powershell
cd C:\Users\ELITEBOOK\OneDrive\Documentos\Repositorio\Trabajo\Agro-ia\apps\voice-clone
docker build -t agroia-voice-clone .
```

> La primera vez descargará PyTorch (≈ 2.5 GB). Tarda varios minutos.

### Probar en local (opcional, sin GPU será lento)

```powershell
docker run --rm -p 8000:8000 -e CHATTERBOX_LANGUAGE_ID=es agroia-voice-clone
# En otra terminal:
curl http://localhost:8000/health
```

---

## 2. Publicar la imagen en un registro

### Opción A — Docker Hub (más simple)

```powershell
docker tag agroia-voice-clone TU_USUARIO/agroia-voice-clone:latest
docker login
docker push TU_USUARIO/agroia-voice-clone:latest
```

### Opción B — GitHub Container Registry (ghcr)

```powershell
docker tag agroia-voice-clone ghcr.io/erick880709/agroia-voice-clone:latest
echo $env:GH_TOKEN | docker login ghcr.io -u erick880709 --password-stdin
docker push ghcr.io/erick880709/agroia-voice-clone:latest
```

> En ghcr, el paquete debe hacerse público: GitHub → Paquetes → `agroia-voice-clone`
> → *Package settings* → *Change visibility* → **Public**.

---

## 3. Desplegar en RunPod (Pod con GPU) — recomendado

1. Ve a **RunPod → Pods → Deploy** (https://www.runpod.io/console/pods).
2. Selecciona GPU: **RTX 3090** (24 GB, $0.50/h) o **L4** (24 GB, $0.59/h). Cualquiera
   alcanza para Chatterbox V3 (0.5B).
3. En **Template**: elige *RunPod PyTorch* (o una plantilla base con CUDA 12.x).
4. En **Container Image**: pega la imagen publicada (p. ej. `TU_USUARIO/agroia-voice-clone:latest`).
5. En **Expose HTTP Port**: `8000`.
6. Pulsa **Deploy** y espera a que el Pod pase a *Running* (la primera carga descarga
   los pesos del modelo, 1–2 min adicionales tras arrancar).
7. Copia la **URL HTTP** del Pod (formato `https://<pod-id>-8000.proxy.runpod.net`).
   La verás en **Connect → HTTP 8000**.

Verifica:

```powershell
curl https://<pod-id>-8000.proxy.runpod.net/health
# {"status":"ok","device":"cuda","t3_model":"v3","language_id":"es"}
```

> ⚠️ **Importante:** apaga el Pod cuando no lo uses (`Stop Pod`) para no acumular
> costo por hora. El wrapper guarda las voces en memoria: al reiniciar el Pod se
> pierden las voces creadas. Para producción, persistir en un volumen/S3 (pendiente).

---

## 4. Alternativa — Hugging Face Spaces (Docker + GPU de pago)

1. Crea un Space: https://huggingface.co/new-space → *Docker* → *AutoTrain/Blank*.
2. Elige hardware GPU (ej. T4 small) — es de pago por hora.
3. Sube los 4 archivos de `apps/voice-clone` (`app.py`, `Dockerfile`,
   `requirements.txt`, `README.md`) al Space.
4. HF inyecta `PORT=7860`; el Dockerfile ya respeta `$PORT`.
5. La URL pública será `https://<usuario>-<space>.hf.space`. Úsala como
   `CLONACION_VOZ_URL` agregando el prefijo de API.

> ZeroGPU (gratis) solo funciona con Gradio SDK, no con Docker; sirve solo para
> probar el modelo en el demo oficial, no para este wrapper.

---

## 5. Conectar con AgroIA en Render

1. Abre **Render → agroia-backend → Environment**.
2. Agrega las variables:
   - `CLONACION_VOZ_URL` = `https://<pod-id>-8000.proxy.runpod.net`
   - `CLONACION_VOZ_TOKEN` = (vacío si no configuraste token)
3. Pulsa **Save Changes** (Render reinicia el servicio).

> Sin estas variables, "Mi voz" queda en modo muestra (la lectura usa la voz del
> navegador). Con `CLONACION_VOZ_URL` configurada, al grabar la voz se envía la
> muestra al motor y se habilita la síntesis con voz clonada.

---

## 6. Verificación de punta a punta

### 6.1 El motor responde

```powershell
# 1. Clonar una muestra (cualquier .wav/.webm pequeño; aquí generamos tono de prueba)
python -c "import base64,open; raw=open('muestra.webm','rb').read(); print(base64.b64encode(raw).decode())" > b64.txt
curl -X POST https://<pod-url>/clonar -H "Content-Type: application/json" -d "{\"usuario_email\":\"test@agroia.co\",\"audio_base64\":\"$(Get-Content b64.txt -Raw)\"}"
# → {"voice_id":"abc123","estado":"activa"}

# 2. Sintetizar con la voz clonada
curl -X POST https://<pod-url>/sintetizar -H "Content-Type: application/json" -d "{\"voice_id\":\"abc123\",\"texto\":\"Buenos días, su suelo está en buen estado\",\"velocidad\":\"1\"}" -o respuesta.wav
```

### 6.2 Desde AgroIA (producción)

1. Entra a la app y ve a **Configuración → Lectura → 🎙️ Mi voz**.
2. Marca el consentimiento, **Grabar** una frase (10–20 s), **Guardar voz**.
3. Debe aparecer **"Clonando su voz…"** y luego **"Voz clonada y lista"**.
4. Activa la lectura y pídele algo al Asesor agronómico; al pulsar 🔊 debe
   leer con tu voz clonada.

---

## 7. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `GET /health` no responde | Pod aún descargando pesos | Espera 1–3 min y reintenta |
| `/clonar` responde 500 | `ffmpeg` no convirtió la muestra | Revisa logs del Pod (`docker logs`) |
| "Clonando…" por siempre | El Pod se detuvo y la voz se perdió | Reinicia el Pod y vuelve a grabar |
| La lectura usa voz del navegador | `CLONACION_VOZ_URL` vacía o Pod apagado | Verifica la variable y enciende el Pod |
| Costo inesperado | Pod encendido sin uso | Detén el Pod tras las pruebas |
