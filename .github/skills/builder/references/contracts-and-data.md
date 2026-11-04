# Contratos, compatibilidad y datos

## Descubrir el contrato real

Localiza interfaces por componente: OpenAPI, GraphQL, Protobuf, AsyncAPI, schemas de
eventos, tipos de paquetes, CLI o formatos de archivos. Reutiliza su ubicación,
versión y mecanismo de generación; no centralices todo en un OpenAPI nuevo.
Si falta contrato, captura solo la interfaz necesaria usando las convenciones del
proyecto. Un frontend solo debe leer el contrato existente, no reinventarlo.

Cuando existan `resources/design/openapi.yaml` y `api.md` del Builder anterior,
consérvalos como entradas si siguen siendo canónicos. Actualiza por operación/schema,
sin reemplazar contenido ajeno. Reutiliza componentes compatibles y comprueba
colisiones de ruta/método, operationId y nombres. No expongas una entidad completa
por reutilizar su schema: el DTO debe conservar los límites de datos del endpoint.

Antes de implementar interfaces compartidas registra fuente y revisión durable
(commit, versión o hash pertinente), productor, consumidores y propietario. Mantén
nombres, tipos, errores y semántica consistentes aun si solo cambia una capa.

## Evaluar compatibilidad

Compara requests y responses por dirección: un campo obligatorio nuevo en request,
un campo retirado en response, un enum restringido en entrada o ampliado en salida,
un cambio de autorización o semántica pueden romper consumidores. Un cambio
aparentemente aditivo no es universalmente compatible. Evalúa también eventos,
clientes generados, exhaustividad y versiones soportadas.

Usa el analizador de contratos del proyecto cuando exista y comprueba consumidores
afectados. Un diff estructural no detecta todas las rupturas semánticas. Incrementa
versiones y actualiza historial según la política del proyecto; no impongas semver
minor/major por corrida ni migres OpenAPI de versión sin necesidad.

Para una incompatibilidad, identifica consumidores, mitigación/versionado y decisión
necesaria antes de aplicar. Si el usuario ya autorizó ese cambio con alcance claro,
no pidas la misma aprobación otra vez. Si no hay mandato suficiente, conserva la
interfaz actual y bloquea solo el cambio incompatible hasta resolverlo.

## Persistencia y migraciones

Si la skill `dba` está disponible, úsala como criterio experto de datos: `advise`
antes de diseñar el cambio de persistencia y `gate` al cerrarlo (ver `SKILL.md`,
pasos 3 y 5). Sus observaciones `DB-NNN` usan la misma escala que code-review.
Las reglas de esta sección siguen siendo el mínimo cuando `dba` no está.

Inspecciona modelos, restricciones, índices y mecanismo real de migración. Genera
una migración incremental coherente con el proyecto; no reinicialices schemas ni
reescribas migraciones ya aplicadas. Comprueba modificaciones locales del modelo.

Antes de ejecutar una migración identifica el destino mediante configuración no
sensible: debe ser local o aislado y estar autorizado para pruebas. Un valor de
conexión desconocido no demuestra aislamiento. Generar la migración no autoriza
aplicarla en una base compartida/remota. No registres credenciales en la evidencia.

Para cambios con datos existentes, revisa nulabilidad, valores previos, backfill,
compatibilidad entre versiones y orden de aplicación. Usa expansión/contracción
si hace falta; una reversión destructiva no es un rollback seguro. Declara límites
de reversibilidad y prueba con datos sintéticos representativos en entorno aislado.

Si no hay entorno para ejecutar, valida lo que sea posible y entrega migración
pendiente de verificación, sin afirmar que se aplicó ni ocultar el gate pendiente.

## Seguridad y efectos

Deriva las comprobaciones del cambio: identidad no equivale a permiso sobre el
recurso; valida ownership/tenant cuando aplique. Prueba entradas no permitidas y
ausencia de efectos, exposición de campos sensibles y escritura de atributos no
autorizados. No copies logs con secretos o datos personales.

Para concurrencia y reintentos determina dónde se garantiza unicidad/idempotencia
y qué ocurre después de un efecto parcial. No regeneres una clave de operación en
cada intento. Prueba la garantía en el límite que la implementa, no únicamente en
una función mockeada. Remite decisiones arquitectónicas materiales pendientes al
responsable, sin imponer un patrón distribuido a todos los proyectos.
