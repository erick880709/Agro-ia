# Guía: Diagramas interactivos de flujos

El diagrama interactivo es un HTML autocontenido para **recorrer** un flujo paso a paso: el
lector elige un escenario, avanza con ▶/→, ve cómo se ilumina cada conector, lee en el panel
qué viaja (payload, protocolo, requisito de seguridad) y puede alternar modos
(`AS-IS`/`TO-BE`, `dev`/`prod`). Basado en `architecture-diagram-skill` (konraddzbik) y en el
visor de Archify (tt-a1i), con el gobierno de archi: IDs estables, fuente en `15`/`14.00` y
validación antes de entregar.

Lee antes `references/guia-diseno-diagramas.md` (cuándo conviene) y aplica la notación de
`references/guia-calidad-visual-diagramas.md`.

## Contenido

1. Cuándo usarlo
2. Artefactos y numeración
3. Modelo mental: nodos, flujos, pasos y modos
4. Especificación JSON
5. Diseño de flujos y pasos
6. Construir, validar y mirar
7. Uso ante el Comité
8. Checklist

## 1. Cuándo usarlo

| Sí | No |
|---|---|
| Flujos críticos de `15` que el Comité o el equipo necesitan recorrer (pago, login, ingesta) | Un diagrama estático basta (C4, ER, despliegue) |
| Comparar AS-IS y TO-BE sobre la misma topología (Caso C) | La pregunta no tiene secuencia ni escenarios |
| Onboarding o handoff a builder/QA de cómo fluye un caso de uso | El flujo tiene más de 9 pasos sin poder dividirse |
| Mostrar dónde aplica cada `SEC-xxx` a lo largo de un flujo | Sustituir al `sequenceDiagram` dueño de `15` (siempre se conserva) |

## 2. Artefactos y numeración

- Especificación: `15.1.1-Flujos-Interactivos_<Proyecto>.json` (fuente editable y versionable).
- HTML generado: `15.1-Flujos-Interactivos_<Proyecto>.html` (abrible sin conexión).
- Delta de Caso C con modos AS-IS/TO-BE: puede vivir en `15.1` (si los flujos cambian) o como
  `24.1-Transicion-Interactiva_<Proyecto>.html` + `24.1.1-…json` cuando el foco es la migración.
- `15` enlaza el HTML y contiene la tabla de pasos generada con `--markdown` o equivalente; el
  `sequenceDiagram` de `15` sigue siendo la fuente auditable. `25.1` puede enlazarlo.

## 3. Modelo mental: nodos, flujos, pasos y modos

- **Nodos**: actores, contenedores `CT-xx`, datos `DATA-xxx`, mensajería, externos `EXT-xx`,
  con `role` (color/forma) y opcionalmente `status` por modo (`nuevo`, `retirado`,
  `modificado`).
- **Zonas**: sistema, red o **frontera de confianza** (`TB-xx`, `kind: "trust"`), dibujadas como
  contenedores discontinuos alrededor de sus nodos.
- **Flujos**: escenarios con nombre de objetivo del usuario y operación (`Pago (POST /v1/pagos)`).
- **Pasos**: traspasos `de → a` con tipo (`sync`, `async`, `return`, `self`), etiqueta corta
  (verbo + protocolo), descripción (qué y por qué), payload real, chips (`SEC-004`,
  `p95 < 300 ms`) y referencias (`API-003-OP-002`, `DA-012`).
- **Modos**: forma del despliegue o del tiempo (AS-IS/TO-BE, dev/prod). Un modo cambia nodos
  (oculta, renombra, marca estado) y puede limitar flujos (`onlyMode`); **un modo no es un flujo**.

## 4. Especificación JSON

```json
{
  "title": "¿Cómo se aprueba un pago con tarjeta?",
  "subtitle": "Flujo crítico de 15 · audiencia mixta",
  "description": "Recorrido del pago desde el canal hasta la pasarela, AS-IS y TO-BE.",
  "lang": "es",
  "modes": ["AS-IS", "TO-BE"], "defaultMode": "TO-BE",
  "zones": [{"id": "TB-01", "label": "Zona privada", "kind": "trust", "nodes": ["CT-01", "DATA-001"]}],
  "nodes": [
    {"id": "CANAL", "label": "App móvil", "role": "canal", "detail": "Cliente que inicia el pago"},
    {"id": "CT-01", "label": "API de Pagos", "role": "foco", "tech": "Java 21 · WebFlux",
     "detail": "Orquesta el pago", "refs": ["14.01"], "status": {"TO-BE": "nuevo"},
     "modes": {"AS-IS": {"label": "Monolito de pagos", "tech": "Java 8 · WebLogic"}}},
    {"id": "DATA-001", "label": "Pagos", "role": "datos", "tech": "Aurora PostgreSQL", "detail": "Fuente de verdad"},
    {"id": "EXT-01", "label": "Pasarela", "role": "externo", "detail": "Autoriza la transacción"}
  ],
  "flows": [{
    "id": "pago", "title": "Pago (POST /v1/pagos)", "source": "15 §2", "critical": true,
    "steps": [
      {"from": "CANAL", "to": "CT-01", "label": "HTTPS · POST /v1/pagos",
       "desc": "Solicitud con Idempotency-Key para reintentos seguros.",
       "payload": "{\"monto\": 1200.50, \"moneda\": \"COP\"}", "chips": ["SEC-004"], "refs": ["API-003-OP-001"]},
      {"from": "CT-01", "to": "EXT-01", "label": "mTLS · autoriza", "desc": "Autorización con la pasarela."},
      {"from": "EXT-01", "to": "CT-01", "kind": "return", "label": "402 rechazado", "desc": "Ruta de error.", "error": true},
      {"from": "CT-01", "to": "DATA-001", "label": "SQL/TLS · registra", "desc": "Persiste el resultado con outbox."}
    ]
  }]
}
```

