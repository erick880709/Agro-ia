---
id: TT-05
type: Tarea Técnica
epic: 001-motor-recomendaciones
priority: Alta
points: 5
---

# TT-05: Implementar sistema de discordancia y escalado

## Descripción
Construir el Discordance Resolver: detecta conflicto entre la predicción del modelo ML y la validación del motor de reglas → crea caso de revisión → notifica al técnico → aplica SLA de 10 días → bloquea si no hay respuesta.

## Criterios de Done
- [ ] Detección automática de discordancia al comparar salida ML vs salida Rules Engine
- [ ] Creación de caso DISC-XXXX en tabla `discordancias` con todos los datos del conflicto
- [ ] Notificación al técnico asignado (email + notificación interna en plataforma)
- [ ] Contador de SLA visible (días restantes de los 10 días hábiles)
- [ ] Job programado (Celery Beat / cron) que bloquea casos con SLA vencido
- [ ] Endpoint `GET /api/v1/discordancias` para cola de casos pendientes
- [ ] Endpoint `POST /api/v1/discordancias/{id}/resolver` para que el técnico resuelva

## Dependencias
TT-03
