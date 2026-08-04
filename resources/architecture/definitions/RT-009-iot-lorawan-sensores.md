# RT-009: Arquitectura IoT — Protocolo LoRaWAN y Sensores

**Tipo:** Requisito técnico
**Categoría:** Infraestructura / IoT
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 7.4

## Descripción
La plataforma debe integrarse con una red de sensores IoT de campo para la captura de variables de suelo. La arquitectura IoT de referencia incluye:

- **Protocolo de comunicación:** LoRaWAN, adecuado para zonas rurales con conectividad limitada (largo alcance, bajo consumo energético).
- **Frecuencia de transmisión:** configurable, con referencia de cada 15–30 minutos.
- **Autonomía energética:** dispositivos con paneles solares integrados, autonomía superior a 12 meses sin cambio de baterías.
- **Gateway LoRaWAN:** concentrador(es) que reciben datos de múltiples sensores y los retransmiten al backend (vía Internet o red celular).

La arquitectura del backend debe estar preparada para:
- Recibir y desacoplar la ingesta de datos mediante un message broker (cola de mensajes).
- Normalizar datos de diferentes fabricantes/modelos de sensores.
- Soportar la adición de nuevos tipos de sensores sin modificar el pipeline de ingesta.

## Criterio medible / restricción concreta
- El componente de ingesta IoT debe ser independiente y reemplazable.
- Los sensores se autentican mediante certificados o tokens únicos.
- No especificados en el RFP — definir: proveedor de red LoRaWAN (The Things Network, Helium, ChirpStack autoalojado, operador local colombiano), modelo específico de sensores, tolerancia a pérdida de datos (¿qué pasa si un sensor no transmite durante 24h?).

## Impacto en la arquitectura
- Requiere un message broker (RabbitMQ, Kafka, AWS SQS) para desacoplar la ingesta de datos de los sensores del procesamiento.
- AWS IoT Core ofrece un servicio gestionado para conectar dispositivos LoRaWAN, con integración a SQS/S3.
- Formato de datos flexible (JSON con esquema dinámico) para permitir nuevas variables de sensor sin migraciones de base de datos.

## Notas del analista
- LoRaWAN es la elección correcta para el contexto colombiano: las zonas rurales cafeteras tienen poca cobertura celular, y LoRaWAN ofrece varios kilómetros de alcance con bajo consumo.
- The Things Network (TTN) es una red LoRaWAN comunitaria gratuita con cobertura creciente en Colombia. Alternativamente, se puede desplegar un gateway propio con ChirpStack (open source).
- Los detalles específicos del hardware de sensores no están definidos en el RFP. Esto debe resolverse en la fase de diseño del piloto en conjunto con el Comité de Cafeteros y la IES aliada.
