# Guía: Estimación de costos por proveedor de nube

Aplica a toda generación o revisión de pricing, en una o varias nubes y escenarios A/B/C. Sigue además [contrato-costos.md](contrato-costos.md): `17` posee el inventario por ambiente; `17.4.1-Costos_<Proyecto>.json` posee las partidas y alimenta los totales de `17.4`/`17.5`.

> `17.4-Pricing_<Proyecto>.md` se guarda dentro de `resources/architecture/`.

## Principio rector

No inventes precios de memoria — el pricing de la nube cambia con frecuencia y varía por región. **Usa WebSearch/WebFetch para obtener precios publicados vigentes** en el momento de generar el documento, y dedica un componente del costo a cada servicio identificado en el diagrama de despliegue correspondiente.

## Proceso

1. **Extrae la lista de servicios facturables por ambiente** desde `17`, diagramas, `10.1` y los recursos observados cuando existan. Incluye cómputo, capacidad ociosa, datos/réplicas/IO, backups/DR, almacenamiento, egreso entre zonas/regiones, NAT/IP, balanceadores, endpoints privados/DNS/CDN, colas, seguridad, secretos, observabilidad/retención, registro de imágenes, licencias, soporte y servicios externos. No omitas un servicio por parecer barato: registra costo cero/exclusión con motivo y evidencia. Para IA sigue `guia-costos-ia.md`, incluyendo embeddings y herramientas facturables.
2. **Dimensiona cada servicio y ambiente** según carga y SLO. Confirma los ambientes necesarios (dev, QA, staging, prod, DR solo cuando apliquen), región, SKU, réplicas, horarios activos, datos/retención y tráfico. No estimes dev/staging mediante un porcentaje global de producción. Identifica recursos compartidos y asigna su costo una sola vez, con fracciones justificadas que sumen 1. Si falta información, registra escenarios y supuestos en `04`, sin atribuirlos a mediciones reales.
3. **Busca el precio publicado** de cada ítem con WebSearch/WebFetch. Usa consultas específicas con el nombre exacto del SKU/tier y la región (por defecto la región principal más común salvo que el usuario indique otra: `us-east-1` para AWS, `eastus` para Azure, `us-central1` para GCP). Ejemplos de consulta:
   - `"AWS EC2 pricing t3.medium us-east-1 on-demand"`
   - `"Azure App Service pricing P1v3 East US"`
   - `"Google Cloud SQL pricing db-custom-2-7680 us-central1"`
   - Prioriza siempre la página oficial de pricing del proveedor (`aws.amazon.com/*/pricing`, `azure.microsoft.com/*/pricing`, `cloud.google.com/*/pricing`) sobre blogs de terceros.
4. **Completa el manifiesto `17.4.1`** con cantidades, unidades, tarifas, fuentes y fechas por partida. Separa mensual y único (migración, ingesta inicial, entrenamiento), con escenarios mínimo/esperado/alto por proveedor y ambiente. Explicita descuentos, free tiers, impuestos y conversión de moneda; no aplicarlos silenciosamente al total.
5. **Genera el resumen desde el manifiesto** según `contrato-costos.md`. Compara solo proveedores incluidos; no sumar proveedores/modelos mutuamente excluyentes. En una arquitectura híbrida explica qué servicios se despliegan juntos.
6. **Guarda el resultado** como `17.4-Pricing_<NombreProyecto>.md`.
7. Ejecuta `scripts/validate_pricing.py <17.4.1.json> --sync-reports` para rellenar los bloques de totales, y después sin esa opción para validarlos. Registra resultado y hash en `17.4`; revisa comercialmente fuentes y semánticamente inventario/cantidades. Los detalles narrativos se trazan a IDs de partidas; no mantener otro resumen numérico calculado a mano. Actualiza los checkpoints/hashes de `17`/`25` si cambia una estimación existente.

## Evidencia comercial y gasto real

Clasifica cada partida: `public` (tarifa publicada consultada), `contractual` (acuerdo vigente), `observed` (consumo/facturación conciliado de un periodo) o `approximation` (equivalente explícito, pendiente de validar). Una tarifa pública real no demuestra gasto real del proyecto. Una URL tampoco certifica la cifra: contrastar SKU, región, modalidad, unidad y contenido de la fuente; si la página es dinámica, usar API/calculadora oficial o declarar aproximación.

