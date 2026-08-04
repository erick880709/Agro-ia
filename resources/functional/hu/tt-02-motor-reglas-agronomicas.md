---
id: TT-02
type: Tarea Técnica
epic: 001-motor-recomendaciones
priority: Alta
points: 8
---

# TT-02: Implementar motor de reglas agronómicas (sistema experto)

## Descripción
Construir el Rules Engine que evalúa reglas UPRA, restricciones fenológicas, compatibilidad cultivo-suelo y umbrales de alerta. Debe ser determinístico, trazable y versionado.

## Criterios de Done
- [ ] Motor que carga reglas desde la tabla `reglas_agronomicas` al iniciar (con caché en Redis, TTL 5 min)
- [ ] Evalúa las 18 variables de entrada contra los umbrales definidos para el cultivo objetivo
- [ ] Retorna estructura `{status: "OK"|"FORBIDDEN"|"WARNING", violations: [...], warnings: [...]}`
- [ ] Las reglas se versionan; el motor siempre usa la última versión activa
- [ ] Soporte para reglas universales (aplican a todos los cultivos) y específicas por cultivo
- [ ] Tests unitarios con casos de reglas conocidas (ej. pH < 4.5 → corrección de encalado)
- [ ] Documentación de cada regla con su fuente (UPRA, Cenicafé, AGROSAVIA)

## Subtareas
- [ ] Cargar reglas UPRA oficiales para café (Quindío) como baseline inicial
- [ ] Implementar motor de evaluación con soporte para umbrales numéricos y categóricos
- [ ] Construir UI de administración de reglas (integrada en HU-05)
