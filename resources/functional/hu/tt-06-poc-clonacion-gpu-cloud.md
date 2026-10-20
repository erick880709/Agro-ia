---
id: TT-06
type: Tarea Técnica
epic: 011
priority: Baja
points: 8
---

# TT-06: PoC e integración de motores de clonación en GPU cloud (Fase 2)

## Descripción
Probar GPT-SoVITS y Chatterbox (MIT) en GPU cloud (RunPod/HF Spaces) con acentos colombianos, y documentar el costo mensual; integrar la voz resultante a la cadena.

## Criterios de Done
- [x] Integración del motor a la cadena de síntesis (adaptador HTTP + endpoints + tests).
- [ ] PoC con resultados de inteligibilidad y parecido (requiere cuenta RunPod/HF Spaces).
- [x] Estimación de costo mensual de GPU y decisión de proveedor.

## Subtareas
- [ ] Despliegue de GPT-SoVITS/Chatterbox en GPU cloud (RunPod/HF Spaces).
- [ ] Prueba de concepto con audios de acento colombiano.
- [x] Estimación de costo mensual de GPU y documentación de la decisión.

## Entregables
- Documento: `resources/architecture/poc-clonacion-voz-tt06.md`
- Adaptador: `apps/backend/agroia_backend/services/clonacion_voz.py`
- Tests: `apps/backend/tests/test_clonacion_voz.py`

## Dependencias
- TT-01
- TT-02
