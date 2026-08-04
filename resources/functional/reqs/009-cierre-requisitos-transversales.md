---
id: 009
slug: cierre-requisitos-transversales
ia_cierre: 10/100
rondas: 0
estado: lista-para-diseno
fecha: 2026-08-03
---

# NECESIDAD DE NEGOCIO REFINADA — CIERRE

Consolidación de requisitos transversales ya cubiertos en refinamientos anteriores y funcionalidades post-MVP. No requiere refinamiento adicional.

**Requisitos ya cubiertos implícitamente**

| ID | Tema | Cubierto en refinamiento # |
|----|------|---------------------------|
| RF-001 | Portal web responsive (Angular 21, Chrome/Safari/Edge/Firefox) | #5 |
| RF-006 | Gestión de fincas (CRUD: nombre, depto, municipio, área, GPS, foto) | #5 |
| RF-011 | Variables adicionales (históricas, económicas, NDVI) | #3 |
| RF-017 | Administración de la plataforma | #5 |
| RF-019 | Visualización geoespacial (Leaflet + PostGIS) | #5 |
| RF-020 | Notificaciones WhatsApp/SMS | #3 (post-MVP) |
| RF-021 | Pasarela de pagos | #8 (post-MVP) |
| RNF-001 | Tiempo de respuesta <3s consultas, <10s chat IA | #1, #5, #6 |
| RNF-002 | Disponibilidad 99.9% | #7 |
| RNF-010 | Actualización RAG sin reentrenar | #6 |
| RT-002 | Frontend Angular 21 | #1 (vinculante desde inicio) |
| RT-003 | Backend Python FastAPI | #1 (vinculante desde inicio) |
| RT-004 | Modelos IA Python (scikit-learn, XGBoost, TensorFlow/PyTorch) | #1 |
| RD-001 | Diagrama contexto C4 | Artefacto de arquitectura |
| RD-002 | Arquitectura en capas | Artefacto de arquitectura |
| RD-004 | Estrategia cold-start 3 fases | #1 |
| RD-005 | Mapa fuentes datos → modelos | #1 |

**Funcionalidades post-MVP (RF-022)**

| Funcionalidad | Prioridad | Depende de |
|-------------|----------|-----------|
| Predicción por imágenes de drones | Could | Datos del piloto |
| Sensores IoT a escala nacional | Should | Éxito del piloto Quindío |
| Alertas automáticas sequías/inundaciones | Should | IDEAM + modelos LSTM |
| Detección plagas por visión artificial | Could | Datos propios de imágenes |
| Optimización automática de riego | Could | Integración con sistemas de riego |
| Simulación de escenarios | Could | Todos los modelos maduros |
| Recomendaciones financieras | Could | DANE-SIPSA + EVA integrados |
| Pasarela de pagos completa | Should | Modelo de negocio validado |

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 15/100 → ya cubierto
 Ronda 1:           10/100  ← CIERRE (sin rondas)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

✅ **Lista para diseño/estimación**
