# RT-034: Campaña de calibración en campo y metas por variable

**Tipo:** Requisito técnico
**Categoría:** Integración / Stack tecnológico
**Fuente:** RFP-AGROIA-003 §3 y §9 (Anexo A)

## Descripción
Al menos 30 pares sensor–laboratorio por unidad de suelo y variable, cubriendo el rango de valores, con laboratorio acreditado y métodos declarados. Metas iniciales a validar: pH sesgo ≤ 0,3 y RMSE ≤ 0,4 (vs pH en agua 1:1); humedad RMSE ≤ 5 puntos VWC (vs gravimétrico × densidad aparente); CE R² ≥ 0,8 (vs CE 1:5 o CEe); N/P/K R² ≥ 0,6 en el rango del suelo (si no, solo tendencia).

## Criterio medible / restricción concreta
Según lo especificado en la descripción; los valores son parametrizables y ajustables con el equipo agronómico.

## Impacto en la arquitectura
Condiciona el cierre de la fase 3 y el paso de variables de grado C a B.

## Notas del analista
Si una variable no cumple su meta, permanece en grado C (indicativa).
