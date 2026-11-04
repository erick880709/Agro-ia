# 11 — Protocolos y autenticación

## OAuth2 / tokens
- **client_credentials** (servicio a servicio): obtener el token una vez en un **setUp Thread Group**, guardarlo como propiedad (`props.put("token", ...)` en un JSR223 PostProcessor) y leerlo con `${__P(token)}` en los hilos. Si expira durante la prueba, renovarlo con un hilo de refresco o un If Controller por tiempo.
- **Por usuario** (password/authorization code en pruebas): login por hilo dentro de un **Once Only Controller** + JSON Extractor del `access_token` + Header Manager `Authorization: Bearer ${token}`.
- No cargar el **proveedor de identidad** corporativo (Azure AD/Entra, Okta) sin acuerdo explícito: suele tener límites y no es el sistema bajo prueba. Usa tokens de prueba o un emisor de pruebas.

## JDBC
JDBC Connection Configuration (`JDBCDataSource`: `dataSource`, `dbUrl`, `driver`, `username`, `password`, `poolMax`) + JDBC Request (`JDBCSampler`: `dataSource`, `queryType`, `query`, `queryArguments`, `queryArgumentsTypes`). Driver en `lib/`. Consultas **parametrizadas** (Prepared Select/Update), nunca concatenadas. En 6.0 el driver de MySQL es `com.mysql.cj.jdbc.Driver`.

## SOAP
HTTP Request POST con cuerpo XML, Header `Content-Type: text/xml; charset=utf-8` y `SOAPAction`. Extracción con XPath2 Extractor; aserciones ligeras (substring del elemento de éxito).

## Kafka, gRPC, WebSocket, MQ
No están en el núcleo de JMeter:
| Protocolo | Opción |
|---|---|
| Kafka | Plugin `di-kafkameter`, o JSR223 con el cliente Kafka (productor reutilizado por hilo) |
| gRPC | Plugin `jmeter-grpc-request` |
| WebSocket | Plugin WebSocket Samplers (Peter Doornbosch) o JMeter DSL `-websocket` |
| JMS / IBM MQ | JMS Point-to-Point / Publisher-Subscriber del núcleo + jars del proveedor |

Declara plugin y versión en la Línea Base; instálalo igual en todos los generadores.

## HTTP/2 y HTTP/3
El HttpClient4 del núcleo usa HTTP/1.1. Para HTTP/2 hay plugins (p. ej. `bzm-http2`); verifica compatibilidad con la versión de JMeter antes de comprometer la prueba.
