# Referencia generica — Listados maestros de documentos (respaldo)

Esquema generico de registro de control documental (ISO 9001), agnostico de cliente. **Usa esta
referencia solo cuando el proyecto actual no tenga su propia plantilla de listado maestro** en
`resources/procesos/templates/` — si el proyecto SI tiene plantilla propia, esa manda sobre esta guia.

## Que es esto y en que se diferencia del inventario de procesos

`resources/procesos/00-inventario-procesos.md` trackea el **avance del levantamiento** (que
proceso se ha documentado, en que estado, quien es el responsable). Los listados maestros trackean
algo distinto: el **registro de control documental** — cada documento oficial y controlado de la
organizacion (formatos, procedimientos, politicas, manuales, caracterizaciones ya validadas, y
documentos externos de referencia), con su codigo, version vigente y quien lo elaboro/reviso/aprobo.

**No los confundas ni los fusiones.** Un mismo proceso puede aparecer en el inventario (como fila de
avance de levantamiento) y, una vez su caracterizacion/procedimiento este `Validado por el dueno`,
tambien como fila nueva en el listado maestro de documentos internos (como documento controlado con
codigo propio).

## Listado maestro de documentos internos

Columnas: `CODIGO | NOMBRE DEL DOCUMENTO | MACROPROCESO | PROCESO | TIPO DE DOCUMENTO | ESTADO |
ULTIMA VERSION | FECHA DE LA VERSION | ELABORACION | REVISION | APROBACION | OBSERVACION`.

- **Codigo**: codigo documental unico (ej. `FR-PM-MC-02`, `CP-JU-01` para una caracterizacion de
  Juridica). Si el proyecto no tiene una convencion de codificacion definida, es un hotspot tipo
  "Decision pendiente" — pregunta antes de inventar un esquema de codigos.
- **Tipo de documento**: Formato / Procedimiento / Instructivo / Politica / Manual tecnico /
  Caracterizacion / Documento de apoyo / Circular, etc.
- **Estado**: Activo / Obsoleto / En revision.
- **Elaboracion / Revision / Aprobacion**: nombre o cargo de quien elaboro, reviso y aprobo la version
  vigente.

## Listado maestro de documentos externos

Columnas: `CODIGO | REFERENCIA | FECHA DE EMISION | NOMBRE DEL DOCUMENTO | DESCRIPCION | MACROPROCESO
RESPONSABLE | PROCESO RESPONSABLE | OBSERVACION`.

Documentos que no genera la organizacion pero que un proceso usa como referencia obligatoria: normativa
externa, contratos marco, estandares, circulares de terceros. `Referencia` es el identificador propio
del documento externo (numero de ley, norma tecnica, etc.), distinto del `Codigo` interno que se le
asigna para catalogarlo.

## Cuando se actualizan estos listados

Ver `SKILL.md`, Paso 7b: cuando un proceso llega a estado `Validado por el dueno`, se agrega/actualiza
su fila en el listado interno. Cuando durante el levantamiento (Paso 2/3) aparece un documento externo
referenciado que no esta aun en el listado externo, se agrega ahi.
