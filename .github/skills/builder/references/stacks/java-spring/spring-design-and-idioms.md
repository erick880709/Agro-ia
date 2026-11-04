# Diseño e idiomas Java / Spring

## Ubicación

| Proyecto | Cómo extender |
|---|---|
| Scaffold de Bancolombia | Entidad/valor y puerto en `domain/model` (`.../gateways`); caso de uso en `domain/usecase` con nombre terminado en `UseCase` (lo registra `app-service`); tecnología en `infrastructure/driven-adapters` o `entry-points`; cableado solo en `applications/app-service` |
| Hexagonal o por capas propio | Respeta la dirección de dependencias y los nombres existentes (`port`, `adapter`, `application`, `infrastructure`) |
| Por feature (`order/`, `customer/`) | Añade al paquete de la feature; visibilidad de paquete para lo interno |
| Por capa técnica (`controller/`, `service/`) | Extiende igual; no reorganices a feature dentro de una tarea |

Reglas comunes:

- `model` y `usecase` son Java puro: sin Spring, Jakarta, Lombok fuera de lo que
  el proyecto ya permita en dominio, ni clases de adaptadores. El oráculo de
  Builder compila `usecase` solo con `model` en el classpath: cualquier
  `@Service`, `@Transactional` o import de un adaptador ahí rompe la regla.
- Nombres de dominio sin sufijos técnicos (`Dto`, `Request`, `Response`) ni
  tecnologías (`Kafka`, `Dynamo`, `Postgres`...) en el Scaffold.
- No crees paquetes `utils`/`common` para lógica de dominio; los `helpers` del
  Scaffold son para utilidades técnicas de adaptadores.

## Inyección y beans

- Inyección por constructor con campos `private final`. Con Lombok, usa la
  anotación que ya usa el proyecto (`@RequiredArgsConstructor`); sin Lombok,
  constructor explícito. Nunca `@Autowired` en campos en código nuevo.
- `@Value` solo como parámetro del constructor (regla del Scaffold) o, mejor,
  `@ConfigurationProperties` en un record validado (`@Validated`) cuando la
  configuración tiene varios campos.
- Estereotipos según el rol (`@RestController`, `@Repository`, `@Component`);
  en el Scaffold los casos de uso no llevan estereotipo.
- Beans sin estado mutable compartido; si es inevitable, sincronización explícita.
- Evita `@Lazy`, `ApplicationContext.getBean` y ciclos de dependencias; un ciclo
  indica una responsabilidad mal ubicada.

## Modelado

- `record` para valores inmutables, comandos, eventos y DTO de entrada/salida
  (Java 16+). Valida invariantes en el constructor compacto o en una fábrica.
- Entidades JPA no son modelos de dominio ni DTO: en el Scaffold viven en el
  adaptador (`*Data`) con mapeo explícito; fuera de él, al menos no se exponen
  por la API.
- Dinero con `BigDecimal` (nunca `double`/`float`), escala y `RoundingMode`
  explícitos, redondeo solo donde la regla lo diga; compara con `compareTo`, no
  con `equals` (que considera la escala). Tiempo con `java.time` e `Instant`/
  `OffsetDateTime` en límites; zona horaria explícita.
- `Optional` solo como tipo de retorno; no en campos, parámetros ni colecciones.
- Colecciones devueltas inmutables (`List.copyOf`) o copiadas; no expongas
  estructuras internas mutables. No modifiques colecciones recibidas como
  argumento.
- `sealed` + `record` para jerarquías cerradas (17+); el `switch` con patrones
  sobre ellas requiere Java 21.

## Errores

- Errores de negocio como excepciones de dominio con un tipo o código estable
  (en el Scaffold, `BusinessException` + enum de tipos, si existe). Errores
  técnicos separados y traducidos en el adaptador; no dejes escapar
  `SQLException`, `WebClientResponseException` o excepciones de SDK al dominio.
- No captures `Exception` para silenciarla ni registres y relances el mismo
  error (log en el límite). Conserva la causa (`new X(msg, cause)`).
- El mapeo a HTTP ocurre en el entry point (`@RestControllerAdvice` o handler de
  errores WebFlux) con un formato estable (`ProblemDetail` en Boot 3+ si el
  proyecto no tiene otro), sin trazas ni mensajes internos.
- Crear, renombrar o cambiar el significado de un código de error consumido por
  canales es cambio de contrato.

## Mapeo y Lombok

- Mapeo con el mecanismo existente (MapStruct, métodos `toDomain`/`fromDomain`,
  mappers manuales). En MapStruct, `unmappedTargetPolicy` del proyecto; revisa
  que los campos nuevos se mapeen en ambos sentidos.
- Lombok solo si el proyecto lo usa y con su `lombok.config`. En entidades JPA
  evita `@Data`/`@EqualsAndHashCode` sobre relaciones (bucles y cargas
  perezosas); en records no hace falta.

## Configuración

- Propiedades en `application.yaml` con perfiles existentes; nada secreto en el
  repositorio. Secretos vía el mecanismo del proyecto (en el Scaffold, `gda
  --type=secrets` con AWS Secrets Manager o Vault).
- Propiedades nuevas con valor por defecto seguro o falla rápida al arrancar, y
  documentadas en el archivo de configuración del proyecto.
- No cambies propiedades globales (pool, timeouts, `open-in-view`, Jackson) como
  efecto colateral de una feature.

## Concurrencia

- Estado compartido con `java.util.concurrent` (`ConcurrentHashMap`,
  atómicos) u operaciones atómicas en el almacén; check-then-act sobre un
  almacén compartido es una carrera aunque cada llamada sea segura.
- Virtual threads (`spring.threads.virtual.enabled`, Boot 3.2+ con Java 21)
  solo si el proyecto ya los usa; no los actives en una feature.
- `@Async` y `@Scheduled` requieren ejecutor configurado, manejo de errores y
  límites; en varias réplicas, un `@Scheduled` se ejecuta en todas.
