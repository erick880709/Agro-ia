# RT-027: Selección y verificación de motores y licencias

**Tipo:** Requisito técnico
**Categoría:** Integración
**Fuente:** RFP-AGROIA-002 — Sección 9 y 15

## Descripción
Seleccionar los motores de voz verificando cuotas, licencias y precios vigentes. Decisión tomada: Fase 1 usa Web Speech API (`speechSynthesis`, por defecto), Google Cloud TTS o Azure AI Speech (nube, calidad/género), Amazon Polly y Piper/Kokoro como contingencia; para la voz personalizada (Fase 2) se usarán **GPT-SoVITS y Chatterbox** (ambos MIT, autoalojados). Se descartan **F5-TTS** (código MIT pero pesos CC-BY-NC-4.0, no comercial) y **XTTS-v2** (CPML, no comercial sin acuerdo). Qwen3-TTS queda como alternativa de respaldo (Apache 2.0).

## Criterio medible / restricción concreta
Informe de decisión técnica con comparación de motores, licencias y costos vigentes. Licencias comerciales MIT/Apache 2.0; descartados F5-TTS y XTTS-v2.

## Impacto en la arquitectura
Determina la cadena de respaldo (RT-021), el costo operativo (RNF-030) y la viabilidad de la voz personalizada (RT-028).

## Notas del analista
Las condiciones gratuitas cambian con frecuencia; el RFP exige verificación vigente antes de comprometerse. Los motores de clonación elegidos (GPT-SoVITS/Chatterbox) requieren prueba de concepto con acentos colombianos antes de producción.