Usar acuerdos ya disponibles antes de asumir lista pública. Para operación real, conciliar cantidad, periodo, moneda, impuestos/créditos y atribución a ambientes con facturación/telemetría. Conservar solo un resumen de evidencia redactado sin secretos. Si faltan esos datos, declarar estimación y pendiente de conciliación. Definir antigüedad aceptable de precios con justificación y renovar evidencia al vencer; no presentar una verificación aritmética como aprobación financiera.

## Plantilla de `17.4-Pricing_<Proyecto>.md`

La tabla comparativa siguiente es una orientación de categorías para la explicación. El resumen numérico contractual se inserta únicamente con los delimitadores `archi-pricing:start`/`archi-pricing:end` de `contrato-costos.md`; sustituye los totales manuales de esta plantilla. Añade alcance de ambientes, exclusiones/recursos compartidos, evidencia comercial, costos únicos, limitaciones y responsable de pendientes.

```markdown
# Estimación de Costos de Despliegue: [Nombre del Proyecto]

**Fecha de la estimación:** [fecha]
**Región de referencia:** [región usada por proveedor, si difiere indicarlo por proveedor]

> ⚠️ **Esto es una estimación basada en precios públicos de lista (on-demand) vigentes a la fecha indicada.**
> No incluye: descuentos por volumen, instancias reservadas/committed use, planes de soporte, ni acuerdos empresariales.
> Valida las cifras finales en la calculadora oficial de cada proveedor antes de tomar decisiones de presupuesto:
> [AWS Pricing Calculator](https://calculator.aws) · [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator) · [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator)

## Supuestos de dimensionamiento

[Lista de supuestos de carga/tamaño usados para dimensionar cada servicio — ver paso 2 del proceso.]

## Comparativo de costo mensual estimado

| Proveedor | Cómputo | Base de datos | Storage | Red/CDN | IA/LLM | Otros | **Total mensual estimado** |
|---|---|---|---|---|---|---|---|
| AWS | $[x] | $[x] | $[x] | $[x] | $[x]–$[y] | $[x] | **$[total]** |
| Azure | $[x] | $[x] | $[x] | $[x] | $[x]–$[y] | $[x] | **$[total]** |
| GCP | $[x] | $[x] | $[x] | $[x] | $[x]–$[y] | $[x] | **$[total]** |

Omite la columna IA/LLM (o dilo explícitamente como "No aplica") si el proyecto no llama a ningún LLM. Cuando aplica, la columna refleja el rango calculado en `references/guia-costos-ia.md`, no un valor puntual inventado.

## Detalle AWS

| Servicio | SKU / Tier | Cantidad | Precio unitario | Costo mensual estimado | Fuente |
|---|---|---|---|---|---|
| [ej. EC2] | [ej. t3.medium] | [ej. 2 instancias, 730h/mes] | $[x]/h | $[x] | [enlace a la página de pricing consultada] |

## Detalle Azure

[misma estructura de tabla]

## Detalle GCP

[misma estructura de tabla]

## Estimación de costos de IA/LLM

[Solo si el proyecto llama a un LLM. Sigue `references/guia-costos-ia.md` — no dejes esta sección en "No estimable" solo porque el modelo no está elegido; usa el rango entre modelos candidatos.]

## Observaciones y recomendación

[2-4 líneas: qué proveedor conviene según el balance costo/requerimientos no funcionales del proyecto, y qué variable (ej. tráfico de salida, soporte 24/7, familiaridad del equipo) podría cambiar esa conclusión.]
```

## Reglas de honestidad

- Si no encuentras el precio exacto de un SKU específico, usa el tier equivalente más cercano y dilo explícitamente en la columna "Fuente" (ej. "aproximado por tier equivalente, no se encontró el SKU exacto").
- Nunca presentes un total como definitivo — siempre "estimado".
- Si el usuario ya tiene descuentos negociados o un Enterprise Agreement con algún proveedor, pregúntale antes de asumir precios de lista, ya que puede cambiar la conclusión por completo.
