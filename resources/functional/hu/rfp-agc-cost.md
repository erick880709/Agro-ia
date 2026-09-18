# RFP AGC-COST — Estimación de costos de trabajos de campo (AgroIA v4)

> Fuente: `context/RFP_AgroIA_Estimacion_Costos.md` (Solicitud de propuesta · v1.0 · 2026-09-18).
> Módulo: **AGC-COST** — catálogo de parámetros versionado + motor de cálculo determinista + cotizador.
> Proyecto existente: AgroIA (SPA vanilla + FastAPI + PostgreSQL), esquema `agroia`, JWT, roles Admin/Agrónomo/Cliente/Extensionista, auditoría, migraciones 001→044.

## Descripción funcional

AgroIA ya administra fincas, lotes, comisiones, equipo de trabajo e insumos. Falta el eslabón
previo a la comisión: **cuánto cuesta y cuánto se cobra un trabajo de campo antes de comprometerlo**.
AGC-COST construye un catálogo de parámetros 100% administrable (nada de valores en código),
un motor de cálculo puro y determinista, y un cotizador que produce estimaciones desglosadas,
auditables, con snapshot inmutable y convertibles en comisión y en documento de cobro.

Fórmula de referencia (el motor debe reproducirla exactamente y extenderla sin despliegue):

```
Comisión_visita = Tarifa_base + (Puntos × Tarifa_por_punto_escalonada) + Recargo_dificultad
```

## Reglas de negocio transversales

- Ningún valor monetario, tramo, recargo ni regla de densidad puede estar escrito en código.
- Aritmética monetaria con `Decimal` (NUMERIC(18,4)) — nunca coma flotante; redondeo una sola vez.
- Motor puro, determinista y sin estado: entrada = contexto + parámetros; salida = desglose + trazas.
- Un solo conjunto de parámetros publicado vigente por fecha; publicar archiva el anterior.
- Doble control: editor y aprobador deben ser usuarios distintos (validación en servidor).
- Snapshot inmutable dentro de cada estimación emitida (reproducibilidad dígito a dígito).
- Piso de rentabilidad en pesos: bloquear emisión por debajo salvo autorización con justificación.
- Costos internos (mano de obra, prestacional, margen) nunca visibles para el rol Cliente.
- Documento de cobro: hereda líneas de la estimación aceptada; emitido es inmutable;
  correcciones = anulación (con motivo) + documento nuevo; consecutivo asignado en servidor.

## Recursos a crear

- **Nombre:** Costeo (AGC-COST) — tablas `costeo_*`, `estimacion*`, `cobro_*`
- **Capa(s):** backend + frontend
- **Tipo de recurso:** CRUD + motor de cálculo determinista (no ML)

## Historias de usuario (desglose por fase de entrega del RFP §18)

### AGC-01 · F1 — Modelo de datos, motor de cálculo, conjunto semilla y API de simulación
- **RF:** RF-09 (desglose línea a línea), RF-10 (indicadores), RF-16 (simular), RNF-02/03/04/11.
- **Alcance:** migraciones `costeo_*` + `estimacion`/`estimacion_linea`/`estimacion_snapshot`;
  motor de cálculo puro (`tipo` de componentes: fijo, escalonado, por_unidad, por_distancia,
  por_jornada, porcentual, condicional); orden de resolución de 10 pasos (§8); conjunto semilla
  con tarifa base $100.000, tramos 1–15/$15k, 16–30/$10k, 31+/$7k, factores 0/15/30%;
  endpoints `POST /costeo/simular` y `GET /costeo/parametros/vigentes`.
- **Cierre:** CA-01 a CA-04 en verde en CI. Tolerancia cero en el total.

### AGC-02 · F2 — Pantalla de parámetros con versionado, doble control y simulador
- **RF:** RF-01 a RF-05, RF-14, RF-15, RF-16, RF-18; RNF-06/07/08.
- **Alcance:** CRUD admin de conjuntos/servicios/componentes/tramos/factores/densidad/zona/
  laboratorio/insumos/política/impuestos/descuentos; estados borrador → en_revisión →
  publicado → archivado; validación previa obligatoria; doble control; clonar + reajuste masivo.
