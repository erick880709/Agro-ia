# RNF-002: Disponibilidad

**Tipo:** Requerimiento no funcional
**Categoría:** Disponibilidad
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 6.1

## Descripción
La plataforma debe tener una disponibilidad objetivo del 99.9% (three nines), lo que equivale a un tiempo de inactividad máximo de aproximadamente 8.76 horas al año (43.8 minutos al mes).

## Criterio medible / restricción concreta
- Disponibilidad ≥ 99.9% medida mensualmente.
- El tiempo de inactividad planificado (mantenimiento) debe notificarse con al menos 48 horas de anticipación.
- No especificados en el RFP — definir: ¿horario de ventana de mantenimiento?, ¿se excluye el mantenimiento planificado del cálculo de disponibilidad?

## Impacto en la arquitectura
- Requiere despliegue en múltiples zonas de disponibilidad (AZs) en AWS.
- Kubernetes con réplicas múltiples para eliminar puntos únicos de fallo (SPOF).
- Base de datos con replicación y failover automático.
- Estrategia de health checks y auto-healing para servicios.
- Plan de disaster recovery (RPO/RTO) — no definido en el RFP.

## Notas del analista
- 99.9% es un objetivo razonable para un MVP/sistema en fase piloto. Si la plataforma escala a producción comercial con miles de agricultores dependiendo de las alertas, puede ser necesario elevar a 99.95% o 99.99%.
- El RFP no define RPO (Recovery Point Objective) ni RTO (Recovery Time Objective). Se recomienda proponer: RPO < 1 hora, RTO < 4 horas para el MVP.
