# Diseño de casos unitarios

## Qué es una unidad

Una función, clase o módulo cuyo comportamiento se comprueba en memoria. Una prueba
que abre una base de datos, llama a la red o levanta un servidor es de integración:
no cuenta en la cobertura unitaria.

## Técnicas

| Técnica | Cuándo | Ejemplo |
|---|---|---|
| Partición de equivalencia | Entradas que el código trata igual | Cliente oro, plata, estándar, desconocido |
| Valores límite | Umbrales numéricos o de longitud | 9, 10, 49, 50, 99, 100 unidades |
| Caminos de error | Validaciones y excepciones | Cantidad 0, cantidad decimal, precio negativo |
| Tabla de decisión | Reglas que se combinan | Volumen + cliente + cupón por encima del tope |
| Transición de estado | Objetos con estados | Pedido creado → pagado → anulado |

Cubre cada requisito con al menos un caso y cada rama con el caso que la justifica.
Una rama sin requisito que la explique es una pregunta para el equipo, no un caso inventado.

## Estructura de cada prueba

- **Arrange-Act-Assert**: preparar, ejecutar una sola acción, comprobar.
- Una razón para fallar por prueba. Varios `assert` sobre el mismo resultado son válidos.
- Compara el objeto completo cuando sea posible (`deepEqual`, `toEqual`) en lugar
  de comprobar solo que existe un valor.
- Para errores, comprueba el tipo o el mensaje (`assert.throws(fn, /Cupón vencido/)`),
  no solo que "algo falló".

## Trazabilidad

Nombre: `UT-<n> [<prioridad>] [<ID de requisito>] <comportamiento esperado>`.
La prioridad usa los valores de la política QA (`critical`, `high`, `medium`, `low`).
Los IDs de requisitos solo se añaden si existen en las fuentes. El mismo `UT-<n>`
aparece en el plan, en el JUnit y en `execution.cases` del resultado.

## Dobles de prueba

| Doble | Uso |
|---|---|
| Stub | Devuelve un valor fijo de una dependencia |
| Mock | Comprueba que se llamó a una dependencia con ciertos argumentos |
| Fake | Implementación simplificada en memoria (repositorio, cola) |
| Spy | Registra llamadas sobre la implementación real |

Simula solo lo que está fuera de la unidad: reloj, aleatoriedad, red, disco, base
de datos y servicios externos. Simular la propia unidad o sus funciones internas
produce pruebas que pasan aunque el comportamiento esté roto.

## Determinismo

- Reloj: inyecta la fecha o usa los temporizadores falsos del runner
  (`vi.useFakeTimers`, `jest.useFakeTimers`, `mock.timers` en `node:test`, `freezegun`).
- Aleatoriedad: inyecta la semilla o el generador.
- Sin esperas fijas (`setTimeout`, `sleep`): espera la promesa o avanza el reloj falso.
- Sin estado compartido mutable entre pruebas; cada prueba crea sus datos.
- El orden de ejecución no cambia el resultado.

## Subir cobertura con valor

1. Mide la línea base con los archivos de prueba excluidos.
2. Lista las líneas y ramas sin cubrir y relaciona cada una con un requisito.
3. Prioriza rechazos, límites y reglas de dinero antes que getters o logs.
4. Vuelve a medir. Si una rama no es alcanzable sin cambiar el código, regístrala
   como hallazgo en lugar de forzarla.
