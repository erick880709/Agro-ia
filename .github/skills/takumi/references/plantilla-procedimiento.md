# Referencia generica — Formato de procedimiento/instructivo (respaldo)

Esquema generico tipo ISO 9001/PHVA, agnostico de cliente. **Usa esta referencia solo cuando el
proyecto actual no tenga una plantilla oficial de procedimiento propia** en
`resources/procesos/templates/` (ver `SKILL.md`, Paso 1.0a) — si el proyecto SI tiene plantilla propia,
esa manda sobre esta guia. Aplica tambien, con las secciones que correspondan, a variantes como "Manual
tecnico", "Politica" y "Documento de apoyo" cuando el proceso lo requiera (ver "Variantes" al final).

## Secciones

- **Objeto del proceso**: igual criterio que en la caracterizacion (ver
  [plantilla-caracterizacion.md](plantilla-caracterizacion.md)) — proposito o razon de ser, evitando
  "Definir directrices para...". Preferir verbos como Controlar, asegurar, mantener.
- **Alcance**: extension y limite de aplicacion del documento — donde inicia, actividades
  transformadoras principales, donde termina. Se explicito con lo que queda **fuera**.
- **Definiciones**: terminos que requieren aclararse (tecnicismos del proceso o de la organizacion) que
  sean necesarios para entender el documento.
- **Condiciones generales**: aspectos relevantes a tener en cuenta para ejecutar el
  procedimiento/instructivo (restricciones, supuestos, prerequisitos).
- **Responsable(s)** *(solo aplica a procedimientos, no a instructivos)*: responsables de la aplicacion
  del documento — distintos de los "ejecutores" que aparecen en la tabla de actividades.
- **Documentos relacionados**: documentos que soportan la ejecucion de las actividades (formatos,
  otros procedimientos, normativa).

## Desarrollo — tabla de actividades

Columnas fijas: `ID | ETAPA PHVA | NOMBRE ACTIVIDAD | COMO | RESPONSABLE | REGISTRO`. El `ID` (`AC-001`,
`AC-002`, ...) es numeracion propia de este documento (no global) — se usa para referenciar la actividad
desde la matriz de actividades-actores, las reglas de negocio, y las tablas de mejoras/hotspots (ver
[plantilla-caracterizacion.md](plantilla-caracterizacion.md), secciones "Actores..." y "Reglas de
negocio").

- **Nombre actividad**: verbo en infinitivo, resumido, comprensible fuera de contexto (ej. "Radicar
  solicitud de compra", no "Se radica la solicitud").
- **Como**: responde que/donde/cuando/como/por que hace falta para ejecutar la actividad — el nivel de
  detalle real de ejecucion, no una parafrasis del nombre.
- **Responsable**: cargo de quien ejecuta esa actividad especifica (puede diferir del responsable del
  proceso).
- **Registro**: documento o evidencia que resulta de la actividad, si aplica (puede quedar vacio si la
  actividad no genera un registro).

Agrupa las actividades segun el ciclo PHVA cuando el proceso lo permita, usando estos verbos como guia:

| Etapa | Verbos tipicos |
|---|---|
| Planear | Establecer, Determinar, Definir, Planificar, Programar, Disenar, Incluir, Documentar |
| Hacer | Implementar, Realizar, Desarrollar, Llevar a cabo, Acordar, Suministrar |
| Verificar | Realizar seguimiento, Realizar medicion, Realizar analisis, Realizar evaluacion, Asegurar, Mantener, Verificar, Validar, Revisar, Auditar |
| Actuar | Tomar accion, Mejorar, Tomar accion correctiva, Reaccionar ante no conformidad |

## Flujograma

La plantilla oficial pide un flujograma con simbologia estandar de diagramacion. En esta skill se
genera como diagrama **Mermaid** dentro del `.md` (ver "Paso 6" del `SKILL.md`) — es un borrador de
trabajo 1:1 con la tabla de actividades, no el `.bpmn` final (fase 2, ver "Principio rector" del
`SKILL.md`).

## Control de cambios / aprobacion del documento

Igual estructura que en caracterizacion: tabla `VERSION | FECHA | DESCRIPCION DE LA ACTUALIZACION` y
fila `ELABORO | REVISO | APROBO`.

## Variantes de formato

Cuando el resultado del levantamiento no es un procedimiento operativo sino otro tipo de documento,
ajusta las secciones asi (mismos principios de Objeto/Alcance, sin la tabla PHVA):

- **Manual tecnico**: Objeto, Alcance, Definiciones, Condiciones generales, Desarrollo (libre, tecnico),
  Control de cambios.
- **Politica**: Objeto, Alcance, Politica (declaracion de la politica en si).
- **Documento de apoyo**: Objeto del documento, Alcance, Documentos relacionados, Desarrollo (libre —
  esta plantilla no tiene composicion interna fija, varia segun lo que se necesite describir).

Estas variantes tienen su propio esqueleto en `../templates/manual-tecnico.md`,
`../templates/politica.md` y `../templates/documento-apoyo.md` respectivamente (ver `SKILL.md`, "Resolver
el tipo de documento a producir") — usa esos en vez de `proceso.md` cuando el usuario pida explicitamente
uno de estos formatos, o sigue la plantilla oficial del proyecto si existe una para ese tipo de documento
en `resources/procesos/templates/`.
