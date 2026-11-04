# RF-071: Modelo de calibración

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E4)
**Prioridad:** No especificada

## Descripción
Sustituir el factor único de calibración por regresión lineal (pendiente e intercepto) por dispositivo, variable y unidad de suelo, con n, R², RMSE, sesgo, vigencia y responsable. Se mantiene el historial de calibraciones.

## Actores involucrados
Administrador, agrónomo

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RD-011 (`calibracion_sensor`, `par_calibracion`); RF-073 (campaña).

## Notas del analista
H-02: un factor multiplicativo único no captura sesgo ni no linealidad.
