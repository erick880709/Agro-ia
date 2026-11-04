# Criterios y escenarios BDD/Gherkin

Guía compartida para decidir cuándo usar BDD y escribir escenarios de negocio. La configuración, los steps y la captura de cada runner se mantienen en su especialista.

## Índice

- [Cuándo Usar BDD en Vez de Specs Directos](#cuándo-usar-bdd-en-vez-de-specs-directos)
- [Estructura de un `.feature`](#estructura-de-un-feature)
- [Step Definitions Reutilizables](#step-definitions-reutilizables)
- [Convención de Id de Caso](#convención-de-id-de-caso)
- [Gotchas de BDD](#gotchas-de-bdd)
- [Implementación por herramienta](#implementación-por-herramienta)

## Cuándo Usar BDD en Vez de Specs Directos

BDD agrega una capa de traducción (Gherkin → step definitions → código de
automatización) que cuesta mantenimiento extra. Usarlo cuando el beneficio
de legibilidad compensa ese costo:

- El equipo de negocio/QA manual participa activamente escribiendo o
  revisando escenarios en Gherkin.
- Hay un requisito de auditoría/compliance de que los casos de prueba sean
  legibles por no-técnicos (común en banca/seguros).
- El proyecto ya tiene una suite Cucumber existente — no forzar una
  reescritura a specs directos solo por preferencia.

Si ninguna de estas aplica, preferir specs directos (`test()`/`it()`) —
son más simples de mantener y depurar.

## Estructura de un `.feature`

```gherkin
# features/login.feature
Feature: Login de usuario

  Background:
    Given el usuario está en la página de login

  @TC-01 @critical
  Scenario: Login con credenciales válidas
    When ingresa un email y password válidos
    And hace clic en "Ingresar"
    Then es redirigido al dashboard
    And ve su nombre en el header

  @TC-02 @high
  Scenario Outline: Login con credenciales inválidas
    When ingresa el email "<email>" y password "<password>"
    And hace clic en "Ingresar"
    Then ve el mensaje de error "<mensaje>"

    Examples:
      | email                  | password    | mensaje                          |
      | usuario@example.com    | incorrecta  | Credenciales inválidas           |
      |                        | Password123 | Email requerido                  |
```

`Background` factoriza precondiciones comunes a todos los escenarios del
archivo. `Scenario Outline` + `Examples` reemplaza escribir el mismo
escenario para cada combinación de datos — igual función que un test
parametrizado.

## Step Definitions Reutilizables

- Un step genérico y parametrizado (`When ingresa el email "<email>" y
  password "<password>"`) es preferible a uno hardcodeado por escenario —
  reduce la cantidad de step definitions a mantener.
- No duplicar lógica entre steps: si dos steps hacen casi lo mismo,
  extraer un método/función común que ambos llamen.
- Evitar steps que dependan del orden de ejecución de otros escenarios —
  cada `Scenario` debe poder correr aislado (Regla de Oro 3).

## Convención de Id de Caso

Cada escenario conserva ID y prioridad (`@TC-01 @critical`). Verifica que el reporter los propague al CTRF y que los adjuntos correspondan al escenario y su intento. El formato Gherkin no acredita la ejecución ni genera evidencia por sí solo.

## Gotchas de BDD

- No escribir Gherkin que en realidad es un script paso a paso técnico
  (`When hago clic en el botón con id #submit-btn-2`) — si el escenario no
  es legible por alguien no técnico, BDD no está cumpliendo su propósito y
  probablemente convenga un spec directo.
- No reutilizar el mismo `.feature` para casos que en realidad prueban
  cosas distintas solo porque comparten un `Background` — separar por
  intención, no por conveniencia de setup.
- No dejar steps ambiguos que calcen con más de un texto de escenario —
  Cucumber falla la compilación o, peor, ejecuta el step equivocado.

## Implementación por herramienta

- [Playwright: generación y steps](../../../qa-ranger-playwright/references/15-bdd-gherkin.md).
- [Selenium Java: Cucumber y ciclo de vida](../../../qa-ranger-selenium/resources/13-bdd-gherkin.md).
- Para otras herramientas, conserva el adaptador instalado y verifica reportes y evidencia según la [guía común](../evidence_guide.md).
