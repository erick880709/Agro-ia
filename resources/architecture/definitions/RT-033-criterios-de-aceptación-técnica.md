# RT-033: Criterios de aceptación técnica

**Tipo:** Requisito técnico
**Categoría:** Integración / Stack tecnológico
**Fuente:** RFP-AGROIA-003 §3 y §9 (Anexo A)

## Descripción
100 % de los vectores de prueba decodificados correctamente (incluida temperatura negativa); cero lecturas `invalidada`, `saturada` o `humedad_insuficiente` en reportes; todo reporte con grado de evidencia y variables no medidas declaradas; reclasificación histórica sin pérdida de registros.

## Criterio medible / restricción concreta
Según lo especificado en la descripción; los valores son parametrizables y ajustables con el equipo agronómico.

## Impacto en la arquitectura
Define los gates de aceptación de las fases 1–5.

## Notas del analista
Verificable de forma automatizada en el pipeline de CI.
