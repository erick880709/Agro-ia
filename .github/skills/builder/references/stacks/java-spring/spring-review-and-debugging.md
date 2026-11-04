# Revisión y diagnóstico Java / Spring

Complementa [diagnóstico y revisión](../../review-and-debugging.md). La revisión
de cumplimiento va primero; esta lista concreta la revisión de **calidad** del
diff. Clasifica por impacto observable; una preferencia compatible con el
proyecto no bloquea.

## Lista de calidad del diff

**Bloqueante** (defecto probable, seguridad o datos)

- Violación de la regla de dependencias del Scaffold: `usecase` o `model` con
  imports de Spring, Jakarta, adaptadores o `app-service`; infraestructura que
  depende de `app-service`.
- Check-then-act sobre un almacén compartido en lugar de una operación atómica;
  confirmación (ack) o marca de procesado antes del efecto; sin camino de
  reproceso tras fallo.
- `@Transactional` que no aplica (auto-invocación, método privado, excepción
  checked sin `rollbackFor`, excepción capturada) en una operación que lo
  necesita; llamada remota o publicación a broker dentro de la transacción sin
  outbox.
- `.block()`, JDBC o SDK síncrono dentro de un flujo reactivo; `subscribe()`
  dentro de un flujo; trabajo ejecutado antes de la suscripción.
- SQL/JPQL concatenado con entrada; entidad JPA expuesta por la API; ruta nueva
  sin regla de autorización o sin verificar pertenencia del recurso; secretos,
  tokens o PII en logs o en `application.yaml`.
- `double`/`float` para dinero; `BigDecimal.equals` donde se quería
  `compareTo`; redondeo distinto al especificado.
- API posterior a la release Java o a la versión de Boot declaradas; versión o
  dependencia subida sin mandato.

**Mayor** (mantenibilidad o contrato)

- Inyección por campo, `@Value` en campos, dependencias ocultas o ciclos.
- N+1 evidente (colección perezosa recorrida en bucle), `EAGER` nuevo, consulta
  sin paginación sobre tablas grandes.
- Errores técnicos que escapan al dominio, `catch (Exception)` que silencia,
  log-y-relanzar, mensajes internos en la respuesta HTTP.
- Cambio de ruta, DTO, código de error, nombre de evento o esquema sin evaluar
  consumidores.
- Cliente HTTP sin timeouts; reintentos sobre operaciones no idempotentes.
- Nombres de dominio con sufijos técnicos (`Dto`, `Request`, `Response`) o de
  tecnología en el Scaffold; clase nueva fuera de la capa correspondiente.
- Prueba que no puede fallar: `@SpringBootTest` sin aserciones de
  comportamiento, `StepVerifier` sin `verify*`, duplicados probados solo en
  secuencia, filtro de tests que no ejecuta nada, H2 presentado como prueba de
  compatibilidad con la base productiva.

**Menor** (si Checkstyle/Spotless no lo decide ya)

- Forma antigua donde la release permite la moderna en líneas nuevas
  ([tabla](spring-modern-by-version.md)).
- Lombok o MapStruct usados de forma distinta al módulo de referencia.
- Logging con concatenación en lugar de parámetros.

Antes de reportar, vuelve a leer cada hallazgo contra el diff y elimina los que
no puedas justificar con archivo y línea.

## Diagnóstico dirigido por evidencia

| Síntoma | Primera observación discriminante |
|---|---|
| `NoSuchBeanDefinitionException` / `UnsatisfiedDependencyException` | ¿El paquete está bajo el escaneo? En Scaffold, ¿el nombre termina en `UseCase` y lo cubre `UseCasesConfig`? ¿Falta el adaptador que implementa el puerto o su perfil activo? |
| `BeanCurrentlyInCreationException` (ciclo) | Grafo de constructores; extraer la responsabilidad compartida, no añadir `@Lazy` |
| `LazyInitializationException` | Acceso a una relación fuera de transacción; cargar con `JOIN FETCH`/proyección en el adaptador |
| Cambios no persistidos o sin rollback | Proxy no aplicado (auto-invocación, método privado), excepción checked, transacción en el bean equivocado; activar `logging.level.org.springframework.transaction=DEBUG` |
| Muchas consultas por petición | Log SQL o estadísticas de Hibernate; N+1 en relaciones perezosas |
| `NoSuchMethodError` / `ClassNotFoundException` al arrancar | Conflicto de versiones (BOM sobrescrito, `javax` frente a `jakarta`); `./gradlew dependencies` / `./mvnw dependency:tree` |
| Flujo reactivo que no hace nada | No hay suscripción o el `Mono` se descartó; buscar efectos fuera de la cadena |
| `blocking call` / hilos `reactor-http` agotados | `.block()` o I/O síncrono en el event loop; BlockHound o volcado de hilos |
| Evento procesado dos veces | Check-then-act, ack antes del efecto, reintento sin idempotencia |
| Test pasa local y falla en CI | Orden de tests, contexto cacheado contaminado (`@DirtiesContext`), zona horaria/locale, Docker ausente |
| `validateStructure` o ArchUnit fallan | Import entre capas no permitido o nombre de clase fuera de convención |

Antes de culpar a la caché de Gradle o al IDE, comprueba que se compiló el
módulo editado, que la prueba ejecutada es la tuya (filtro `--tests`) y que no
existe otra ruta de código con el mismo defecto.

## Entrega a `code-review`

Incluye JDK y release, versión de Boot, stack imperativo o reactivo, si es
Scaffold, módulos y comandos ejecutados con su resultado, y qué integraciones se
probaron con dobles. Esta lista es tu auto-revisión; el revisor aplica su propio
criterio.
