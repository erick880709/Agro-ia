# Evidencia de UI con Karate

El driver Karate permite automatizar UI y adjuntar `screenshot()`. Las plantillas
de esta skill son de API: no incluyen un grabador de video ni un trace de navegador
equivalente al de Playwright. El reporte HTML o un log HTTP no sustituyen esos archivos.

Antes de ejecutar UI, identifica el mecanismo real del proyecto para grabar el
navegador o la sesión de Grid y capturar su trace. Comprueba en un caso de prueba
que produce los tipos exigidos por la política, incluso cuando el caso pasa.
Conserva los archivos por caso, proyecto e intento y decláralos como `path` o `uri`.
Una referencia remota necesita verificación por el host. El validador no la descarga.

Si el proyecto carece de esa integración:

- Puedes diseñar o implementar la suite y declarar la preparación pendiente.
- Una ejecución con política browser predeterminada queda `partial` o `failed`
  por evidencia faltante. Describe qué tipos faltan y quién debe habilitarlos.
- Si el usuario elige Playwright para UI, transmite el encargo a esa skill.
  No migres automáticamente una suite Karate existente.
- Solo una excepción explícita del encargo permite reducir `evidencePolicy.required`.
  Registra su motivo en `override`. La ausencia de un grabador no es una excepción.

API conserva los resultados originales del runner bajo `resources/qa/`.
Para una suite híbrida separa resultados por nivel, conservando IDs y fuentes.
No declares UI verificada por haber ejecutado únicamente sus llamadas API.
