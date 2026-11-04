# Confiabilidad y mantenimiento de QA

Ranger coordina la salud de las suites y el cierre con evidencia. Los ejemplos de implementación y depuración viven en cada especialista:

- [Jest, RTL y MSW](../../qa-ranger-unitarias/references/05-buenas-practicas-javascript.md): testeabilidad, AAA, aislamiento, mocks y mantenimiento.
- [Playwright](../../qa-ranger-playwright/references/08-flakiness-y-debug.md): sincronización, traces y diagnóstico.
- [Selenium](../../qa-ranger-selenium/resources/07-flakiness-y-debug.md): esperas, sesiones y diagnóstico.

## Revisión y mantenimiento

Comprueba que cada caso verifica un comportamiento y mantiene su vínculo con los requisitos. Comparte fixtures y helpers cuando reduzcan duplicación sin introducir estado mutable entre casos. Actualiza las pruebas junto con los cambios del producto; elimina un caso solo con una justificación de alcance, nunca para ocultar un fallo.

## Estrategia de Cuarentena

1. Identifica las variaciones por caso/proyecto en corridas independientes, conservando reportes, reintentos, entorno y runIds.
2. Registra responsable, motivo, impacto y condición de retorno antes de separar temporalmente un caso.
3. Ejecuta el conjunto separado y corrige la causa con el especialista correspondiente.
4. Restáuralo cuando la evidencia muestre estabilidad.

La cuarentena no acredita aprobación: conserva el caso en el alcance previsto y refleja su omisión o bloqueo en el reporte. Un retry exitoso no borra el intento fallido. El kit no incluye un analizador de tendencias; usa el del proyecto y declara período y denominador.

## Métricas de calidad e indicadores

Deriva estados, conteos y veredicto desde el CTRF con el evaluador común. Para cobertura unitaria usa el reporte nativo y la [política QA](../../../contracts/output/validators/qa/qa-policy.json): 95% por métrica soportada salvo una meta explícita documentada en `targetOverride`. No fijes metas distintas por madurez del proyecto ni un mínimo arbitrario de cantidad de tests.

Observa duración, reintentos, defectos y cambios de cobertura para priorizar mejoras. Compara el mismo alcance y entorno, e identifica la fuente de cada métrica. Las tendencias no sustituyen los criterios de salida acordados ni permiten presentar una suite vacía como aprobada.

## Gates de CI

Genera y conserva reportes y [evidencia](evidence_guide.md) aunque falle el runner. Aplica los criterios acordados al veredicto agregado. La configuración del pipeline se mantiene en el especialista; para Playwright consulta [CI y reportes](../../qa-ranger-playwright/references/09-ci-cd-y-reportes.md).
