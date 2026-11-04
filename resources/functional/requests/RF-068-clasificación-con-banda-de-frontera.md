# RF-068: Clasificación con banda de frontera

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E3)
**Prioridad:** No especificada

## Descripción
Si |valor − umbral| ≤ exactitud, la clase se informa como 'indeterminada (frontera)', con la probabilidad estimada de cada clase. El motor de reglas y el orquestador consumen esa salida; la confianza (incluido el umbral duro de 80 %) incorpora la incertidumbre medida.

## Actores involucrados
Motor de reglas (rules_engine), orquestador

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RF-067; RF-081 (reglas por grado).

## Notas del analista
H-01: hoy las reglas son deterministas y clasifican valores inciertos como exactos.
