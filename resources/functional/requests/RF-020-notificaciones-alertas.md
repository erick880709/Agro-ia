# RF-020: Notificaciones y Alertas (WhatsApp/SMS)

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 4, 5.14
**Prioridad:** Media

## Descripción
La plataforma debe enviar notificaciones y alertas a los agricultores a través de canales de comunicación accesibles en zonas rurales colombianas, principalmente WhatsApp y SMS. Tipos de notificaciones:

**Alertas agronómicas:**
- Condiciones críticas detectadas en el suelo (deficiencia severa, pH fuera de rango crítico).
- Riesgo de enfermedad o plaga según condiciones climáticas.
- Recordatorios de fertilización, riego o medición programada.

**Alertas climáticas:**
- Pronóstico de lluvias intensas, sequía o heladas que afecten el cultivo.
- Condiciones óptimas para siembra o cosecha.

**Notificaciones del sistema:**
- Reporte de análisis completado y disponible.
- Vencimiento de membresía.
- Sensor offline o con batería baja.

## Actores involucrados
- Cliente (Agricultor) — recibe notificaciones
- Sistema — envía notificaciones automáticas según reglas configuradas

## Criterios de aceptación
- El agricultor puede configurar qué tipos de notificaciones desea recibir y por qué canal.
- Las notificaciones se envían en español, en lenguaje sencillo.
- El sistema registra el historial de notificaciones enviadas.
- No especificados en el RFP — definir: ¿plantillas de mensajes predefinidas o generadas por IA?, ¿frecuencia máxima de notificaciones para no saturar al agricultor?, ¿proveedor de WhatsApp Business API (Meta) o Twilio para SMS?

## Dependencias / relacionados
- RF-008: Integración con APIs externas (WhatsApp/SMS)
- RF-013: Recomendaciones inteligentes (dispara alertas)
- RF-012: Motor predictivo (Modelo 6: predicción de enfermedades)

## Notas del analista
- WhatsApp es el canal de comunicación dominante en Colombia, incluso en zonas rurales. Se recomienda priorizar la integración con WhatsApp Business API sobre SMS.
- La API de WhatsApp Business requiere un número de teléfono verificado y aprobación de Meta. Twilio ofrece una capa de abstracción que unifica WhatsApp y SMS.
- Para el MVP, puede implementarse un sistema de notificaciones por correo electrónico + WhatsApp, dejando SMS para una fase posterior.
