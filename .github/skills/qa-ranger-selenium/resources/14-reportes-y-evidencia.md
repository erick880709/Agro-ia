# Reportes y evidencia de Selenium

Allure presenta resultados y adjuntos; la [política QA compartida](../../../contracts/output/validators/qa/qa-policy.json) define la evidencia requerida. Cada caso/proyecto/intento necesita video, traza diagnóstica y screenshot, incluidos los exitosos. Conserva la asociación con el test y la sesión WebDriver bajo `resources/qa/`.

Una traza Selenium no es un `trace.zip` de Playwright. Conserva JUnit/Allure como reporte nativo y usa un reporter CTRF del runner o una conversión compatible. Declara el CTRF como artefacto `test_results`; el [lector común](../../../contracts/output/validators/qa/ctrf.mjs) lee CTRF de cualquier runner. No entregues XML JUnit o archivos Allure directamente a ese lector.

En el resultado declara `data.task`, `data.expected`, `data.exitCriteria` y `data.evidencePolicy`, según las [reglas del contrato](../../ranger/references/qa-output.md). El motor compartido genera métricas y reporte desde los archivos reales. Para enlazar adjuntos externos usa [attach-evidence.mjs](../../ranger/scripts/attach-evidence.mjs); no captura archivos ni acredita evidencia inexistente.

Si falta captura, registra el pendiente y entrega incompleta, o aplica la excepción explícita recibida del encargo. El contrato no instala un grabador ni sustituye la infraestructura Selenium.

Consulta [CI y reportes](08-ci-cd-y-reportes.md) para publicación y [Grid](06-grid-paralelismo-nube.md) para sesiones y paralelismo.
