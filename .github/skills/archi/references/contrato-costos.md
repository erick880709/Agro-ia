# Contrato de costos por ambiente

## Dueños e inventario de despliegue

`17.4.1-Costos_<Proyecto>.json` es la fuente numérica; `17.4-Pricing_<Proyecto>.md` explica cantidades, tarifas, fuentes y pendientes. `17.5` reutiliza los totales cuando aplica multi-nube o el usuario pide HTML. Cada manifiesto representa una alternativa/configuración y moneda; usar sufijos distintos para alternativas de modelo excluyentes y no sumarlas como si todas se desplegaran.

En `17-Vista-de-Despliegue.md`, confirmar ambientes y cruzar recursos con `10.1`, `14`, `16`, diagramas y recursos observados (AS-IS). Incluir esta sección/cabecera exacta; IDs de recurso estables trazados en el texto a `CT-xx`, SKU, región, réplicas, horarios, retención, tráfico y HA/DR. Los recursos compartidos aparecen con el mismo ID en cada ambiente servido.

```markdown
## Inventario de costos por ambiente

| Ambiente | Proveedor | Recurso | Tratamiento | Justificación |
|---|---|---|---|---|
| dev | azure | RES-api-dev | costed | CT-02, horario laboral |
| prod | azure | RES-api-prod | costed | CT-02, disponibilidad continua |
| dev | azure | RES-registry | costed | Registro compartido |
| prod | azure | RES-registry | costed | Registro compartido |
| prod | azure | RES-identity | excluded | Licencia existente; confirmar cobertura y costo incremental cero |
```

Usar ambientes reales del proyecto; no imponer los del ejemplo. `costed` requiere partida; `excluded` exige motivo sustentado y revisión. El validador cruza esta tabla, pero no descubre recursos omitidos también de ella ni certifica exclusiones. Ningún ambiente de `17` puede quedar fuera de la tabla sin justificación de alcance explícita.

## Manifiesto v1

| Campo | Contrato |
|---|---|
| `version` | Entero `1` |
| `as_of` | Fecha ISO de estimación, no futura ni vencida |
| `currency` | Código de tres letras mayúsculas; importes en una única moneda |
| `max_price_age_days`, `freshness_reason` | Ventana de 1 a 366 días y razón basada en servicio/contrato; no ampliar para ocultar evidencia antigua |
| `deployment` | Ruta relativa al archivo `17` con el inventario |
| `pricing_report` | `17.4-Pricing_<Proyecto>.md`, existente y con delimitadores |
| `html_report` | HTML existente con delimitadores; obligatorio al comparar varios proveedores |
| `environments` | Nombres únicos, igualdad con ambientes de la tabla de `17` |
| `items` | Lista de partidas de esta configuración |

Las rutas de archivos/evidencia son relativas al directorio del manifiesto y deben permanecer dentro de él. No copiar facturas o contratos sensibles: referenciar resúmenes redactados sin secretos y numerados bajo el dueño `17.4`, con fuente interna identificada para revisión autorizada.

## Partidas

| Campo | Contrato |
|---|---|
| `id` | ID único, por ejemplo `COST-001` |
| `provider`, `resource` | Coinciden con la tabla de despliegue |
| `region`, `sku`, `meter`, `category` | Región, SKU/modalidad, medidor y categoría |
| `unit`, `unit_size`, `unit_price` | Unidad de consumo, cantidad cubierta por tarifa (positiva) y precio no negativo por esa cantidad |
| `cadence` | `monthly` o `one_time`; se totalizan separados |
| `quantity` | Objeto `low`, `expected`, `high`: cantidades totales del periodo, finitas, no negativas, ordenadas |
| `allocations` | Fracciones positivas por ambiente, suma exacta 1; dedicado: `{ "prod": 1 }` |
| `assumption` | Fuente del volumen, horario, fórmula/factores y referencia a `04`/medición; no basta «estimado» |
| `evidence.kind` | `public`, `contractual`, `observed` o `approximation` |
| `evidence.ref` | URL de tarifa pública/equivalente; archivo local redactado para contractual/observed |
| `evidence.checked_on` | Fecha ISO de consulta/revisión, no posterior a `as_of` ni vencida al ejecutar |
| `evidence.period` | Obligatorio para contractual/observed: vigencia o periodo conciliado |
| `evidence.reason` | Obligatorio para approximation: equivalente, limitación y pendiente |

