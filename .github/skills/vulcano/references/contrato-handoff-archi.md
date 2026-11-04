# Contrato de handoff entre Archi y Vulcano

## Índice

1. [Objetivo](#1-objetivo)
2. [Descubrimiento de artefactos](#2-descubrimiento-de-artefactos)
3. [Orden de lectura](#3-orden-de-lectura)
4. [Propiedad de la información](#4-propiedad-de-la-información)
5. [Consumo de requisitos `SEC-xxx`](#5-consumo-de-requisitos-sec-xxx)
6. [Mapeo a documentos Vulcano](#6-mapeo-a-documentos-vulcano)
7. [Estados y conflictos](#7-estados-y-conflictos)
8. [Reglas por escenario](#8-reglas-por-escenario)
9. [Gate de consistencia](#9-gate-de-consistencia)

## 1. Objetivo

Este contrato evita dos verdades paralelas entre arquitectura y DevSecOps. Archi define el
sistema, sus amenazas y propiedades de seguridad; Vulcano consume esas decisiones y diseña
su operacionalización mediante CI/CD, pruebas, supply chain, IaC, secretos y evidencia.

No vuelvas a preguntar datos que ya estén resueltos con estado y fuente en Archi. Sí pregunta
por herramientas, stages, severidades, SLA, owners operativos o excepciones cuando aún falten,
porque pertenecen a Vulcano.

## 2. Descubrimiento de artefactos

Busca recursivamente bajo `resources/architecture/` para soportar proyectos con carpeta propia.
Prioriza la numeración vigente:

| Prioridad | Patrón vigente | Uso en Vulcano |
|---:|---|---|
| 1 | `**/01-Linea-Base_*.md` | Stack, nube, cumplimiento, equipo, DevOps y observabilidad confirmados |
| 2 | `**/00-Documento_Arquitectura_*.md` | Índice y estado aprobado greenfield |
| 3 | `**/00-Arquitectura_AS-IS_*.md` | Índice y evidencia aprobada actual |
| 4 | `**/00-Arquitectura_TO-BE_*.md` | Índice y diseño objetivo aprobado |
| 5 | `**/10.1-Arquetipo-de-Solucion_*.md` | Baseline tecnológico, hosting, building blocks y estados |
| 6 | `**/14-Vistas-C4.md` y `**/14.*-Diseno-Detallado_CT-*.md` | Contenedores, tecnologías, contratos y boundaries |
| 7 | `**/14.00-Gobierno-y-Catalogo-Inicial-de-APIs_*.md` | APIs/operaciones, exposición, datos y seguridad requerida |
| 8 | `**/17-Vista-de-Despliegue.md` | Ambientes, nube, identidad, zonas y topología |
| 9 | `**/19-Dimensiones-Arquitectonicas.md` | Calidad, Clean Code, operación y seguridad transversal |
| 10 | `**/19.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_*.md` | `THR-xxx`, `SEC-xxx`, aceptación y handoff |
| 11 | `**/20-Decisiones-Arquitectonicas.md` | Decisiones y excepciones vigentes |
| 12 | `**/21-Riesgos-y-Deuda-Tecnica.md` | Riesgo residual/deuda que Vulcano puede reducir |
| 13 | `**/25-Revision-Tecnica-Arquitectura.md` | Hallazgos y gate técnico |
| 14 | `**/26-Validacion-y-Aprobacion.md` | Autoridad, aprobación y condiciones |

Por compatibilidad, si los nombres vigentes no existen, acepta como legacy:

- `resources/architecture/definitions/Linea_Base_*.md`;
- `resources/architecture/Documento_Arquitectura_*.md`;
- `resources/architecture/Arquitectura_AS-IS_*.md`;
- `resources/architecture/Arquitectura_TO-BE_*.md`;
- `resources/architecture/stack.md` y `overview.md`.

Nunca prefieras un legacy más antiguo sobre un archivo numerado vigente. Si hay varios
proyectos, relaciona nombre/ruta con el `project_id` y detente ante una selección ambigua.

## 3. Orden de lectura

1. Lee `26` y `25` para conocer aprobación, bloqueantes y versión revisada.
2. Lee el `00` aplicable como índice; no lo uses como única fuente técnica.
3. Lee `01`, `10.1`, `14`, `17` y `19` para baseline y diseño.
4. Lee `19.1`, `20` y `21` para seguridad, excepciones y riesgo residual.
5. Sigue enlaces a `14.00`, `14.xx`, `16.xx` o fuentes solo cuando sean necesarios para el
   archivo Vulcano en curso.
6. Revisa `RNF-*`/`RT-*` de Janus y evidencia real del repositorio para completar, no para
   sobrescribir una decisión aprobada silenciosamente.

Registra en el manifiesto o documento Vulcano la ruta, versión/hash y estado de aprobación de
cada fuente material. Un borrador puede orientar, pero no se presenta como decisión aprobada.

## 4. Propiedad de la información

| Tema | Dueño | Regla de integración |
|---|---|---|
| Alcance, C4, componentes y datos | Archi | Vulcano enlaza; no rediseña el sistema |
| Amenazas y escenarios de abuso `THR-xxx` | Archi `19.1` | Vulcano consume el driver |
| Requisito y criterio arquitectónico `SEC-xxx` | Archi `19.1` | Vulcano conserva ID y semántica |
| Controles de aplicación/API | Archi `14.00`/`14.xx`/`19.1` | Vulcano automatiza evidencia cuando sea viable |
| Herramientas SAST/DAST/SCA/IAST/secrets/images/IaC | Vulcano | No se duplican en Archi |
| Stages, umbrales, severidades y política de fallo | Vulcano | Deben mapear a riesgo y `SEC-xxx` |
| SLA de remediación y excepciones operativas | Vulcano | Excepciones arquitectónicas vuelven a `20`/`21` |
| SBOM, firma, provenance y policy as code | Vulcano | Implementación y evidencia continua |
| Materialización local de CI/CD/IaC | Vulcano Bob | Implementa la definición aprobada de Vulcano |
| Operación remota | Vulcano Operador | Solo con autorización y verificación |

## 5. Consumo de requisitos `SEC-xxx`

Al generar o actualizar `devops-strategy/08-security.md`, crea una fila por cada `SEC-xxx` del
handoff de `19.1`. Conserva texto/criterio mediante enlace y añade la operacionalización:

| Campo | Regla |
|---|---|
| `SEC-xxx` | ID exacto de Archi; no renumerar ni reutilizar |
| Scope | `CT/API/OP/Dato/Zona` de origen |
| Criterio arquitectónico | Cita corta o enlace a la sección dueña |
| Control operacional | Gate, prueba, política, evidencia o proceso que lo soporta |
| Documento owner Vulcano | `06-ci-cd`, `07-continuous-testing`, `08-security`, secrets u otro |
| Evidencia producida | Reporte, attestation, test, log, aprobación o excepción |
| Frecuencia/momento | PR, build, release, runtime, periódico o manual justificado |
| Estado | Cubierto, Parcial, Pendiente, No requiere automatización, Excepción |

Reglas:

- un `SEC-xxx` puede mapear a varios controles y documentos;
- varios `SEC-xxx` pueden compartir un control, pero conservan filas separadas;
- `No requiere automatización` exige motivo y evidencia/owner alternativo;
- `Parcial` o `Pendiente` exige riesgo, owner y fecha/condición de salida;
- una excepción que cambia riesgo o criterio se registra también en Archi `20`/`21`;
- Vulcano no suaviza un criterio porque una herramienta no lo soporte; registra la brecha.

Si no existe `19.1`, no inventes `SEC-xxx`. Deriva requisitos operativos de `03`, `05`,
`14.00`, `14.xx`, `17`, `19`, estándares corporativos y evidencia, e indica la fuente. Si
encuentras riesgo arquitectónico material no cubierto, recomienda volver a Archi para crear o
actualizar `19.1`.

## 6. Mapeo a documentos Vulcano

| Necesidad | Documento Vulcano principal |
|---|---|
| Topología del pipeline y promoción | `devops-strategy/06-ci-cd.md` |
| Pruebas funcionales/no funcionales continuas | `devops-strategy/07-continuous-testing.md` |
| SAST, DAST, SCA, IAST, secrets, images y supply chain | `devops-strategy/08-security.md` |
| Gestión operativa de credenciales/secretos | `infrastructure-as-code/08-secrets-management.md` |
| Scanning/policy/costo de IaC | `infrastructure-as-code/09-testing.md` y `10-policy-as-code.md` |
| Acceso, aprobación y promoción | `05-environments.md`, `06-ci-cd.md`, `09-release-management.md` |
| Evidencia runtime/alerta | documentos de observabilidad e incident management |

Usa el nombre lógico y la ruta canónica del manifiesto cuando difieran. No copies el modelo de
amenazas completo en cada archivo; `08-security` actúa como índice de operacionalización.

## 7. Estados y conflictos

- **Fuente aprobada:** se consume como restricción/decisión vigente.
- **Fuente aprobada con condiciones:** cada condición se refleja como pendiente o gate.
- **Borrador:** se usa como hipótesis con ruta/hash; requiere confirmación antes de una decisión
  irreversible o un gate bloqueante.
- **Contradicción con código:** los hechos observables mandan para AS-IS; la aprobación manda
  para TO-BE. Documenta el gap, no sobrescribas ninguno.
- **Contradicción entre documentos:** informa archivos/versiones, impacto y dueño; devuelve la
  decisión al artefacto canónico.

## 8. Reglas por escenario

- **Greenfield:** `SEC-xxx: Definido` puede operacionalizarse como diseño de controles aún sin
  evidencia de ejecución. No marques `Cubierto` hasta definir control, evidencia y owner.
- **AS-IS:** valida pipelines/configuración/reportes reales. Distingue documentado, implementado
  y efectivo; no conviertas intención en evidencia.
- **TO-BE:** separa control actual de objetivo, brecha, fase, rollback y criterio de salida.

## 9. Gate de consistencia

Antes de cerrar la sesión Vulcano:

- [ ] se leyeron las fuentes Archi vigentes y se registraron ruta/estado/versión;
- [ ] no se re-preguntaron decisiones confirmadas;
- [ ] cada `SEC-xxx` aplicable aparece en la matriz de operacionalización;
- [ ] cada fila tiene control o disposición, owner, evidencia esperada y estado;
- [ ] `Parcial`, `Pendiente` y `Excepción` tienen riesgo y salida;
- [ ] no se renumeraron ni redefinieron requisitos Archi;
- [ ] contradicciones y cambios de riesgo volvieron a `19.1`, `20` o `21`;
- [ ] `06-ci-cd`, `07-continuous-testing`, `08-security`, secrets e IaC son consistentes;
- [ ] la especificación entregada a Bob no promete una capacidad no materializable sin marcar
  la brecha.
