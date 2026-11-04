# 10 — Arquitectura de suite, diseño de casos y revisión

## Contenido
1. Principios
2. Convenciones de nombres y archivos
3. Estrategia de datos de prueba
4. Diseño de casos (técnicas)
5. Pirámide y alcance de Karate
6. Anti-patrones (con corrección)
7. Checklist de revisión de PR
8. Formato de reporte de revisión

---

## 1. Principios

1. **Independencia**: cualquier escenario corre solo, en cualquier orden, en paralelo.
2. **Determinismo**: mismo código + mismo ambiente = mismo resultado. Nada de esperas fijas ni datos que "a veces están".
3. **Legibilidad como documentación**: un analista de negocio entiende qué valida la feature leyendo los nombres de escenario.
4. **Una razón para fallar**: cada escenario valida un comportamiento; su nombre dice cuál.
5. **Contrato centralizado**: esquemas en `schemas/`, no repetidos en cada feature.
6. **Configuración fuera del código**: ambientes y secretos en `karate-config.js` + variables de entorno.

## 2. Convenciones

- Archivos: kebab-case, verbo + entidad: `crear-pago.feature`, `consultar-saldo.feature`. Una feature por capacidad/endpoint, no por "sprint".
- `Feature:` describe la capacidad; `Scenario:` describe el comportamiento esperado en presente: "rechaza transferencias sin saldo suficiente", no "test 3" ni "validar que funcione".
- IDs de trazabilidad en el nombre o como tag (`[HU-245][CA-3]` / `@req=HU-245/CA-3`).
- Helpers en `common/` con `@ignore` y un comentario de entradas/salidas en la cabecera.
- Variables en camelCase; constantes de config en camelCase también (Karate no distingue).
- Comentarios: explican el **por qué** (regla de negocio, bug conocido), no el qué.

## 3. Datos de prueba

| Estrategia | Cuándo | Cómo |
|---|---|---|
| Crear por API en el escenario | Por defecto | `call` a helper + limpieza en `afterScenario` |
| Datos únicos generados | Campos con unicidad (documento, email, referencia) | `java.util.UUID.randomUUID().toString()` (v1/v2), `karate.uuid()` (v2), timestamp, `karate.faker` (v2) |
| Datos maestros compartidos de solo lectura | Catálogos, clientes semilla | `callSingle` o archivo por ambiente `data/<env>/...` |
| Setup por BD | Estados imposibles vía API | `DbUtils.update` con SQL parametrizado, solo ambientes de prueba |
| Mock | Dependencia inestable o estado difícil | ver 05 |

Nunca: depender de IDs fijos que alguien puede borrar, datos reales de clientes, ni de que otra feature haya corrido antes.

## 4. Diseño de casos

Para cada campo de entrada / regla:
- **Partición de equivalencia**: un representante por clase válida e inválida.
- **Valores límite**: mínimo−1, mínimo, máximo, máximo+1 (montos, longitudes, fechas, cantidades).
- **Tabla de decisión** para reglas con varias condiciones combinadas (traducir a `Scenario Outline`).
- **Transición de estados** para entidades con ciclo de vida (creado → aprobado → aplicado → reversado): probar transiciones válidas e inválidas.
- **Negativos y seguridad**: ver 04 §10 (401/403/IDOR/validaciones/errores consistentes).
- **Idempotencia y concurrencia** en operaciones monetarias: reintento con la misma llave, doble envío.

Un `Scenario Outline` con 15 filas de validación vale más que 15 escenarios casi idénticos.

## 5. Alcance de Karate en la pirámide

- **Fuerte**: API (componente y E2E de servicios), contrato, integración con mocks, smoke post-despliegue, performance reutilizando features.
- **Bueno**: UI E2E de flujos críticos (pocos), híbridas API+UI.
- **No es su lugar**: pruebas unitarias de lógica interna (JUnit/Mockito), pruebas visuales exhaustivas.

## 6. Anti-patrones

