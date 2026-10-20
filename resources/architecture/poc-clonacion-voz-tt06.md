# PoC de clonación de voz en GPU cloud — TT-06 (Epic 011)

**Fecha:** 2026-10-19
**Estado:** Integración lista (adaptador + endpoints + tests). PoC de audio real **pendiente de ejecución** con cuenta de RunPod/HF Spaces.
**Dependencias cubiertas:** TT-01 (interfaz común de síntesis), TT-02 (cadena de respaldo).

---

## 1. Objetivo

Probar los motores de clonación **GPT-SoVITS** y **Chatterbox** (ambos MIT) para generar la
voz personalizada del usuario ("Mi voz") y decidir el proveedor de GPU con su costo mensual.

## 2. Comparación de motores

| Criterio | Chatterbox Multilingual V3 | GPT-SoVITS |
|---|---|---|
| Licencia | MIT (código y modelo) | MIT |
| Idiomas | Multilingüe (incluye español, base V2 23+ idiomas) | EN / JA / KO / CN oficialmente; español solo vía fine-tuning |
| Muestra requerida | Zero-shot (varios segundos) | Zero-shot 5 s; few-shot 1 min |
| Tamaño / VRAM | 0.5B; corre en ~4–8 GB VRAM; existe **Nano (110M)** que corre en CPU | ~1B; requiere ~8–16 GB VRAM; entrenamiento fino más pesado |
| Latencia | Baja; hay Turbo (350M, solo EN) y Nano | RTF 0.014–0.028 en 4090/4060Ti (rápido en GPU) |
| Parecido de voz | Alto, estable entre idiomas | Muy alto con fine-tuning (few-shot) |
| Madurez / operación | Modelo único, API simple | WebUI pesada; mejor para entrenamiento supervisado |

**Hallazgo clave:** GPT-SoVITS **no lista español** entre sus idiomas oficiales de inferencia
zero-shot, lo que obligaría a fine-tuning para el acento colombiano. Chatterbox Multilingual V3
sí soporta español de forma nativa y preserva el acento, con un solo modelo y menos VRAM.
Además, Chatterbox ofrece un **Single Language Pack de Latam Spanish**
(`ResembleAI/Chatterbox-Multilingual-es-mx-latam`), el más adecuado para el acento colombiano.

**Decisión de motor:** **Chatterbox Multilingual V3** como motor principal de clonación
(`language_id="es"`, con el pack Latam Spanish como opción regional);
**GPT-SoVITS** queda como alternativa para casos que exijan parecido máximo con fine-tuning.

## 3. Proveedor de GPU y costo

