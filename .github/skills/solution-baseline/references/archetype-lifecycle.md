# Lifecycle de arquetipos

## Cuándo crear

Crea un candidato solo si no existe una composición compatible y se cumple al menos una condición:

- Hay dos o más consumidores reales o previstos con estructura esencial equivalente.
- Materializa un estándar tecnológico aprobado.
- Centraliza controles transversales difíciles de repetir correctamente.
- Reduce de forma demostrable el arranque sin ocultar decisiones de solución.

Si el componente es específico, genera baseline local con `promotion: not-planned`.

## Subflujo separado

```text
discover → plan → create candidate → test → approve → publish immutable → instantiate
```

1. Abre un workspace/repo exclusivo de catálogo.
2. Neutraliza nombres, secretos y reglas de negocio del proyecto origen. La marca y el diseño visual del origen se convierten en inputs (tokens, assets, catálogo de componentes); no se fijan en la plantilla ni se eliminan.
3. Define schema de inputs, defaults seguros, ownership y capabilities.
4. Selecciona motor nativo y fija su versión.
5. Declara compatibilidad, permisos, licencia, owner y soporte.
6. Añade migraciones desde versiones soportadas cuando corresponda.
7. Genera dos golden projects y ejecuta la matriz de calidad; si el arquetipo declara `design-system`, usa paquetes de tokens distintos en cada uno.
8. Obtén aprobación humana para publicar.
9. Publica versión SemVer inmutable y registra commit/digest.
10. Cierra el workspace mutable antes de instanciar consumidores.

La creación y la instanciación pueden pertenecer al mismo run, pero la publicación es una barrera obligatoria. No instancies desde el directorio mutable del candidato.

## Versionamiento

- Patch: corrección compatible sin cambiar inputs ni ownership observable.
- Minor: capability o input compatible, o nueva migración soportada.
- Major: cambio incompatible de estructura, contrato, runtime mayor u ownership.

No reescribas tags ni versiones publicadas. Depreca con fecha, sustituto y ruta de migración; retira solo según política del catálogo.

## Publicación remota

Preparar el candidato local está dentro del modo. Commit, push, publicación de paquete y cambio del índice remoto requieren autorización explícita y deben registrarse como acciones separadas.

