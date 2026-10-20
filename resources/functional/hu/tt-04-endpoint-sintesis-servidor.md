---
id: TT-04
type: Tarea Técnica
epic: 011
priority: Media
points: 5
---

# TT-04: Endpoint de síntesis en servidor

## Descripción
Endpoint autenticado que sintetiza texto en servidor con límites de tamaño, tasa de peticiones y streaming/fragmentos.

## Criterios de Done
- [ ] Endpoint con autenticación JWT y rate limiting.
- [ ] Salida por streaming o fragmentos.

## Recurso de datos involucrado

### Recurso
- **Nombre:** SintesisVoz (recurso transitorio petición/respuesta)
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| texto | texto | Sí | Texto normalizado a sintetizar |
| voz | texto | Sí | Voz objetivo |
| velocidad | texto | No | Velocidad de lectura |
| audio | binario | Sí | Respuesta de audio (no persistido) |

### Relaciones con otros recursos
- Ninguna persistida.

## Dependencias
- TT-01
