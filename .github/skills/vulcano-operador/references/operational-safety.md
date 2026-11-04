# Seguridad operacional

Toda mutación requiere cierre estricto de Bob, reconciliación reciente, acción mínima, hash de
alcance, confirmación explícita, autorización vigente y lectura inmediata anterior.

- La confirmación debe nombrar `OP-ACT-NNN` o el target exacto.
- Consultar por nombre/ID antes de crear.
- Si el estado ya coincide, verificar sin repetir.
- Si el snapshot cambió, cancelar autorización y reconciliar.
- Ante timeout o respuesta ambigua, leer antes de reintentar.
- Usar ETag, commit o revisión cuando la plataforma los exponga.

`configure` expira máximo en 24 horas. `execute` expira máximo en 30 minutos. Producción puede
observarse, pero el agente no responde approvals.

Guardar herramienta, hashes de request/response sanitizados, resultado, ID externo y timestamps.
Nunca guardar payloads crudos ni credenciales.

## Acciones de ciclo de vida de release

`approve_deployment`, `promote_release`, `rollback_deployment` y `tag_release` operan sobre un
release ya desplegado, no sobre configuración de repositorio/pipeline — la misma disciplina de
arriba aplica sin excepción, más estas puntuales:

- `approve_deployment` nunca resuelve un approval de producción, incluso si la plataforma lo
  permite técnicamente; el agente jamás aprueba su propio cambio (ver `SKILL.md` §Límites).
- `rollback_deployment` exige releer el estado del target inmediatamente antes de ejecutar — un
  rollback contra un snapshot obsoleto puede revertir sobre un estado que ya cambió.
- Ninguna variante de `update_*_variable`/`update_variable_group` usada para rotar una referencia
  de secreto persiste el valor del secreto: solo la URI/path del gestor externo ya definido en
  `decisions.secrets_manager`.

## Progresión de ambiente (dev → qa → prod)

`queue_pipeline`, `approve_deployment` y `promote_release` — los tipos que promueven un
despliegue hacia adelante — exigen `--environment <dev|qa|prod>` en `plan-operation.mjs`. El
script bloquea con `Progresión bloqueada` cualquier intento de proponer una acción para `qa` o
`prod` si no existe ya, para el mismo `logical_id`, una acción del ambiente inmediatamente
anterior con `status: verified` y `verification.result: succeeded` — nunca saltar de `dev`
directo a `prod`, ni promover `prod` sin que `qa` haya pasado por verificación real (no solo
ejecución exitosa: `succeeded` sin `verify` posterior no cuenta). `dev` no tiene predecesor, así
que no requiere esta comprobación.

Este guardrail vive en el propio operador (no depende de que el pipeline generado por Bob
respete su propio `dependsOn` entre stages) — es la capa de seguridad que impide que una
operación remota individual (ej. un `approve_deployment` disparado a mano) salte la escala
dev/qa/prod aunque el pipeline en sí ya la modele correctamente.

`rollback_deployment`, `cancel_pipeline_run` y las acciones `configure` (`register_pipeline`,
`create_environment`, `update_variable_group`, `configure_branch_policy`, `tag_release`) quedan
fuera de esta exigencia a propósito: son correctivas o de configuración, sin una noción de
"promover hacia adelante" a la que aplicarle orden de ambiente.
