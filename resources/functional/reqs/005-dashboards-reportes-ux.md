---
id: 005
slug: dashboards-reportes-ux
ia_cierre: 9/100
rondas: 2
estado: lista-para-diseno
fecha: 2026-08-03
---

# NECESIDAD DE NEGOCIO REFINADA

Dashboard personalizado por finca (una a la vez) con indicador UPRA, mapa geoespacial, series temporales de sensores, KPIs, alertas priorizadas y acceso a reportes PDF — con carga <3s. Reportes PDF con plantilla fija única que incluyen estado del suelo, resumen ejecutivo, variables vs. umbrales, gráficas, recomendaciones, top 5 cultivos sugeridos y plan de acción — generación <10s. Dos modos de interfaz: agricultor (lenguaje coloquial, semáforos, guía paso a paso) y experto (datos crudos, métricas de modelos, exportación CSV/JSON/Excel, anotación de recomendaciones). Sin PWA/offline en MVP: datos se actualizan manualmente. Métrica de usabilidad: ≥80% de agricultores del piloto interpretan un reporte sin ayuda en ≤5 minutos, medido por el equipo de desarrollo en prueba presencial al mes 3 del piloto.

**Fuente(s) de origen**
- `RF-015-dashboard-usuario.md`, `RF-016-generacion-reportes-pdf.md`, `RF-018-modo-experto-agronomos.md`, `RNF-008-usabilidad-agricultor.md`, `RD-006-lineamientos-ux-modo-agricultor-experto.md`

**Actores**

| Rol | Tipo | Responsabilidad |
|-----|------|-----------------|
| Agricultor | Beneficiario | Visualiza dashboard de una finca a la vez; descarga reportes PDF |
| Técnico Agrónomo | Beneficiario avanzado | Modo experto: datos crudos, comparativas, exportación, anotación de recomendaciones |
| Equipo de desarrollo | Ejecutor | Mide usabilidad al mes 3 del piloto (prueba presencial) |

**Alcance**

- ✅ IN SCOPE (MVP):
  - Dashboard: una finca a la vez, indicador UPRA, mapa Leaflet, series temporales, KPIs, alertas, predicción climática, acceso a reportes. Carga <3s.
  - Reportes PDF: plantilla fija única, WeasyPrint (HTML/CSS), logo AgroIA, <10s generación, almacenamiento S3 + re-descarga
  - Modo agricultor: lenguaje coloquial, semáforos, guía paso a paso, sin tecnicismos
  - Modo experto: datos crudos, métricas de modelos, exportación CSV/JSON/Excel, anotación de recomendaciones
  - Usabilidad: 80% interpretan reporte en ≤5min, medido al mes 3 del piloto

- ❌ OUT OF SCOPE (MVP):
  - PWA/offline — datos se actualizan manualmente
  - Comparativa multi-finca en dashboard
  - Plantillas de reporte personalizables o marca blanca
  - WhatsApp integrado en MVP

**Criterios de Aceptación** (Gherkin — 4 escenarios: dashboard carga, reporte PDF, cambio de modo, prueba usabilidad)

**Métricas de Éxito**

| Métrica | Meta | Plazo |
|---------|------|-------|
| Carga dashboard | <3s (p95) | Producción |
| Generación PDF | <10s | Producción |
| Usabilidad | ≥80% interpretan reporte en ≤5min | Mes 3 del piloto |

**Prioridad (MoSCoW)**
- Must: Dashboard por finca, reportes PDF plantilla fija, modo agricultor, modo experto, indicador UPRA
- Should: Exportación CSV/JSON/Excel, anotación de recomendaciones, prueba usabilidad
- Could: Personalización dashboard, marca blanca
- Won't (MVP): PWA/offline, comparativa multi-finca, WhatsApp

**Brechas:** Prueba de usabilidad — confirmar disponibilidad de agricultores del piloto al mes 3

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 36/100
 Ronda 1:           16/100
 Ronda 2:            9/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

✅ **Lista para diseño/estimación**
