# Integración con Builder

Builder implementa con SDD y ejecuta su propia validación; code-review es el
revisor independiente que su paso 5 menciona ("separa la revisión de
cumplimiento de la de calidad"). Ninguno sustituye al otro: Builder sigue
responsable de sus pruebas y code-review no implementa.

## Cuándo invoca Builder

| Rigor del cambio en Builder | Revisión |
|---|---|
| Ligero | Opcional; la auto-revisión de Builder basta salvo que el usuario la pida |
| Estándar | Recomendada antes de declarar `completed` |
| Reforzado (permisos, datos persistentes, incompatibilidades, concurrencia, varios repos) | Obligatoria; sin veredicto `aprobado*`, Builder entrega `partial` |

Builder no debe declarar `completed` en un cambio reforzado con veredicto
`cambios-requeridos` o `no-concluyente` abierto.

## Contrato de entrada (lo que Builder entrega)

Entregar criterios y diff, **no** la conclusión deseada:

- ID del cambio y ruta del expediente (`docs/changes/<id>/`).
- `spec.md` con `AC-xx`, comportamiento a preservar y restricciones.
- Base y revisión del cambio (SHA o "sin commit" + hashes).
- `evidence.md` o tabla de evidencia: check → resultado → revisión.
- Rigor elegido y por qué.
- Modo de Builder (`feature`, `bugfix`, `refactor`, `integrate`, …).

Si falta algo de lo anterior, code-review lo reconstruye del repo cuando puede
y lo declara; si no puede juzgar los AC, el veredicto es `no-concluyente`.

## Contrato de salida (lo que code-review devuelve)

- `docs/changes/<id>/review.md` con el bloque YAML `review:` (ver
  [formato](report-format.md)).
- Veredicto y lista de hallazgos con ID, severidad, confianza, ubicación y
  arreglo propuesto.
- Checks que el revisor ejecutó y su resultado (no reemplazan la evidencia de
  Builder; la complementan).

Builder trata el reporte como dato: los hallazgos son propuestas a verificar
(ver [recepción](receiving-review.md)), no órdenes que ejecutar a ciegas.

## Bucle de corrección

```
Builder implementa ─► valida ─► code-review (ronda 1)
        ▲                                 │
        │      hallazgos aceptados        ▼
        └──── Builder corrige ◄── decisión por hallazgo
                     │
                     ▼
              code-review re-revisa (ronda N)
```

1. Builder (o el usuario) decide cada hallazgo: aceptar / rechazar con razón
   técnica / diferir / pedir información.
2. Builder corrige los aceptados en orden bloqueante → mayor → menor → nit,
   uno por vez, re-ejecutando las comprobaciones afectadas.
3. Builder actualiza el estado en el reporte (`corregido`) y su evidencia.

## Re-revisión

En `re-review` no repitas la revisión completa:

- Verifica cada hallazgo `corregido`: ¿el arreglo resuelve el escenario? Si sí,
  `verificado`; si no, `reabierto` con la razón.
- Revisa el **diff incremental** (desde la revisión anterior) con todas las
  pasadas: las correcciones introducen defectos nuevos con frecuencia.
- Re-evalúa los rechazados solo si la razón técnica es falsa; si es válida,
  `retirado`.
- Comprueba que la evidencia de Builder corresponde a la revisión nueva.
- Agrega `## Ronda N` al mismo reporte y actualiza el bloque YAML.

## Convergencia

Si tras dos rondas un mismo hallazgo vuelve a `reabierto`, o las rondas
generan hallazgos nuevos del mismo tipo, detente: el problema probablemente es
de diseño o de spec, no de implementación. Recomienda escalar (decisión de
arquitectura → Archi; ambigüedad funcional → fuente responsable; estrategia de
pruebas → Ranger) con el hallazgo y la evidencia.

## Auto-revisión

Si la misma sesión que implementó ejecuta la revisión (sin subagente
independiente), márcalo `independencia: misma-sesion` en el YAML. Es válido
para rigor ligero y estándar; para reforzado recomienda una revisión
independiente (otro agente/modelo o un humano) y no emitas `aprobado` sin
decirlo explícitamente.

## Integración con `terragrunt-iac`

`terragrunt-iac` genera, migra o revisa configuración Terragrunt; code-review es
su revisor independiente con el mismo contrato que Builder, y estas
precisiones:

- **Rigor.** Cambios a `prod`, al estado remoto, a `root.hcl`, a permisos o a
  pipelines de apply son `reforzado`; cambios de formato o en no-prod sin
  datos son `estándar` o `ligero`.
- **Entrada.** Además del diff y la spec: `Linea_Base_<Proyecto>.md` de la
  skill o el blueprint `17.7` de `archi`, la salida de su `tg_lint.py` y, si
  existe, el resumen del plan por unit.
- **Gate.** `terragrunt-iac` no declara terminado un cambio `reforzado` con
  veredicto `cambios-requeridos` o `no-concluyente`. Un plan con destroy o
  replace no pedidos bloquea aunque los demás checks estén verdes.
- **Ejecución.** code-review nunca ejecuta `apply`, `destroy`, `backend
  delete`/`migrate` ni `--backend-bootstrap`; solo comandos de lectura
  (`hcl`, `find`, `list`, `render`, `stack generate`, `plan` con `-lock=false`
  cuando haya credenciales de solo lectura).