Precios verificados en [RunPod](https://www.runpod.io/pricing) (actualizados 8-oct-2026):

| Opción | GPU | Precio | Uso recomendado |
|---|---|---|---|
| RunPod Serverless 16 GB | A4000/A4500/RTX 4000 | **$0.58/h** | Nano/CPU o inferencia pequeña |
| RunPod Serverless 24 GB | L4/A5000/3090/MIG 24 GB | $0.69/h | Chatterbox V3 (0.5B) |
| RunPod Pod 24 GB | RTX 3090 | $0.50/h | Entrenamiento/ajuste dedicado |
| RunPod Pod 24 GB | RTX A5000 | **$0.27/h** | Opción más económica por hora |

Hugging Face Spaces dedicados (precios por GPU dinámicos; verificar en consola):
T4 small ≈ $0.40/h, L4 small ≈ $0.80/h, A10G small ≈ $1.05/h; ZeroGPU (compartido) es **gratuito**
y suficiente para el PoC.

### Estimación de costo mensual

| Escenario | Cómputo | Costo mensual estimado |
|---|---|---|
| PoC (2–4 h de prueba + muestras) | Serverless 16–24 GB | **< USD 3** |
| Producción baja (≈ 500 lecturas/mes, ~10 s de audio c/u) | Serverless, facturado por segundo | **≈ USD 2–8** |
| Producción media (≈ 5.000 lecturas/mes) | Serverless 24 GB | **≈ USD 20–50** |
| Concurrencia alta / siempre encendido | Pod RTX 3090/A5000 | USD 200–360 |

> La facturación serverless es por segundo de uso real, no por tiempo encendido, por lo que el
> costo escala con el volumen real de lecturas. Cumple el objetivo del RFP de costo mensual bajo
> (USD 0/mes en Fase 1, solo se paga lo que se usa en Fase 2).

**Decisión de proveedor:** **RunPod Serverless** (GPU L4/3090, $0.69/h) para producción;
**Hugging Face Spaces ZeroGPU** para el PoC sin costo. Ambos aceptan contenedor Docker con el
wrapper HTTP descrito en la sección 5.

## 4. Protocolo de prueba del PoC (inteligibilidad y parecido)

1. Grabar **10 muestras** de voces con acento colombiano (variedad costeña, paisa, cundiboyacense,
   llanera, pastusa) — 10–30 s por muestra, con texto agronómico real (pH, abonos, riego).
2. Sintetizar un set fijo de 20 frases agronómicas con cada motor.
3. Evaluar con 3 jueces:
   - **Inteligibilidad:** escala MOS 1–5 (claridad de palabras y unidades: "pe hache", "kilos por hectárea").
   - **Parecido (SIM):** 1–5 (cuánto se parece a la voz de referencia).
   - **Acento:** ¿preserva el acento colombiano? (sí/no/parcial).
4. Criterio de aprobación: **MOS ≥ 4.0** y **SIM ≥ 3.5** en ≥ 80 % de las muestras.

## 5. Contrato HTTP del wrapper GPU (ya implementado en el backend)

El adaptador [`clonacion_voz.py`](/c:/Users/ELITEBOOK/OneDrive/Documentos/Repositorio/Trabajo/Agro-ia/apps/backend/agroia_backend/services/clonacion_voz.py)
espera un servicio autoalojado que exponga:

```
POST {base}/clonar        {"usuario_email", "audio_base64"}  → {"voice_id", "estado"}
GET  {base}/voces/{id}    → {"voice_id", "estado"}            (procesando | activa | error)
POST {base}/sintetizar    {"voice_id", "texto", "velocidad"}  → audio (body)
```

El wrapper (un `FastAPI`/`sanic` de ~100 líneas que carga Chatterbox V3 y traduce este contrato)
se despliega como Docker en RunPod/HF Spaces. Ya está implementado en
[`apps/voice-clone`](/c:/Users/ELITEBOOK/OneDrive/Documentos/Repositorio/Trabajo/Agro-ia/apps/voice-clone)
(`app.py` + `Dockerfile` + `requirements.txt` + `README.md`). El backend de AgroIA no necesita
cambios adicionales: solo configurar `CLONACION_VOZ_URL` y `CLONACION_VOZ_TOKEN`.

## 6. Integración ya realizada

- Config: `CLONACION_VOZ_URL` y `CLONACION_VOZ_TOKEN` en [`config.py`](/c:/Users/ELITEBOOK/OneDrive/Documentos/Repositorio/Trabajo/Agro-ia/apps/shared/agroia/config.py).
- Adaptador HTTP: [`clonacion_voz.py`](/c:/Users/ELITEBOOK/OneDrive/Documentos/Repositorio/Trabajo/Agro-ia/apps/backend/agroia_backend/services/clonacion_voz.py).
- Cadena de síntesis: `VozClonadaProvider` en [`sintesis_voz.py`](/c:/Users/ELITEBOOK/OneDrive/Documentos/Repositorio/Trabajo/Agro-ia/apps/backend/agroia_backend/services/sintesis_voz.py).
- Endpoints: `POST /lectura/voz-personalizada` ahora envía la muestra al motor si está configurado
  (`estado="procesando"`); nuevos `POST /lectura/voz-personalizada/clonar` y
  `GET /lectura/voz-personalizada/estado` en [`lectura.py`](/c:/Users/ELITEBOOK/OneDrive/Documentos/Repositorio/Trabajo/Agro-ia/apps/backend/agroia_backend/api/lectura.py).
- Frontend: al guardar, si `estado="procesando"` muestra "Clonando su voz…" y consulta el estado
  hasta que quede `activa` ([`lectura.js`](/c:/Users/ELITEBOOK/OneDrive/Documentos/Repositorio/Trabajo/Agro-ia/apps/frontend-web/lectura.js)).
- Tests: [`test_clonacion_voz.py`](/c:/Users/ELITEBOOK/OneDrive/Documentos/Repositorio/Trabajo/Agro-ia/apps/backend/tests/test_clonacion_voz.py) (5 pruebas, contrato + cadena, con transporte HTTP simulado).

## 7. Pendiente (requiere cuenta y créditos)

- [ ] Ejecutar el PoC de audio real en HF Spaces ZeroGPU o RunPod con las muestras colombianas.
- [ ] Publicar el wrapper Docker de Chatterbox V3 con el contrato de la sección 5.
- [ ] Cargar `CLONACION_VOZ_URL`/`CLONACION_VOZ_TOKEN` en Render (producción).
- [ ] Registrar resultados MOS/SIM en este documento y cerrar TT-06.