Por escenario: `importe = quantity × unit_price / unit_size`, luego reparto por ambiente. Precisión decimal y redondeo a dos decimales al presentar totales. Declarar tasas/descuentos, free tier, moneda y contingencia en cantidades/tarifas/supuestos; no aplicar factores ocultos. Precios escalonados se separan por meter/tramo con fórmula documentada. Una misma combinación ambiente/proveedor/recurso/región/SKU/meter/periodicidad no se puede facturar dos veces.

## Ejemplo ilustrativo, no tarifa utilizable

Este ejemplo solo muestra la forma de una partida. Sustituir tarifa ficticia, fuente, región, SKU y fecha por evidencia del proyecto; la URL genérica no respalda el importe.

```json
{
  "version": 1,
  "as_of": "2026-09-14",
  "currency": "USD",
  "max_price_age_days": 30,
  "freshness_reason": "Revisión mensual antes de presupuestar",
  "deployment": "17-Vista-de-Despliegue.md",
  "pricing_report": "17.4-Pricing_Ejemplo.md",
  "environments": ["dev", "prod"],
  "items": [{
    "id": "COST-001",
    "provider": "azure",
    "resource": "RES-registry",
    "region": "REGION-A-CONFIRMAR",
    "sku": "SKU-A-CONSULTAR",
    "meter": "hosting",
    "category": "registry",
    "unit": "hora",
    "unit_size": 1,
    "unit_price": "0.01",
    "cadence": "monthly",
    "quantity": {"low": 700, "expected": 730, "high": 744},
    "allocations": {"dev": "0.2", "prod": "0.8"},
    "assumption": "Ejemplo ficticio; sustituir por horarios y reparto sustentados en 04",
    "evidence": {
      "kind": "approximation",
      "ref": "https://azure.microsoft.com/pricing/",
      "checked_on": "2026-09-14",
      "reason": "Ejemplo de formato, no cotización"
    }
  }]
}
```

## Bloques y comandos

En cada reporte incluir una sola pareja de delimitadores en el lugar del resumen numérico:

```html
<!-- archi-pricing:start -->
<!-- archi-pricing:end -->
```

```powershell
python .claude/skills/archi/scripts/validate_pricing.py resources/architecture/17.4.1-Costos_Proyecto.json --sync-reports
python .claude/skills/archi/scripts/validate_pricing.py resources/architecture/17.4.1-Costos_Proyecto.json
```

`--sync-reports` reemplaza solo los bloques después de validar manifiesto y delimitadores en todos los reportes. Sin la opción, es solo lectura. Los bloques muestran proveedor, ambiente, periodicidad, escenarios, moneda/fecha y SHA-256 del manifiesto. Las tablas narrativas se trazan a partidas por ID y se revisan contra ellas; no conservar otros totales calculados a mano fuera del bloque.

El validador de coherencia invoca este chequeo cuando encuentra `17.4`/`17.4.1`. Pricing histórico sin manifiesto falla: registrar brecha y migrar explícitamente, sin inventar evidencia ni alterar aprobaciones históricas. Cuando pricing no aplica y no existe, no se crea por esta validación.

## Alcance del chequeo

Detecta cantidades/fechas inválidas, evidencia vencida, ambientes/recursos sin cobertura, meters duplicados, repartos incorrectos y bloques desactualizados. No navega ni certifica autenticidad de tarifas/facturas, completitud de meters, dimensionamiento, exclusiones, viabilidad de SKU o números fuera del bloque. `17`/`25` registran por separado esas revisiones. El éxito aritmético no equivale a presupuesto aprobado ni a gasto real validado.