- **Cierre:** CA-05, CA-06 y CA-08 en verde; manual de administrador en Ayuda.

### AGC-03 · F3 — Cotizador, ciclo de vida, snapshot, márgenes y descuentos
- **RF:** RF-06, RF-07, RF-08, RF-11, RF-12, RF-13, RF-17, RF-19, RF-21.
- **Alcance:** pestaña «Estimación de costos» (Admin/Agrónomo), flujo 4 pasos (finca/lotes →
  servicios/cantidades → condiciones → resumen/emisión); ciclo borrador → emitida →
  aceptada/rechazada/vencida; snapshot + hash; piso de rentabilidad; topes de descuento por rol.
- **Cierre:** CA-07 y CA-09 en verde; exportación HTML con audiencia agricultor/técnico.

### AGC-04 · F4 — Identidad administrable y PDF de cotización
- **RF:** RF-26, RF-27, RF-28; P-14.
- **Alcance:** CRUD de identidad y contactos (logo PNG/SVG con previsualización, sitio web,
  teléfonos ordenables); motor de composición PDF/HTML (carta, «página X de Y», degradación sin logo).
- **Cierre:** CA-10 y CA-11 en verde; PDF revisado impreso.

### AGC-05 · F5 — Documento de cobro, numeración consecutiva, pagos y anulación
- **RF:** RF-29 a RF-32, RF-34; P-15.
- **Alcance:** `cobro_*`; conversión estimación aceptada → documento; numeración por prefijo
  con bloqueo en servidor; estados emitido/enviado/pagado_parcial/pagado/vencido/anulado;
  pagos con saldo; bloqueos NUMERACION_AGOTADA / RESOLUCION_VENCIDA.
- **Cierre:** CA-12 y CA-13 en verde; flujo cotización → cobro → pago cerrado.

### AGC-06 · F6 — Conversión a comisión, integración con lista de trabajos y auditoría
- **RF:** RF-20, RF-22.
- **Alcance:** convertir estimación aceptada en comisión (precarga equipo/fechas/valor y
  referencia de origen); nueva etapa «estimación» en el semáforo de la lista de trabajos;
  eventos de parámetros y estimaciones en la bitácora de auditoría existente.
- **Cierre:** flujo completo finca → estimación → comisión → orden de trabajo.

### AGC-07 · F7 — Opcionales (según priorización al cierre de F6)
- **RF:** RF-23 (import/export CSV/JSON), RF-24 (cálculo offline PWA), RF-25 (tablero),
  RF-33 (envío PDF por correo/WhatsApp).

## Criterios de aceptación (casos del motor, sección 15 del RFP)

Con el conjunto semilla (base $100.000; tramos 1–15/$15.000, 16–30/$10.000, 31+/$7.000;
dificultad 0/15/30%; sin margen/descuento/redondeo):

| Caso | Lote | Puntos | Dificultad | Total esperado |
|---|---|---|---|---|
| CA-01 | 1 ha, plano | 10 | 0% | $250.000 |
| CA-02 | 5 ha, pendiente moderada | 8 | 15% | $253.000 |
| CA-03 | 20 ha, acceso difícil | 20 | 30% | $487.500 |
| CA-04 | 50 ha, plano | 35 | 0% | $510.000 |

Además CA-05 a CA-15 (ver RFP §15): cambio de tarifa sin despliegue, cuarto tramo, snapshot
reproducible, rechazo de traslapes, tope de descuento, identidad en PDF, numeración, pagos,
anulación y numeración agotada.

## Estado de ejecución (builder)

- [x] **AGC-01 (F1)** — 2026-09-18: migración `045_costeo_parametros` (11 tablas `costeo_*`),
      modelos `models/costeo.py`, motor puro `services/costeo_motor.py` (10 pasos, Decimal,
      componentes fijo/escalonado/por_unidad/por_distancia/por_jornada/porcentual/condicional),
      seed idempotente `services/costeo_seed.py` + `scripts/seed_costeo.py`,
      API `GET /costeo/parametros/vigentes` y `POST /costeo/simular` (Admin/Agrónomo),
      tests `test_costeo_motor.py` (CA-01 a CA-09 + precisión/redondeo) y `test_costeo_api.py`.
      Motor: 18 pruebas en verde; desplegado y validado en producción (CA-01 → $250.000 COP).
