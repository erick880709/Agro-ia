# Guía: mapeo profundo de integraciones externas

Aplica cuando existe documentación real de un sistema `EXT-xx` — documentación compartida, una colección
Postman o una URL alcanzable — suficiente para mapear campos, no solo para catalogar la operación en `14.00`.
El resultado es `14.xx.N-Mapeo-Integracion_EXT-xx_<Sistema>.md`, sub-artefacto del `14.xx` que posee el
adaptador/ACL hacia ese sistema (ver `references/guia-gobierno-y-diseno-apis.md#8`). Si solo existe el nombre
del sistema y el propósito de la integración, sin evidencia de campos reales, no generes este artefacto:
usa `Sin evidencia disponible` en `14.00` como hoy.

Este artefacto no reemplaza `14.00` (catálogo canónico), `12`/`21` (incertidumbres y riesgos) ni el contrato
ejecutable del `14.xx` dueño. Profundiza el nivel de campo de una integración ya catalogada; no inventa una
integración nueva.

## Contenido

1. [Disparador](#1-disparador)
2. [Ingesta de fuentes](#2-ingesta-de-fuentes)
3. [Estructura del artefacto](#3-estructura-del-artefacto)
4. [Higiene de ejemplos](#4-higiene-de-ejemplos)
5. [Gaps: sin registro propio](#5-gaps-sin-registro-propio)
6. [Gate de cierre](#6-gate-de-cierre)

## 1. Disparador

Genera o actualiza `14.xx.N` cuando el usuario:

- comparte documentación de la API/servicio de un sistema externo (PDF, Word, Excel, Markdown, texto plano);
- comparte una colección Postman (`.postman_collection.json`) exportada de ese sistema;
- comparte una URL de la API o del portal de documentación de ese sistema;
- pide explícitamente mapear, documentar en profundidad o analizar los campos de una integración.

Reserva el consecutivo `N` así: `.1` del `14.xx` dueño es siempre su contrato ejecutable propio (OpenAPI/
AsyncAPI/otro) cuando existe; los mapeos de integración externa usan el siguiente consecutivo libre, uno por
`EXT-xx` (`.2`, `.3`, ...), en el orden en que se documentan.

## 2. Ingesta de fuentes

Registra siempre en la sección "Fuentes consultadas" (ver plantilla en `3.1`) cada fuente usada, con tipo,
fecha/versión y ubicación. Tres tipos de fuente:

**Documentación compartida.** Si el archivo es `.pdf`, `.xlsx`/`.xls` o `.docx`, usa las skills `pdf`,
`xlsx` o `docx` respectivamente para extraer texto y tablas antes de mapear — no transcribas a mano un PDF
grande. Guarda una copia del archivo fuente (o su extracto relevante) bajo `resources/architecture/` junto
al `14.xx.N`, o enlaza su ubicación en el repositorio si ya vive ahí.

**Colección Postman.** Ejecuta `scripts/extract_postman_inventory.py <archivo.postman_collection.json>`
para obtener el inventario completo (nombre, método, ruta, carpeta, tipo de auth, si trae ejemplo de
respuesta guardado) antes de escribir la sección 3.4. No documentes manualmente un subconjunto de la
colección sin antes correr el script: el objetivo es que ningún endpoint quede sin inventariar por omisión
(evita el patrón "colección con 13 endpoints, análisis solo cubre 2"). Si el script reporta más
interacciones que las documentadas en detalle, dilo explícitamente y regístralo como incertidumbre en `12`
o deuda en `21` (ver sección 5), no lo omitas en silencio.

**URL.** Si es la URL base de una API, intenta primero descubrir un contrato machine-readable en rutas
convencionales (`/openapi.json`, `/openapi.yaml`, `/swagger.json`, `/v3/api-docs`, `/.well-known/openapi.yaml`)
con la herramienta de fetch disponible. Si existe, trátalo como cualquier OpenAPI/AsyncAPI de tercero — cítalo
como fuente, no lo declares canónico si no controlas su versión. Si no existe spec, trata la URL como
documentación: haz fetch de la(s) página(s) relevantes y extrae la misma información que de un documento
compartido. Registra la URL exacta y la fecha de consulta; una URL viva puede cambiar sin aviso, por lo que
el snapshot capturado en este artefacto es la "Copia no canónica" que ya exige
`guia-gobierno-y-diseno-apis.md#8`.

## 3. Estructura del artefacto

Sigue `references/plantilla-documento-arquitectura.md` para título, Tabla de Contenido y Criterios de
cierre. El cuerpo tiene estas secciones:

### 3.1 Fuentes consultadas

| Fuente | Tipo | Fecha/versión | Ubicación |
|---|---|---|---|
| `BAPI Fields SAP.md` | Documentación compartida | 2026-04-27 | `resources/architecture/sources/EXT-01/` |
| `SAP-Integration.postman_collection.json` | Colección Postman | v1.0, 2026-05 | `resources/architecture/sources/EXT-01/` |
| `https://api.proveedor.com/swagger.json` | URL (spec descubierto) | consultado 2026-08-10 | enlace externo |

### 3.2 Especificación técnica del canal

Tabla de atributos: protocolo, formato, autenticación, URL por ambiente (cada una `Confirmada`, `Pendiente`
o `Sin evidencia disponible` — no uses solo un ícono), certificados, contenedor/adaptador responsable
(`CT-xx`, enlaza `18-Tacticas-y-Patrones#TP-001` si aplica ACL), resiliencia y timeout. No repitas lo que ya
vive en `14.00`/`09`/`18`; enlázalo y documenta aquí solo el detalle nuevo de protocolo/campo.

### 3.3 Flujo de autenticación

Narrativa numerada del intercambio de credenciales/tokens. Agrega un Mermaid de secuencia solo si el flujo
no es trivial (intercambio de token, mTLS, firma de request) — sigue la regla general de diagramas de
`SKILL.md`.

### 3.4 Inventario de interacciones

| ID | Dirección | Quién expone | Quién consume | `API-xxx-OP-xxx` / `EXT-xx` |
|---|---|---|---|---|

Cada fila enlaza un `API-xxx-OP-xxx` ya existente en `14.00`, o marca `Candidata a API-xxx-OP-xxx nueva —
pendiente de incorporar a 14.00`. Este inventario nunca es un espacio de IDs paralelo: si el sistema externo
invoca algo que el proyecto expone, esa operación debe llegar a `14.00` antes de cerrar este artefacto.

### 3.5 Servicios que el sistema expone al externo (una subsección por operación)

Igual patrón que un `14.xx`: tabla de atributos (endpoint, protocolo, formato, autenticación, rate limiting,
headers, invocado por, evento de dominio, `CT-xx` responsable, idempotencia, reglas de negocio — enlaza
`RN-xx`/`FAS-xxx` real, nunca una regla inventada — contrato, estado), tabla de campos de request y tabla de
respuestas por código HTTP.

### 3.6 Servicios que el sistema consume del externo (una subsección por operación)

Mismo patrón que `3.5`, más:

- descripción del frame/payload (qué representa cada bloque si la estructura es compleja);
- un ejemplo de request y de response reales pero **anonimizados** (ver sección 4);
- tabla de mapeo campo a campo `Campo destino | Tipo | Oblig. | Entidad/campo origen | Lógica` para el
  request saliente, y otra igual para el response entrante — nunca description narrativa sin tabla;
- notas de mapeo numeradas para reglas no evidentes (formato compuesto, valor fijo, cálculo derivado);
- tabla de interpretación de respuesta: condición → resultado → acción del sistema (éxito, error de negocio
  no reintentable, error técnico reintentable, advertencia). Esta tabla es la que más valor aporta a
  implementación: no la omitas aunque el resto del mapeo sea parcial.

### 3.7 Catálogo de datos de referencia del sistema externo (si aplica)

Cuando el sistema externo entrega un catálogo (materiales, estados, monedas, tipos de documento), inclúyelo
como tabla con una nota explícita: `Confirmado completo` (con fuente y fecha) o `Parcial — pendiente de
confirmación` (con qué falta y quién debe confirmarlo).

## 4. Higiene de ejemplos

Nunca pegues un ejemplo de request/response con datos reales de un cliente, empleado o transacción
identificable (documento, nombre, email, teléfono, montos reales de una operación real). Sustituye por
valores sintéticos que conserven formato y longitud. Si la fuente compartida ya trae datos reales, es tu
responsabilidad anonimizarlos antes de pegarlos en el artefacto — no los repitas verbatim.

## 5. Gaps: sin registro propio

No crees una tabla de gaps con IDs propios (`GAP-<SISTEMA>-xxx`) dentro de este artefacto — duplica y
desincroniza el registro real del proyecto. Cada vacío encontrado al mapear se registra donde ya vive:

- si es una pregunta abierta o depende de que el tercero confirme algo → nueva entrada en
  `12-Registro-de-Incertidumbres.md` (`INC-xxx`), con el sistema `EXT-xx` en su descripción para poder
  filtrarla;
- si ya se decidió seguir adelante con el vacío como riesgo aceptado → nueva entrada en
  `21-Riesgos-y-Deuda-Tecnica.md` (`R-xxx`).

Enlaza esos IDs desde este artefacto (una tabla "Incertidumbres y riesgos abiertos" con solo `ID | Resumen`
está bien); no repitas su contenido completo aquí.

## 6. Gate de cierre

Antes de declarar el artefacto `Cumple`:

- toda fuente usada aparece en `3.1` con tipo, fecha/versión y ubicación;
- si hubo colección Postman, el script de inventario corrió y su conteo de endpoints coincide con lo
  documentado, o la diferencia está registrada como incertidumbre/riesgo;
- cada ID de `3.4` enlaza un `API-xxx-OP-xxx`/`EXT-xx` real de `14.00`, no un ID inventado sin dueño;
- cada operación consumida (`3.6`) tiene mapeo campo a campo en ambas direcciones y tabla de interpretación
  de respuesta;
- ningún ejemplo contiene datos reales identificables;
- no existe una tabla de gaps propia — los vacíos viven en `12`/`21` y están enlazados.
