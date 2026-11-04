# RF-072: Capa de equivalencia sensor ↔ laboratorio

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E4)
**Prioridad:** No especificada

## Descripción
Las reglas se evalúan en la unidad del laboratorio (K en cmol(+)/kg; P por Bray II; N a partir de MO). La conversión usa la calibración vigente; sin calibración, la variable queda en grado C y no alimenta clasificaciones definitivas.

## Actores involucrados
Motor de reglas, orquestador

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RF-067; RF-071; RF-080 (grados de evidencia).

## Notas del analista
H-02: los umbrales Cenicafé/UPRA están en unidades de laboratorio; 1 cmol(+)/kg ≈ 391 mg/kg de K.