| # | Anti-patrón | Severidad | Corrección |
|---|---|---|---|
| A1 | URL, host o puerto hardcodeado en features | Mayor | `url baseUrl` desde `karate-config.js` |
| A2 | Secretos (tokens, passwords, client secrets) en el repo | **Bloqueante** | Variables de entorno / secretos del pipeline |
| A3 | Login en cada escenario | Mayor | `karate.callSingle` |
| A4 | `Thread.sleep` / `delay()` / `karate.pause` como sincronización | Mayor | `retry until`, `waitFor*` |
| A5 | Escenario sin `status` o sin `match` (no valida nada) | **Bloqueante** | Validar estado y cuerpo |
| A6 | Solo `status 200`, sin validar cuerpo | Mayor | `match response == esquema` |
| A7 | Decenas de `match response.campo == x` sueltos | Menor | Un `match` sobre el objeto completo con marcadores |
| A8 | Escenarios dependientes del orden (B usa ID creado por A en otra feature/escenario) | **Bloqueante** | Cada escenario crea sus datos |
| A9 | Esquema copiado en N features | Mayor | `schemas/*.json` + `read()` |
| A10 | Copiar-pegar escenarios que difieren en datos | Menor | `Scenario Outline` |
| A11 | `{ id: id }` esperando el valor de la variable | Mayor (bug silencioso) | `{ id: '#(id)' }` o `({ id: id })` |
| A12 | `@parallel=false` en proyecto v2 | Mayor (se ignora) | `@lock=<nombre>` |
| A13 | Helpers sin `@ignore` (se ejecutan solos y fallan) | Mayor | Agregar `@ignore` |
| A14 | `print response` de payloads completos con datos sensibles | Mayor | Imprimir solo IDs; configurar masking |
| A15 | Lógica compleja (`if`/bucles largos) dentro de la feature | Menor | Mover a función JS/Java o separar escenarios |
| A16 | Nombres genéricos ("test 1", "validar servicio") | Menor | Nombre de comportamiento + ID |
| A17 | SQL concatenando valores | **Bloqueante** | Parámetros `?` |
| A18 | Varios runners paralelos en CI (reportes fragmentados) | Menor | Un `SuiteTest` |
| A19 | `configure ssl = true` en config de ambientes altos | Mayor | Truststore explícito |
| A20 | Feature de cientos de líneas con todo mezclado | Menor | Dividir por comportamiento |

`scripts/lint_features.py` detecta automáticamente A1, A2 (patrones evidentes), A4, A5, A11, A12, A13, A14, A16, A17 y escenarios largos.

## 7. Checklist de revisión de PR

- [ ] Corre en paralelo y en cualquier orden (probado con `--threads` > 1).
- [ ] Sin URLs ni secretos en features; ambientes en `karate-config.js`.
- [ ] Cada escenario valida estado **y** contenido; usa esquemas compartidos.
- [ ] Casos negativos y de seguridad mínimos por endpoint.
- [ ] Datos creados por el propio escenario y limpiados.
- [ ] Nombres de escenario descriptivos con trazabilidad.
- [ ] Tags conforme a la taxonomía del proyecto.
- [ ] Linter sin hallazgos bloqueantes ni mayores.
- [ ] Sin `print` de datos sensibles; masking configurado.
- [ ] Línea Base actualizada si cambió config, ambientes o convenciones.

## 8. Formato de reporte de revisión

```markdown
## Revisión Karate — <alcance>
Resumen: X bloqueantes, Y mayores, Z menores. <una frase de veredicto>

### Bloqueantes
1. **[A5] crear-pago.feature:42** — el escenario "..." no valida respuesta.
   Corrección:
   ```gherkin
   Then status 201
   And match response == read('classpath:pagos/schemas/pago.json')
   ```
### Mayores
...
### Menores
...
### Cobertura faltante
- POST /pagos sin casos 401/403.
```
Siempre incluir la corrección concreta (código), no solo el diagnóstico.
