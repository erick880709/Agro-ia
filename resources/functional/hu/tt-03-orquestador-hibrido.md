---
id: TT-03
type: Tarea Técnica
epic: 001-motor-recomendaciones
priority: Alta
points: 8
---

# TT-03: Implementar orquestador híbrido ML + Reglas

## Descripción
Construir el Recommendation Orchestrator que coordina el pipeline completo: recibe solicitud → consulta datos → invoca modelos ML → aplica reglas → detecta discordancia → ensambla respuesta final.

## Criterios de Done
- [ ] Endpoint `POST /api/v1/recommend` que recibe `{finca_id, cultivo_id (opcional)}`
- [ ] Pipeline secuencial: DataAdapters → ML Inference → Rules Engine → Discordance Check → Response Builder
- [ ] Principio de precaución: en caso de discordancia, la regla prevalece sobre el modelo ML
- [ ] Timeout máximo < 5s (p95); si ML excede 3s, se usa fallback solo reglas
- [ ] Trazabilidad completa con AWS X-Ray (segmentos por cada paso del pipeline)
- [ ] Registro de métricas en MLflow (latencia, confianza, estado)
- [ ] Tests de integración con mock de ML y reglas

## Dependencias
TT-01, TT-02, TT-04
