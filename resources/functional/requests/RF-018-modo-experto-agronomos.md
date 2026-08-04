# RF-018: Modo Experto para Técnicos Agrónomos

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 5.13, 5.16
**Prioridad:** Media

## Descripción
La plataforma debe ofrecer dos modalidades de interacción diferenciadas por nivel de conocimiento del usuario:

**Modo agricultor (por defecto):**
- Lenguaje sencillo, sin tecnicismos.
- Explicaciones con analogías cotidianas.
- Recomendaciones accionables paso a paso.
- Visualizaciones intuitivas (semáforos, barras de progreso, iconos).

**Modo experto (activado por perfil de Técnico Agrónomo):**
- Lenguaje técnico con terminología agronómica precisa.
- Acceso a datos crudos de sensores, valores exactos y unidades de medida.
- Visualización de métricas de los modelos de IA (nivel de confianza, F1-score, RMSE).
- Capacidad de anotar y corregir recomendaciones (feedback loop para mejorar modelos).
- Comparativas avanzadas entre fincas, cultivos y períodos.
- Exportación de datos en formatos analíticos (CSV, JSON, Excel).

El sistema debe detectar el rol del usuario y adaptar automáticamente la interfaz y el lenguaje de las respuestas, permitiendo al experto alternar entre ambos modos si lo desea.

## Actores involucrados
- Técnico Agrónomo — usuario principal del modo experto
- Investigador IES — puede beneficiarse del acceso a datos crudos

## Criterios de aceptación
- La interfaz cambia visiblemente entre modo agricultor y modo experto.
- Las respuestas del agente IA usan vocabulario técnico en modo experto.
- El técnico puede ver los valores numéricos exactos de cada variable de sensor.
- El técnico puede anotar/revisar las recomendaciones generadas por la IA.
- No especificados en el RFP — definir: ¿el feedback del técnico se usa para reentrenar modelos automáticamente?, ¿permisos del técnico para modificar reglas agronómicas?

## Dependencias / relacionados
- RF-003: Roles y permisos
- RF-013: Recomendaciones inteligentes
- RF-014: Agente conversacional (RAG)
- RF-015: Dashboard de usuario

## Notas del analista
- El modo experto es clave para la adopción por parte de ingenieros agrónomos y para la validación científica del sistema durante el piloto con el Comité de Cafeteros del Quindío.
- La funcionalidad de feedback (anotar/corregir recomendaciones) es valiosa para el ciclo de mejora continua de los modelos (active learning / human-in-the-loop).
