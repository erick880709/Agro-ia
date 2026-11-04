# Revisión y antipatrones de pruebas unitarias

Prioriza cada hallazgo y acompáñalo de la corrección concreta.

| ID | Antipatrón | Severidad | Corrección |
|---|---|---|---|
| U1 | Prueba sin aserción | Bloqueante | Comprobar el resultado esperado del requisito |
| U2 | `try/catch` que convierte cualquier excepción en fallo o la silencia | Bloqueante | `assert.throws`/`expect().toThrow` o dejar que la excepción falle la prueba |
| U3 | Dependencia del orden o de estado compartido mutable | Bloqueante | Datos propios por prueba; `beforeEach` en lugar de variables de módulo |
| U4 | Espera fija (`setTimeout`, `sleep`) | Mayor | Esperar la promesa o usar temporizadores falsos |
| U5 | Reloj, red o aleatoriedad reales | Mayor | Inyectar o simular la dependencia |
| U6 | Aserción débil (`ok(valor)`, `toBeTruthy`) donde hay un valor esperado | Mayor | Comparar el valor exacto o el objeto completo |
| U7 | Prueba omitida (`skip`, `xit`, `@Disabled`) sin motivo ni pendiente | Mayor | Rehabilitar o registrar el motivo y el responsable |
| U8 | Simular la unidad bajo prueba o sus funciones internas | Mayor | Simular solo dependencias externas |
| U9 | Aserción que repite la fórmula de la implementación | Mayor | Comparar con un valor calculado a mano desde el requisito |
| U10 | Nombre genérico (`funciona`, `test1`) sin ID de caso | Menor | `UT-<n> [prioridad] [requisito] <comportamiento>` |
| U11 | Varias acciones y comportamientos en una prueba | Menor | Separar en casos con una razón para fallar |
| U12 | Archivos de prueba dentro de la medición de cobertura | Menor | Excluirlos en la herramienta o con `--exclude` |

## Checklist

- [ ] Cada requisito del alcance tiene caso o exclusión justificada.
- [ ] Cada caso tiene ID, prioridad y aserción sobre el resultado esperado.
- [ ] Los rechazos comprueban tipo o mensaje del error.
- [ ] Los límites prueban ambos lados del umbral.
- [ ] Ninguna prueba depende de otra, del reloj real ni de la red.
- [ ] Las pruebas omitidas tienen motivo y pendiente.
- [ ] La suite pasa al ejecutarla en orden aleatorio o aislada, si el runner lo permite.
- [ ] La cobertura excluye archivos de prueba y mide solo el nivel unitario.

Una revisión terminada puede concluir que la suite no es confiable. Si no se pudo
ejecutar, dilo: los hallazgos estáticos no acreditan resultados del runner.
