# Verificar la verificación

## Gate computacional

Descubre los comandos reales (manifiestos, `README`, CI en `.github/workflows`,
`azure-pipelines.yml`, `Jenkinsfile`). No inventes nombres. Para proyectos
Gradle del scaffold, lo habitual es:

```bash
./gradlew build                 # compila y ejecuta tests
./gradlew validateStructure     # reglas de dependencia entre módulos (alias: vs)
./gradlew test --tests '*ArchitectureTest*'   # reglas ArchUnit en app-service
./gradlew jacocoMergedReport    # cobertura agregada, si el proyecto lo usa
```

Registra cada check con resultado `passed`, `failed`, `not_run` (con razón) o
`not_applicable`. Si Builder aportó evidencia, compárala con la revisión actual:
evidencia de otro commit o anterior a la última edición está vencida.

No instales servicios, no apliques migraciones sobre bases compartidas ni
llames APIs remotas con efectos para "poder" ejecutar un check. Usa `not_run`.

## ¿Los tests prueban comportamiento?

Revisa los tests antes que la implementación: revelan la intención.

- ¿Cada AC tiene al menos una comprobación que fallaría si el AC se rompe?
- ¿Prueban comportamiento observable o detalles internos (verificar que se
  llamó a un mock con ciertos argumentos no prueba el resultado)?
- ¿Hay aserciones? Un test sin `assert`/`verify`/`StepVerifier.expect*` no
  prueba nada. En Reactor, un `Mono` no suscrito no se ejecuta: sin
  `StepVerifier` o `.block()` en test, el test pasa vacío.
- ¿Cubren negativos: sin permiso, no encontrado, duplicado, entrada inválida,
  error del adapter?
- Bugfix: ¿existe un test que falla en la versión anterior y pasa en la nueva?
- ¿Se debilitó alguna aserción existente, se añadió `@Disabled`/`@Ignore`, se
  cambió un esperado para "ponerlo verde"? Eso es `bloqueante` salvo que la
  spec lo justifique.
- Mocks que reemplazan exactamente lo que se quiere probar (p. ej. mockear el
  repositorio en un test de "persistencia") no demuestran integración.

## Mutación controlada

Responde "¿lo atraparían los tests?" por experimento, no por lectura, cuando la
lógica sea crítica (dinero, permisos, reglas de negocio) y tengas entorno:

1. Copia el workspace a un directorio temporal (nunca mutes el original).
2. Invierte una condición que el cambio introduce (`>`→`>=`, quitar una
   negación, `&&`→`||`, devolver vacío).
3. Ejecuta solo los tests pertinentes.
4. Si siguen verdes, es un hallazgo `mayor`: nombra el caso de prueba que falta.
5. Elimina la copia. Registra mutación y resultado en el reporte.

No es obligatorio en cada revisión; úsalo donde un falso verde sería caro.

## Cobertura

La cobertura porcentual es auxiliar. 90 % de líneas ejecutadas sin aserciones
significativas no demuestra nada; no bloquees por porcentaje si los AC están
probados, ni apruebes por porcentaje si no lo están.

## Lo que cuenta como evidencia

| Evidencia | Vale para |
|---|---|
| Test ejecutado contra la revisión actual | Comportamiento del AC que asevera |
| Test con fake/mock | Lógica local; **no** integración real |
| Inspección del diff | Ediciones declarativas/triviales |
| "Compila" / "el endpoint arranca" | Nada funcional |
| Relato del autor sin salida | Nada; pide la salida o ejecútalo |
