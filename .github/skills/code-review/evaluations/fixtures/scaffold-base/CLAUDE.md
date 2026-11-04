# accounts-ms

Microservicio reactivo generado con el Scaffold Clean Architecture de Bancolombia.

- Validación: `./gradlew build` y `./gradlew validateStructure`.
- Los secretos se leen de variables de entorno inyectadas desde Secrets Manager; nunca en archivos.
- No registrar en logs números de documento ni de cuenta completos.
