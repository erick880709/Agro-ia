---
id: HU-06
type: Historia de Usuario
epic: 001-motor-recomendaciones
priority: Media
points: 3
---

# HU-06: Consultar historial de recomendaciones por finca

## Como
Agricultor

## Quiero
Ver el historial completo de análisis y recomendaciones de cada una de mis fincas

## Para
Hacer seguimiento a la evolución de la salud de mi suelo a lo largo del tiempo

## Criterios de Aceptación
- [ ] CA1: Lista cronológica de todas las recomendaciones generadas para una finca
- [ ] CA2: Gráfico de evolución de variables clave (pH, NPK, MO) con línea de tendencia
- [ ] CA3: Opción de exportar el historial completo en PDF
- [ ] CA4: Filtro por rango de fechas y por cultivo

## Subtareas
- [ ] Construir vista de historial con gráficos de evolución (Chart.js o similar)
- [ ] Implementar endpoint GET /api/v1/fincas/{id}/recomendaciones con filtros
- [ ] Integrar exportación PDF del historial
