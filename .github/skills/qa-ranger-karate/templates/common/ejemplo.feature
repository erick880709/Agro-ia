@{{DOMAIN}} @regresion
Feature: {{DOMAIN}} — consulta de recurso
  # Plantilla de ejemplo: reemplazar ruta, esquema y casos por los del servicio real.

  Background:
    * url baseUrl
    * configure headers = read('classpath:common/headers.js')
    * def esquema = read('classpath:{{DOMAIN}}/schemas/recurso.json')
    * def esquemaError = read('classpath:common/schemas/error.json')

  @smoke
  Scenario: TC-API-01 [critical] consulta un recurso existente
    Given path '{{RESOURCE_PATH}}', 'ID-EXISTENTE'
    When method get
    Then status 200
    And match response == esquema

  @negativo
  Scenario: TC-API-02 [high] responde 404 para un recurso inexistente
    Given path '{{RESOURCE_PATH}}', 'NO-EXISTE-' + java.util.UUID.randomUUID().toString()
    When method get
    Then status 404
    And match response == esquemaError

  @seguridad
  Scenario: TC-API-03 [critical] rechaza peticiones sin token
    * configure headers = { 'X-Request-Id': '#(java.util.UUID.randomUUID().toString())' }
    Given path '{{RESOURCE_PATH}}', 'ID-EXISTENTE'
    When method get
    Then status 401
