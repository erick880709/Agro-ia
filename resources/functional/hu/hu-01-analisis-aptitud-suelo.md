---
id: HU-01
type: Historia de Usuario
epic: 001-motor-recomendaciones
priority: Alta
points: 8
---

# HU-01: Solicitar análisis de aptitud del suelo para una finca

## Como
Agricultor

## Quiero
Solicitar un análisis de aptitud del suelo para un cultivo en mi finca registrada

## Para
Saber si mi suelo es adecuado para el cultivo y recibir recomendaciones correctivas accionables

## Criterios de Aceptación
- [ ] CA1: El agricultor selecciona una finca registrada y un cultivo objetivo → ve la clasificación UPRA (Alta/Media/Baja/No apta)
- [ ] CA2: Para cada variable de suelo fuera del rango ideal, se muestra una recomendación correctiva específica con justificación
- [ ] CA3: Si F1-score < 0.80, la recomendación muestra advertencia "baja confianza" y se escala al técnico
- [ ] CA4: Si faltan variables bloqueantes (pH, N, P, K), el sistema responde "Datos insuficientes" listando las variables faltantes
- [ ] CA5: Tiempo de respuesta < 3 segundos (p95)

## Recurso de datos involucrado
### Recurso
- **Nombre:** Recomendacion
- **Capa(s):** backend / frontend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| id | UUID | Sí | Identificador único |
| finca_id | UUID | Sí | FK a Finca |
| cultivo_id | UUID | Sí | FK a Cultivo |
| clasificacion_upra | Enum(Alta/Media/Baja/NoApta) | Sí | Clasificación según estándar UPRA |
| confianza | Float (0-1) | Sí | F1-score de la predicción |
| justificacion | JSONB | Sí | Variables que influyeron, riesgos, beneficios, costo, impacto |
| estado | Enum(Publicada/Advertencia/Bloqueada) | Sí | Según F1-score y revisión del técnico |
| tecnico_id | UUID | No | FK a Usuario (rol Técnico) si fue escalada |
| created_at | Timestamp | Sí | Fecha de generación |
| tenant_id | UUID | Sí | Aislamiento RLS |

### Relaciones con otros recursos
- `Finca` (N:1): una recomendación pertenece a una finca
- `Cultivo` (N:1): una recomendación referencia un cultivo
- `Usuario` (N:1): técnico que revisó (opcional)

## Subtareas
- [ ] Diseñar endpoint POST /api/v1/recommend
- [ ] Implementar validación de variables bloqueantes vs no bloqueantes
- [ ] Construir componente Angular de resultado de análisis con clasificación UPRA
