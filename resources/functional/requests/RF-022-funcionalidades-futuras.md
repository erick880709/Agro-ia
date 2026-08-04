# RF-022: Funcionalidades Futuras (Post-MVP)

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 10; Anexo-Datasets-Fuentes-Datos.md — Sección 7
**Prioridad:** Baja (Post-MVP)

## Descripción
La plataforma debe diseñarse con una arquitectura extensible que permita incorporar las siguientes funcionalidades en fases posteriores al MVP, sin requerir rediseños mayores:

1. **Predicción mediante imágenes de drones y fotografías del cultivo** — Análisis de salud del cultivo por imágenes aéreas o terrestres, usando visión artificial.

2. **Integración de sensores IoT en tiempo real a mayor escala** — Escalar de un piloto local (Quindío) a cobertura nacional con miles de sensores.

3. **Alertas automáticas de sequías e inundaciones** — Basadas en datos IDEAM + modelos predictivos climáticos.

4. **Detección de plagas mediante visión artificial** — Clasificación de imágenes de hojas para detección temprana de enfermedades (ej. roya del café). Usar transfer learning desde PlantVillage + datos propios capturados en campo.

5. **Optimización automática del riego** — Integración con sistemas de riego inteligente para automatizar la aplicación de agua según las necesidades del cultivo y las condiciones climáticas.

6. **Simulación de escenarios agrícolas** — "¿Qué pasaría si...?" — permitir al agricultor simular diferentes escenarios (cambio de cultivo, aplicación de fertilizante, variación climática).

7. **Recomendaciones financieras para el productor** — Análisis de rentabilidad, punto de equilibrio, retorno de inversión de las recomendaciones agronómicas.

8. **Integración completa con pasarela de pagos** — Cobro recurrente automatizado de membresías.

## Actores involucrados
- Por definir según la funcionalidad

## Criterios de aceptación
- La arquitectura actual (microservicios, IoT pipeline, modelos de IA) no debe requerir rediseño para incorporar estas funcionalidades.
- Cada nueva funcionalidad debe poder implementarse como un módulo o microservicio independiente.
- No especificados en el RFP — definir el orden de prioridad y roadmap de estas funcionalidades con el cliente.

## Dependencias / relacionados
- RT-001: Arquitectura cloud-native basada en microservicios
- RT-009: Arquitectura IoT — LoRaWAN
- RF-007: Captura de sensores IoT
- RF-012: Motor predictivo

## Notas del analista
- Estas funcionalidades están fuera del alcance del MVP pero deben considerarse en las decisiones de arquitectura desde el inicio para evitar bloqueos futuros.
- La detección de plagas por visión artificial (roya del café) es particularmente relevante para el piloto del Quindío, ya que la roya (Hemileia vastatrix) es uno de los tres factores de mayor correlación con pérdidas productivas en el Eje Cafetero.
- No existe un dataset público robusto específico para roya del café en contexto colombiano; se recomienda planear una campaña de captura de imágenes durante el piloto de campo.
