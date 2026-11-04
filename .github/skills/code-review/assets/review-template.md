---
review:
  id: CR-NNN            # o el ID del cambio de Builder
  change: <id-o-slug-del-cambio>
  revision: <sha | "sin-commit + sha256 de archivos">
  base: <rama o sha base>
  rigor: <ligero | estandar | reforzado>
  independencia: <independiente | misma-sesion>
  ronda: 1
  veredicto: <aprobado | aprobado-con-observaciones | cambios-requeridos | no-concluyente>
  conteo: {bloqueante: 0, mayor: 0, menor: 0, nit: 0, pregunta: 0, preexistente: 0}
  hallazgos:
    - {id: B-01, severidad: bloqueante, confianza: alta, archivo: "ruta/Archivo.java:42", estado: pendiente}
---

# Revisión de código — <cambio>

**Veredicto:** <una línea accionable>

## Resumen

<2–3 frases: qué cambió y la lectura del revisor.>

## Gate computacional

| Check | Comando | Resultado | Nota |
|---|---|---|---|
| Build + tests | `./gradlew build` | passed / failed / not_run | |
| Estructura | `./gradlew validateStructure` | | |
| ArchUnit | `ArchitectureTest` | | |

## Cumplimiento de la spec

Fuente: `<docs/changes/<id>/spec.md | issue | intención reconstruida>`

| Criterio | Estado | Evidencia |
|---|---|---|
| AC-01 | ✅ / ⚠️ / ❌ / — | `Test#caso` o razón |

## Estado rápido

| ID | Severidad | Dónde | Estado |
|---|---|---|---|
| B-01 | bloqueante | `ruta/Archivo.java:42` | pendiente |

## Bloqueantes

### B-01 · <título>

- **Dónde:** `ruta:línea`
- **Severidad / confianza:** bloqueante / alta
- **Por qué:** <escenario e impacto>
- **Evidencia:** <qué verificaste o ejecutaste>
- **Arreglo:** <acción concreta + test que lo protege>
- **Decisión:**
  - [ ] aceptar
  - [ ] rechazar
  - [ ] diferir
  - [ ] necesita más información
- **Nota del autor:**

---

## Mayores

## Menores

## Nits

## Preguntas

## Preexistentes

## Fuera de alcance
