# RF-062: Estados de calidad ampliados

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E2)
**Prioridad:** No especificada

## Descripción
El motor de calidad clasifica cada lectura en: `valida`, `valida_con_advertencia`, `bajo_limite_deteccion`, `saturada`, `fuera_de_rango`, `sonda_fuera_de_suelo`, `humedad_insuficiente`, `no_calibrada`, `estimado_sig` e `invalidada`. Cada lectura guarda la lista de motivos y la versión de la regla aplicada.

## Actores involucrados
Motor de calidad, consumidor IoT

## Criterios de aceptación
Cero lecturas `invalidada`, `saturada` o `humedad_insuficiente` en reportes (§9).

## Dependencias / relacionados
RF-063, RF-064, RF-065, RF-066; RD-011 (enum `calidad` ampliado).

## Notas del analista
Sustituye la regla binaria actual 'válida/inválida' por una clasificación fina.
