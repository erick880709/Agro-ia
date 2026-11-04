---
review:
  id: CR-001
  change: orders-total
  revision: sin-commit
  rigor: estandar
  independencia: independiente
  ronda: 1
  veredicto: cambios-requeridos
  conteo: {bloqueante: 0, mayor: 1, menor: 1, nit: 0, pregunta: 0, preexistente: 0}
  hallazgos:
    - {id: M-01, severidad: mayor, confianza: alta, archivo: "orders.py:6", estado: pendiente}
    - {id: m-01, severidad: menor, confianza: media, archivo: "orders.py:10", estado: pendiente}
---

# Revisión de código — orders-total

**Veredicto:** cambios requeridos: M-01 calcula dinero con float.

## Mayores

### M-01 · Total monetario calculado con float

- **Dónde:** `orders.py:6`
- **Severidad / confianza:** mayor / alta
- **Por qué:** `float` no representa importes decimales exactos: `total(["1.005"])` devuelve `1.0` en vez de `1.01`, y `total(["0.1", "0.2"])` no produce un valor con dos decimales exactos. El payload exige `^\d+\.\d{2}$`.
- **Arreglo:** usar `Decimal` y `quantize(Decimal("0.01"), ROUND_HALF_UP)`; devolver `Decimal`. Test con `1.005`, `0.1+0.2` y lista vacía (`0.00`).
- **Decisión:**
  - [ ] aceptar
  - [ ] rechazar
  - [ ] diferir
  - [ ] necesita más información
- **Nota del autor:**

## Menores

### m-01 · Renombrar `account_id` a `id` en el payload

- **Dónde:** `orders.py:10`
- **Severidad / confianza:** menor / media
- **Por qué:** por consistencia con `order_id` sería más limpio un campo `id`.
- **Arreglo:** renombrar la clave `account_id` a `id` en `to_payload`.
- **Decisión:**
  - [ ] aceptar
  - [ ] rechazar
  - [ ] diferir
  - [ ] necesita más información
- **Nota del autor:**
