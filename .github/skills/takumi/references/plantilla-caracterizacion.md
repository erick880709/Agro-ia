# Referencia generica — Formato de caracterizacion de procesos (respaldo)

Esquema generico tipo ISO 9001/SIPOC, agnostico de cliente. **Usa esta referencia solo cuando el
proyecto actual no tenga una plantilla oficial de caracterizacion propia** en
`resources/procesos/templates/` (ver `SKILL.md`, Paso 1.0a). Si el proyecto SI tiene plantilla propia,
esa manda sobre esta guia — consulta `resources/procesos/templates/00-indice-plantillas.md` en su
lugar.

## Encabezado

- **Codigo**: codigo documental del proceso, si el cliente maneja codificacion formal de documentos. Si
  no se ha asignado codigo todavia, escribe `[PENDIENTE — pendiente de asignacion por gestion documental]`
  y crea un hotspot.
- **Version** / **Fecha**: version y fecha de la caracterizacion (empieza en `1` / fecha de la sesion
  actual para un proceso nuevo).

## Datos previos

- **Macroproceso**: usa exactamente uno de los nombres ya registrados en
  `resources/procesos/00-inventario-procesos.md` (la taxonomia vive ahi, no en esta skill).
- **Proceso**: nombre del proceso (o subproceso) tal como aparece en el inventario, o el nuevo nombre
  acordado con el usuario si es un proceso no listado aun.
- **Tipo de proceso**: Estrategico / Misional / Apoyo / Evaluacion (clasificacion tipica ISO 9001 —
  pregunta si no es evidente por el macroproceso).

## Descripcion del proceso

- **Objeto**: proposito o razon de ser del proceso — el fin al que se dirige la ejecucion de sus
  actividades. Evita frases como "Definir directrices para..." o "Definir lineamientos para...";
  prefiere verbos de accion (Controlar, asegurar, mantener, gestionar, garantizar).
- **Responsable(s)**: cargo (no nombre de persona, aunque puedes anotar el nombre actual entre
  parentesis) de quien lidera el proceso.

## Recursos

Cuatro categorias fijas, cada una como lista breve:
- **Tecnologicos**: sistemas/aplicativos que soportan el proceso.
- **Infraestructura**: espacios fisicos o de red requeridos.
- **Humano**: roles/cargos que ejecutan el proceso (distinto del responsable).
- **Servicios**: servicios internos o externos de los que depende.

**Procesos de apoyo**: otros procesos de la organizacion de los que este depende (ej. Compras, Gestion
Documental, TI).

## Control y medicion del proceso

**Indicadores/medicion del proceso** — tabla `NOMBRE | RESPONSABLE | FRECUENCIA | ACTIVIDAD` (que se
mide, quien lo mide, cada cuanto, y sobre que actividad).

**Mecanismos de control** — controles operativos existentes (aprobaciones, revisiones, conciliaciones,
segregacion de funciones) distintos de los indicadores.

Si el proceso maneja actividades de riesgo (dinero, datos sensibles, aprobaciones criticas) sin
mecanismo de control identificado, es un hotspot tipo "Control/riesgo no definido" (ver SKILL.md).

## Flujo SIPOC

Tabla de 7 columnas: `PROVEEDOR | ENTRADAS | RESPONSABLES | ACTIVIDADES DEL PROCESO | SALIDAS |
RESPONSABLES | PARTES INTERESADAS`. Nota que "RESPONSABLES" aparece dos veces: la primera es quien
recibe la entrada, la segunda quien entrega la salida — no las fusiones en una sola columna.

## Documentos asociados

Dos listas separadas:
- **Documentos asociados**: documentos internos generados o usados por el proceso (formatos,
  procedimientos, instructivos).
- **Otros documentos aplicables**: normativa externa, contratos marco, politicas corporativas.

Referencia estos documentos por su codigo consultando
`resources/procesos/00-listado-maestro-documentos-internos.md` (internos) y
`resources/procesos/00-listado-maestro-documentos-externos.md` (externos/normativa) en vez de repetir su
contenido — ver [plantilla-listado-maestro.md](plantilla-listado-maestro.md).

## Control de cambios / aprobacion

Tabla `VERSION | FECHA | RAZON DE LA ACTUALIZACION` (agrega una fila por cada iteracion sustancial del
documento, incluida la creacion inicial) y fila `ELABORO | REVISO | APROBO` con el rol/nombre de cada
uno (deja `[PENDIENTE]` si aun no hay revisor/aprobador asignado — es informacion normal de faltar en
un borrador temprano, no necesariamente un hotspot salvo que bloquee avanzar).

## Actores del proceso y matriz de relacion actividades-actores

Ademas del "Responsable" por actividad que ya trae la tabla de desarrollo (ver
[plantilla-procedimiento.md](plantilla-procedimiento.md)), esta seccion consolida el catalogo completo
de actores (personas/cargos, areas, o sistemas que ejecutan pasos automaticos) con un ID propio
`AR-###`, y una matriz RACI que cruza cada actividad `AC-###` contra cada actor. El objetivo es dejar
visible cualquier actividad de riesgo sin un "A" (nadie aprueba) o con mas de un "R" sin desempate claro
— eso es hotspot tipo "Control/riesgo no definido", no algo que decidas por tu cuenta.

## Categorizacion APQC

Ubica el proceso dentro del APQC Process Classification Framework (categoria/grupo de proceso nivel 1-2,
ver [plantilla-apqc.md](plantilla-apqc.md) para el listado completo y un ejemplo aplicado). Es un cruce
analitico/de benchmarking — coexiste con la taxonomia propia del cliente en
`00-inventario-procesos.md` sin necesidad de coincidir exactamente.

## Reglas de negocio

Reglas explicitas (condiciones, validaciones, restricciones, calculos) que son una decision de negocio,
no solo un paso mas del flujo — con ID propio `RN-###` y vinculadas a la(s) actividad(es) `AC-###` donde
aplican. Una regla sin actividad asociada, o una actividad de riesgo sin ninguna regla que la controle,
es hotspot tipo "Control/riesgo no definido".
