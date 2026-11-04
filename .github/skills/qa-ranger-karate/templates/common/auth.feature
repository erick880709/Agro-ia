@ignore
Feature: obtiene token OAuth2 (client_credentials)
  # Entradas: tokenUrl, clientId, clientSecret, scope (opcional)
  # Salida:   token
  # karate-config.js llama a este archivo una vez por suite con karate.callSingle.

  Scenario:
    * url tokenUrl
    # Karate elimina la clave scope cuando '##(scope)' recibe null.
    * def campos = { grant_type: 'client_credentials', client_id: '#(clientId)', client_secret: '#(clientSecret)', scope: '##(scope)' }
    * form fields campos
    * method post
    * status 200
    * match response contains { access_token: '#string' }
    * def token = response.access_token
