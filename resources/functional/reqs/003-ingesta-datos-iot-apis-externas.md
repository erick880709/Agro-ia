---
id: 003
slug: ingesta-datos-iot-apis-externas
ia_cierre: 15/100
rondas: 2
estado: lista-para-diseno
fecha: 2026-08-03
---

# NECESIDAD DE NEGOCIO REFINADA

Pipeline de ingesta de datos que recibe mediciones de sensores IoT (18 variables de suelo) vía red LoRaWAN de operador local colombiano, con frecuencia configurable de 15–30 minutos, y las desacopla mediante un message broker para almacenamiento y procesamiento. En paralelo, consume 4 APIs externas MVP (IDEAM cada 24h, Google Maps GIS on-demand, IGAC shapefiles bajo demanda, Copernicus/Sentinel-2 NDVI cada 5 días) mediante conectores modulares e independientes. Si un sensor no transmite durante 24 horas, el sistema marca automáticamente la finca como "datos desactualizados", degrada las recomendaciones y alerta al administrador. La arquitectura soporta agregar nuevas variables de sensor y nuevas APIs sin modificar el pipeline de ingesta. WhatsApp queda como fase 2.

**Fuente(s) de origen**
- `resources/functional/requests/RF-007-captura-sensores-iot.md`
- `resources/functional/requests/RF-008-integracion-apis-externas.md`
- `resources/architecture/definitions/RT-009-iot-lorawan-sensores.md`

**Justificación**

El motor de recomendaciones (refinamiento #1) y el catálogo de cultivos (refinamiento #2) necesitan datos reales del campo para funcionar. Sin un pipeline de ingesta robusto que combine sensores IoT + datos climáticos + datos geoespaciales, la plataforma no tiene materia prima para generar inteligencia. En el contexto colombiano, las zonas rurales cafeteras tienen conectividad limitada, lo que exige una arquitectura tolerante a intermitencia (LoRaWAN + desacople con message broker + marca de "datos desactualizados" sin bloquear el sistema).

**Actores**

| Rol | Tipo | Responsabilidad |
|-----|------|-----------------|
| Sensores IoT | Sistema externo (proveedor) | Transmiten mediciones cada 15–30 min vía LoRaWAN; hardware provisto por aliado tecnológico |
| Administrador | Ejecutor / Monitor | Configura conectores, claves de API y gateways; recibe alertas de sensor offline |
| Sistema (backend) | Ejecutor automático | Ingiere, normaliza, almacena y enruta datos; marca fincas desactualizadas; aplica graceful degradation |
| Cliente (Agricultor) | Beneficiario | Visualiza datos en dashboard; recibe alertas de sensor offline |

**Alcance**

- ✅ IN SCOPE (MVP):
  - Ingesta de 18 variables de suelo desde sensores IoT vía LoRaWAN (operador local colombiano)
  - Frecuencia configurable: 15–30 minutos (por defecto)
  - Message broker RabbitMQ para desacoplar ingesta de procesamiento
  - Capa de abstracción/normalización de datos IoT (JSON con esquema dinámico)
  - Sensor offline ≥24h → marca "datos desactualizados" en la finca + alerta al admin
  - APIs externas MVP: IDEAM 24h, GIS on-demand, IGAC bajo demanda, Copernicus NDVI cada 5 días
  - Conectores modulares independientes con graceful degradation
  - Autenticación de sensores mediante tokens únicos por dispositivo
  - Nuevas variables sin migración de esquema (JSON dinámico)

- ❌ OUT OF SCOPE (MVP):
  - WhatsApp/SMS (fase 2)
  - Soporte multi-fabricante de sensores en MVP
  - Kafka (RabbitMQ suficiente para MVP)

**Criterios de Aceptación** (Gherkin — 4 escenarios)

**Restricciones y Supuestos**
- LoRaWAN operador local, hardware definido por aliado, autonomía >12 meses
- RabbitMQ MVP, JSON dinámico, Secrets Manager para claves API
- Pendiente: cobertura real LoRaWAN en fincas piloto, dataset ID IDEAM para Quindío

**Métricas de Éxito**
| Métrica | Meta |
|---------|------|
| Throughput ingesta IoT | ≥100 msg/s |
| Latencia sensor→DB | <3s (p95) |
| APIs MVP integradas | 4/4 |

**Prioridad (MoSCoW)**
- Must: ingesta IoT + broker, 18 variables, marca 24h, IDEAM, GIS, graceful degradation
- Should: IGAC, Copernicus, alertas admin
- Won't (MVP): WhatsApp, multi-fabricante, Kafka

**Dependencias**
- Motor recomendaciones (#1), Catálogo cultivos (#2), Message broker, Aliado tecnológico

**Brechas:** Cobertura LoRaWAN en campo, dataset ID IDEAM Quindío

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 45/100
 Ronda 1:           28/100
 Ronda 2:           15/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

✅ **Lista para diseño/estimación**
