# Evidencia QA compartida

La [política QA](../../../contracts/output/validators/qa/qa-policy.json) y las [reglas del resultado](qa-output.md) se aplican a todos los runners. La política vive en el paquete de contratos; Ranger conserva trazabilidad y evaluación; cada especialista mantiene la configuración y captura de su herramienta.

## Política de evidencia

Para navegador conserva video, trace y screenshot por caso/proyecto/intento, incluidos los exitosos. Para API y unitarias conserva los resultados reales del runner (`raw_results`). Reducir los tipos predeterminados requiere una instrucción explícita registrada en `data.evidencePolicy.override` con su motivo. Un reporter instalado no acredita que los archivos existan.

Si la infraestructura no produce un tipo requerido, registra el faltante y entrega incompleta o aplica la excepción explícita del encargo. Los formatos de trace dependen del runner; una traza Selenium no es un archivo Playwright.

## Convención de Id de Caso

Conserva ID y prioridad del runbook en el título, tags o anotaciones que exporta el reporter. Verifica su presencia en el CTRF y el vínculo de cada adjunto con el caso, proyecto e intento. Un caso sin trazabilidad no permite acreditar el alcance previsto.

## Organización y reporte

Guarda evidencia real bajo `resources/qa/test-results/<runId>/` (Playwright la organiza en `resources/qa/<CASE-ID>/<runId>/<proyecto>/attempt-<n>/`) y reportes bajo `resources/qa/reports/<runId>/`. Usa un runId nuevo para cada ejecución y conserva los reintentos. La carpeta contractual contiene únicamente resultados JSON de invocaciones, no archivos binarios del runner.

Conserva el reporte nativo y usa un reporter CTRF compatible o una conversión. Declara el CTRF como `test_results` con su ruta local. Enlaza adjuntos externos con [attach-evidence.mjs](../scripts/attach-evidence.mjs); no genera evidencia. Genera el reporte mediante [generate-execution-report.mjs](../../../contracts/output/generate-execution-report.mjs), pasando el alcance y criterios acordados; el contrato y el reporte usan el mismo evaluador.

## Almacenamiento y Retención

Conserva reportes y evidencia aunque fallen pruebas. Versiona planes, runbooks y código; almacena binarios en el sistema de artefactos del proyecto, con acceso y retención acordados. No borres intentos fallidos ni reutilices carpetas de otra corrida. Comprueba que las rutas del reporte se puedan abrir después de publicar los artefactos.

## Captura por herramienta

- [Playwright: video, pacing, trace, captura y diagnóstico](../../qa-ranger-playwright/references/13-evidencia-video.md).
- [Selenium: reportes, captura de infraestructura y adjuntos](../../qa-ranger-selenium/resources/14-reportes-y-evidencia.md).
- [Robot Framework: evidencia por caso/intento, output.xml y conversión CTRF](../../qa-ranger-robotframework/resources/12-reportes-evidencia-y-ctrf.md).
- [Unitarias: runners y reportes nativos](../../qa-ranger-unitarias/references/01-runners-y-cobertura.md).
- [Karate](../../qa-ranger-karate/SKILL.md) y [JMeter](../../qa-ranger-jmeter/SKILL.md): resultados de su runner y contrato.
- [Cypress](tools/cypress_patterns.md), [WebdriverIO](tools/webdriverio_patterns.md) y [Appium](tools/appium_mobile_patterns.md): guías de los stacks que no tienen especialista dedicado.
