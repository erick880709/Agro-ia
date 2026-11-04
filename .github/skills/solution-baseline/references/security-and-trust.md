# Seguridad y confianza

## Fuentes

Solo usa catálogos declarados en el blueprint o política local aprobada. Cada fuente requiere `namespace`, URL/origen, owner, nivel de confianza y prioridad. Resuelve tags a commit/digest inmutable y verifica integridad antes de leer código ejecutable.

La ubicación de esos catálogos (por ejemplo un catálogo de Backstage, un repositorio Git de arquetipos u otro registro gobernado) es una decisión arquitectónica que documenta `archi` como parte de la arquitectura aprobada. `solution-baseline` no asume una fuente por defecto, no la inventa y no embebe un catálogo propio dentro del skill; si la arquitectura no declara dónde viven los arquetipos y el componente lo requiere, trátalo como vacío pendiente conforme a [architecture-discovery.md](./architecture-discovery.md), no como ausencia de arquetipo.

El resolver no confía en un digest declarado por sí solo. Primero debe existir material local o cacheado sin ejecutar y una atestación creada con `verify-source`. Al resolver, el CLI recalcula el hash o commit y exige coincidencia exacta de `archetype_id`, `source` y `digest`. Una atestación ausente, ajena o cuyo material cambió deja al candidato inelegible o detiene la operación. Descargar/clonar la fuente sigue siendo una acción de red separada y autorizada; `verify-source` no accede a red.

Registra licencia y procedencia de arquetipos, capabilities y generadores. Una coincidencia de nombre no establece identidad ni confianza.

## Clases de acción

| Clase | Ejemplos | Regla |
|---|---|---|
| Lectura local | Inspect, hash, diff | Permitida dentro del alcance solicitado |
| Escritura local | Render temporal, apply | Requiere plan; apply sigue review/aprobación |
| Ejecución | Build, test, codemod | Solo binarios/proyectos confiables y permisos mínimos |
| Red | Clonar, descargar dependencias, consultar catálogo | Fuente permitida; no enviar secretos |
| Mutación remota | Crear repo, push, publicar paquete/arquetipo | Autorización explícita inmediata |

## Hooks y sandbox

Hooks, post-generation tasks y scripts arbitrarios están deshabilitados por defecto. Habilítalos solo si:

- La fuente y versión son confiables e inmutables.
- El hook declara comandos, permisos, red, rutas de escritura y efecto.
- El plan muestra ese efecto y la política o el usuario lo autoriza.
- Se ejecuta en workspace aislado con el mínimo acceso.

No confíes en un hook solo porque está en el catálogo.

## Secretos

Nunca persistas tokens, contraseñas, connection strings reales, claves o contenido sensible en blueprint, manifest, receipt, logs, hashes legibles o prompts de workers. Genera únicamente nombres de variables y `.env.example` sin valores reales. Usa helpers de credenciales existentes cuando una operación autorizada los requiera.

## Supply chain

- Fija versiones y digests; no uses `latest`.
- Usa el esquema de versiones del ecosistema (`semver`, `pep440`, `maven`, `nuget` o `generic`) y resuelve rangos a una versión efectiva exacta.
- Conserva hashes de inputs, render y resultado.
- Evita instalar paquetes globales implícitamente.
- No ejecutes archivos del proyecto durante `inspect`.
- Examina comandos de package scripts antes de instalar en fuentes no conocidas.
- Reporta licencias, vulnerabilidades o firmas según las herramientas disponibles; no inventes certificación ausente.
