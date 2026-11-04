# Referencia — APQC Process Classification Framework (PCF)

Guia de apoyo para llenar la seccion "Categorizacion APQC" de `templates/proceso.md`. El **APQC PCF**
(American Productivity & Quality Center) es el marco de referencia estandar, agnostico de industria,
para clasificar procesos de negocio en una jerarquia de 4 niveles:

```
Categoria (nivel 1) > Grupo de proceso (nivel 2) > Proceso (nivel 3) > Actividad (nivel 4)
```

**Proposito de esta seccion en el `.md`:** ubicar el proceso levantado dentro de un lenguaje comun de
la industria (util para benchmarking, para conversar con otras areas, y para detectar si dos procesos
de macroprocesos distintos del cliente en realidad son el mismo proceso APQC duplicado). **No** reemplaza
ni corrige la taxonomia propia del cliente (`00-inventario-procesos.md`) — son dos clasificaciones con
proposito distinto, coexisten sin problema aunque no coincidan 1:1.

**Advertencia de precision:** los 13 nombres de categoria (nivel 1) son estables entre versiones del PCF
Cross-Industry. Los grupos de proceso (nivel 2) listados abajo son los mas representativos de cada
categoria segun las versiones publicas mas recientes del PCF, pero la numeracion exacta de sub-grupos
puede variar levemente entre versiones — si el cliente/proyecto necesita el codigo exacto para
benchmarking formal, verifica contra el documento oficial de APQC vigente en vez de asumir que el listado
de abajo es la version definitiva. Para el uso normal de esta skill (ubicar el proceso, no certificarlo),
esta guia es suficiente.

## Las 13 categorias (nivel 1)

**Categorias operativas:**

| # | Categoria | Cuando aplica |
|---|---|---|
| 1.0 | Develop Vision and Strategy | Planeacion estrategica, direccionamiento, gobierno corporativo |
| 2.0 | Develop and Manage Products and Services | Diseno/desarrollo de nuevos productos o servicios |
| 3.0 | Market and Sell Products and Services | Marketing, ventas, gestion comercial, captacion de clientes/proyectos |
| 4.0 | Deliver Physical Products | Produccion, logistica, cadena de suministro de bienes fisicos |
| 5.0 | Deliver Services | Entrega/ejecucion del servicio al cliente (cuando el "producto" es el servicio mismo) |
| 6.0 | Manage Customer Service | Atencion al cliente, PQRS, soporte postventa |

**Categorias de gestion y soporte:**

| # | Categoria | Cuando aplica |
|---|---|---|
| 7.0 | Develop and Manage Human Capital | Gestion humana: planeacion de talento, reclutamiento/seleccion, desarrollo, compensacion, retiro |
| 8.0 | Manage Information Technology | Gestion de TI, sistemas, infraestructura tecnologica |
| 9.0 | Manage Financial Resources | Contabilidad, tesoreria, presupuesto, impuestos, cartera y facturacion |
| 10.0 | Acquire, Construct, and Manage Assets | Compras/procura, gestion de activos fijos, infraestructura fisica |
| 11.0 | Manage Enterprise Risk, Compliance, and Resiliency | Gestion de riesgos, cumplimiento normativo, juridico, continuidad de negocio |
| 12.0 | Manage External Relationships | Relacionamiento con gobierno, gremios, junta directiva, relaciones publicas, alianzas |
| 13.0 | Develop and Manage Business Capabilities | Gestion del cambio, gestion de conocimiento, mejora continua de procesos, sostenibilidad |

## Grupos de proceso (nivel 2) mas comunes por categoria

Uso como punto de partida — no exhaustivo. Elige el grupo que mas se acerque; si ninguno calza bien,
usa el mas cercano y anotalo en la "Justificacion".

- **7.0 Develop and Manage Human Capital**: 7.1 Planeacion y estrategia de RRHH · **7.2 Reclutar,
  buscar y seleccionar empleados** · 7.3 Desarrollar y asesorar empleados · 7.4 Recompensar y retener
  empleados · 7.5 Redistribuir y retirar empleados · 7.6 Gestionar informacion de empleados.
- **9.0 Manage Financial Resources**: 9.1 Planeacion y contabilidad de gestion · 9.2 Contabilidad de
  ingresos · 9.3 Contabilidad general y reportes · 9.4 Contabilidad de activos fijos/proyectos · 9.5
  Procesar nomina · 9.6 Procesar cuentas por pagar · 9.7 Operaciones de tesoreria · 9.8 Controles
  internos · 9.9 Gestion de impuestos.
- **10.0 Acquire, Construct, and Manage Assets**: gestion de proveedores y compras, gestion de activos
  fisicos, gestion documental/archivo.
- **3.0 Market and Sell Products and Services**: 3.1 Entender mercados/clientes · 3.2 Desarrollar
  estrategia de marketing · 3.3 Planes de marketing · 3.4 Planes de ventas · 3.5 Promocion/marca ·
  gestion comercial y captacion de proyectos.
- **5.0 Deliver Services**: 5.1 Planear y alinear recursos para el servicio · 5.2 Entregar el servicio
  al cliente — aplica a procesos de ejecucion/entrega de eventos, membresias, consultorias.
  Nota: NO uses "Deliver Services" ni "Manage Human Capital" para el proceso interno de vinculacion de
  personal a un tercero (staffing) sin verificar bien el matiz — sigue siendo 7.2 (reclutar/seleccionar)
  aunque el "cliente" final del proceso sea otro cliente externo, no la propia organizacion.
- **11.0 Manage Enterprise Risk, Compliance, and Resiliency**: gestion juridica, riesgos, cumplimiento
  normativo, PQRS ante autoridades.
- **12.0 Manage External Relationships**: relaciones publicas, comunicaciones externas, gobierno
  corporativo, relacionamiento con gremios/gobierno, gestion de membresias/aliados institucionales.
- **13.0 Develop and Manage Business Capabilities**: procesos de mejora continua, gestion documental
  como sistema (no como archivo fisico), gestion del cambio organizacional.

## Ejemplo aplicado

Proceso "Reclutamiento y Selección" (organización de ejemplo, macroproceso Gestión Humana):

- **Categoria APQC:** 7.0 Develop and Manage Human Capital
- **Grupo de proceso APQC:** 7.2 Recruit, source, and select employees
- **Proceso APQC (nivel 3):** Aproximadamente "Manage employee requisitions" + "Screen and select
  candidates" (el PCF los separa; esta organización los combina en un solo flujo end-to-end)
- **Justificacion:** cubre desde la solicitud de personal hasta la vinculación — coincide con el grupo
  7.2 del PCF aunque la organización lo gestione como un solo proceso en vez de dos subprocesos
  separados como sugiere el PCF.
