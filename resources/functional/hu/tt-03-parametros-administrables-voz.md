---
id: TT-03
type: Tarea Técnica
epic: 010
priority: Media
points: 3
---

# TT-03: Mecanismo de parámetros administrables de voz

## Descripción
Implementar en el backend la configuración de la función de voz (duración máxima, activación, idioma) de forma administrable, sin valores fijos en código, alineada con la administración existente de AgroIA.

## Criterios de Done
- [ ] Parámetros de duración máxima, activación e idioma configurables sin cambiar código.
- [ ] Valores por defecto: duración 60 s, activado, idioma `es`.

## Recurso de datos involucrado

### Recurso
- **Nombre:** ParametroVoz
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| activado | booleano | Sí | Activa/desactiva la función de voz |
| duracion_maxima_segundos | entero | Sí | Límite máximo por consulta (60 s) |
| idioma | texto | Sí | Idioma de transcripción (`es`) |

### Relaciones con otros recursos
- Ninguna.

## Dependencias
- Ninguna (alinear con el mecanismo de parámetros existente)