Campos de nodo: `id` (ID estable de archi o un nombre corto para actores), `label`, `role`
(`canal`, `borde`, `servicio`, `foco` ≤ 2, `mensajeria`, `datos`, `externo`, `seguridad`,
`observabilidad`), `tech`, `detail` (responsabilidad en una frase), `refs`, `status`, `modes`
(sobrescrituras por modo, incluido `hidden: true`) y, opcionalmente, `col`/`row` para fijar la
posición. Sin `col`, la columna sale del rol (canal → borde → servicio → mensajería → datos →
externos), que produce lectura de izquierda a derecha.

Ejemplo completo en `assets/ejemplo-flujos-interactivos.json`.

## 5. Diseño de flujos y pasos

- 3–6 flujos que **juntos** expliquen el sistema: camino feliz, ruta de error/compensación,
  escritura asíncrona, autenticación, ingesta. Si son 8 y se parecen, subdividiste de más.
- 3–9 pasos por flujo. Menos de 3 es una llamada, no un flujo; más de 9 es detalle de
  implementación: pliega idas y vueltas o divide.
- Cada paso es un **traspaso** ("X envía Y a Z"); la descripción dice qué viaja y **por qué
  ahora**. Nada de "el servicio procesa".
- Los flujos críticos (`critical: true`) muestran al menos un paso con `error: true`.
- Payloads y nombres reales de `14.00`/contratos `14.xx.y`; chips con `SEC-xxx` de `19.1` donde
  el control se aplica. No inventes evidencia.
- Disposición: usuario a la izquierda, datos a la derecha, servicios en medio; los trabajos
  ocasionales (cron, migración) en una esquina. Con más de 14 nodos, divide.

## 6. Construir, validar y mirar

```bash
python scripts/build_interactive_diagram.py 15.1.1-Flujos-Interactivos_<P>.json \
  -o 15.1-Flujos-Interactivos_<P>.html --markdown /tmp/pasos-15.md \
  --owner 14-Vistas-C4.md 15-Secuencias.md 16-Modelo-de-Datos.md --strict
```

- El script valida la especificación (IDs, roles, modos, pasos 3–9, nodos huérfanos, foco ≤ 2,
  rutas de error en flujos críticos, IDs presentes en los dueños), escapa el contenido y genera
  un único HTML sin dependencias externas.
- La página se autoverifica: `window.archValidate()` devuelve la lista de problemas (nodos
  inexistentes, conectores sin ruta libre, posiciones repetidas); debe ser `[]`.
- **Mírala**: ábrela en un navegador, recorre cada flujo y cada modo, y revisa con el bucle de
  `guia-diseno-diagramas.md` §9 (conectores que rodean nodos, distintivos legibles, foco
  correcto, leyenda completa). Si un conector no encuentra ruta libre, fija `col`/`row`.
- Funciones del visor: pestañas de flujo (teclas 1–9), modos (M), reproducir/pausa (espacio),
  ← →, inicio, búsqueda de nodo, clic en nodo para ver su detalle y sus pasos, tema claro/oscuro
  (T), enlace profundo `#modo=TO-BE&flujo=pago&paso=3`, lista de todos los pasos (también al
  imprimir), anuncios para lectores de pantalla y movimiento reducido respetado.

## 7. Uso ante el Comité

- Enlaza desde `25.1` el HTML con un enlace profundo al paso que sustenta cada argumento.
- Para versión impresa o PDF, la lista "Todos los pasos" queda visible al imprimir; acompaña con
  el `sequenceDiagram` de `15`.
- En Caso C, recorre el mismo flujo en `AS-IS` y en `TO-BE` para mostrar qué se retira, qué es
  nuevo y qué riesgo desaparece.

## 8. Checklist

- [ ] Especificación con `source` por flujo y IDs presentes en los artefactos dueños.
- [ ] 3–6 flujos, 3–9 pasos, ruta de error en los críticos, foco ≤ 2.
- [ ] Payloads, protocolos y `SEC-xxx` tomados de `14.00`, contratos y `19.1`.
- [ ] `build_interactive_diagram.py --strict` sin errores; `archValidate()` vacío.
- [ ] Recorrido manual de todos los flujos y modos; sin conectores sobre nodos ajenos.
- [ ] `15` enlaza el HTML y conserva su `sequenceDiagram` y la tabla de pasos.