- [x] **AGC-02 (F2)** — 2026-09-18: `api/costeo_admin.py` (CRUD de conjuntos, servicios,
      componentes, tramos, factores, opciones, densidad, zonas, impuestos, política,
      descuentos), `services/costeo_validacion.py` (validación previa RF-03/CA-08),
      doble control (APROBADOR_ES_EDITOR), publicación con simulación obligatoria y
      archivo automático del vigente, clonar con reajuste masivo + vista previa (RF-18),
      import/export JSON (RF-23). Simulación what-if sobre borradores (RF-16).
      Frontend: pantalla «Parámetros de costeo» en Administración con sub-pestañas
      y simulador lado a lado.
- [x] **AGC-03 (F3)** — 2026-09-18: tablas `estimacion*` (migración 046),
      `api/estimaciones.py` + `services/estimaciones.py` (ciclo borrador → emitida →
      aceptada/rechazada/vencida, snapshot SHA-256 con selección congelada y
      verificación de reproducibilidad CA-07, piso de rentabilidad RF-12,
      tope de descuento por rol CA-09, vencimiento automático RF-19, export
      HTML/PDF por audiencia RF-21). Frontend: pestaña «Estimación de costos»
      con vista previa en vivo, emitir/aceptar/rechazar y verificación de snapshot.
- [x] **AGC-04 (F4)** — 2026-09-18: `costeo_identidad`/`costeo_telefono`,
      `api/costeo_identidad.py` (CRUD de identidad, teléfonos ordenables, logo
      PNG/SVG con validación, sede con coordenadas para km geodésicos RF-07),
      `services/documentos_costeo.py` (motor de composición carta con «página X de Y»,
      degradación sin logo; reportlab). CA-10/CA-11 cubiertos.
- [x] **AGC-05 (F5)** — 2026-09-18: `cobro_*` + `services/cobros.py` (numeración
      consecutiva con bloqueo en servidor, NUMERACION_AGOTADA/RESOLUCION_VENCIDA,
      pagos con saldo, anulación con motivo). `api/estimaciones.py` expone /cobros*.
      CA-12 a CA-15 cubiertos. Frontend: pantalla «Documentos de cobro».
- [x] **AGC-06 (F6)** — 2026-09-18: conversión estimación aceptada → comisión con
      equipo precargado y referencia de origen (`comisiones.origen_estimacion_id`),
      nueva etapa «estimación» en el semáforo de la lista de trabajos, auditoría
      completa de parámetros, estimaciones y cobros (RF-22).
- [x] **AGC-07 (F7)** — 2026-09-18: import/export JSON (RF-23), tablero de
      estimaciones con tasa de conversión y ticket promedio (RF-25), envío del
      documento por WhatsApp con registro en eventos (RF-33, canal v4 reutilizado).
      El cálculo offline PWA (RF-24) queda documentado como pendiente de priorización.

## Notas técnicas

- **Referencias del proyecto:** CRUD con estados → `api/comisiones.py` + `models/comision.py`;
  cálculo puro → `services/economia.py::calcular_plan_economico`; exportación HTML por
  audiencia → `services/reportes_html.py`; auditoría → `services/auditoria.py::registrar_auditoria`.
- **Convenciones:** FastAPI + SQLAlchemy async + Alembic (siguiente migración: 045);
  esquema `agroia`; JWT con roles; errores `{"code","message"}`; Pydantic v2.
- **Precisión:** `Decimal` en toda la cadena de cálculo; redondeo único parametrizado.
- **Sin valores en código:** todo valor de negocio vive en el conjunto de parámetros.
- **Fuente del RFP:** `context/RFP_AgroIA_Estimacion_Costos.md` (preservada en el repo).
