---
id: TT-02
type: Tarea Técnica
epic: 010
priority: Alta
points: 8
---

# TT-02: Endpoint de transcripción en servidor (respaldo)

## Descripción
Crear el endpoint que recibe audio y devuelve texto en español, usado como respaldo cuando Web Speech API no está disponible o falla. Debe exigir autenticación JWT, limitar tamaño y duración, aplicar rate limiting, transmitir por HTTPS y descartar el audio al terminar.

## Criterios de Done
- [ ] Endpoint con autenticación JWT y rate limiting.
- [ ] Validación de tamaño y duración máximos del audio.
- [ ] Descarte del audio al completar la transcripción (sin persistencia).
- [ ] Pruebas de contrato y de descarte de audio.

## Recurso de datos involucrado

### Recurso
- **Nombre:** TranscripcionVoz (recurso de solicitud/respuesta, transitorio)
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| audio | binario | Sí | Audio cifrado en tránsito (HTTPS); no persistido |
| idioma | texto | Sí | `es` (español) |
| texto | texto | Sí | Respuesta con la transcripción |

### Relaciones con otros recursos
- Ninguna persistida.

## Subtareas
- [ ] Definir el contrato del endpoint (petición audio → respuesta texto).
- [ ] Implementar autenticación JWT y rate limiting.
- [ ] Implementar validación de tamaño y duración máximos del audio.
- [ ] Implementar ciclo de vida transitorio del audio (procesar y descartar, sin persistencia).

## Dependencias
- TT-01
