# Lógica en base de datos: procedimientos, funciones y triggers

Basado en `adv-logic` (u1pns) y `generating-stored-procedures` (tons-of-skills),
extendido a PL/SQL para el contexto bancario.

## ¿En la base o en la aplicación?

| En la base | En la aplicación |
|---|---|
| Integridad (restricciones), auditoría/historización | Reglas de negocio que cambian, integraciones externas, orquestación |
| Operaciones masivas cercanas a los datos (set-based) | Validaciones complejas con contexto de usuario |
| Sistemas existentes con lógica PL/SQL establecida (respeta el estándar del cliente) | Lógica que debe probarse con unit tests rápidos y desplegarse con la app |

Nuevo código en el Scaffold/microservicios: preferir la aplicación salvo razón técnica
documentada. En sistemas Oracle/APEX existentes, seguir el estándar del equipo.

## Reglas de calidad

- **Set-based** antes que cursores fila a fila; si hay que iterar, `BULK COLLECT`/`FORALL`
  (PL/SQL) o lotes.
- **Transacción explícita** y responsabilidad clara: ¿el procedimiento hace commit o lo
  hace el llamador? (en PL/SQL, generalmente el llamador; nunca commits dentro de bucles).
- **Manejo de errores:** PL/SQL `EXCEPTION` con `RAISE_APPLICATION_ERROR` y códigos
  propios, sin `WHEN OTHERS THEN NULL`; PL/pgSQL `EXCEPTION WHEN ... THEN` + `RAISE`
  con `ERRCODE`; T-SQL `TRY...CATCH` + `THROW` con `SET XACT_ABORT ON`.
- **Sin SQL dinámico concatenado:** `EXECUTE IMMEDIATE ... USING`, `format('%I', ...)` +
  `USING`, `sp_executesql` con parámetros; identificadores solo de lista blanca.
- **Seguridad:** PL/SQL `AUTHID` explícito (`DEFINER` con privilegios mínimos o
  `CURRENT_USER`); PG `SECURITY DEFINER` con `SET search_path` fijo; SQL Server firma de
  módulos o `EXECUTE AS` acotado.
- **Triggers:** cortos, sin efectos externos, sin lógica de negocio oculta; Oracle: evitar
  "mutating table" (compound triggers); orden y recursión controlados.
- **Versionado:** el código de BD vive en migraciones/repositorio, con `CREATE OR REPLACE`
  idempotente y pruebas (utPLSQL, pgTAP, tSQLt).

## Plantilla PL/pgSQL (forma)

```sql
CREATE OR REPLACE FUNCTION app.registrar_movimiento(p_cuenta_id bigint, p_monto numeric(18,2), p_idem text)
RETURNS bigint
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = app, pg_temp
AS $$
DECLARE v_id bigint;
BEGIN
  INSERT INTO app.idempotencia(clave) VALUES (p_idem);           -- UNIQUE: falla si se repite
  UPDATE app.cuenta SET saldo = saldo + p_monto
   WHERE cuenta_id = p_cuenta_id AND saldo + p_monto >= 0;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'saldo insuficiente o cuenta inexistente' USING ERRCODE = 'P0001';
  END IF;
  INSERT INTO app.movimiento(cuenta_id, monto) VALUES (p_cuenta_id, p_monto) RETURNING movimiento_id INTO v_id;
  RETURN v_id;
END $$;
```
