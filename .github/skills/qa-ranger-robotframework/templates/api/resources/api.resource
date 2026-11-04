*** Settings ***
Documentation     Sesión HTTP y keywords de negocio de la API. Una sesión por API, creada en Suite Setup.
Library           RequestsLibrary
Library           Collections
Resource          common.resource

*** Keywords ***
Abrir Sesion De La Api
    [Documentation]    Crea la sesión ``api`` con TLS verificado y timeout del ambiente.
    Create Session    api    ${API_URL}    verify=${TLS_VERIFY}    timeout=${TIMEOUT}

Autenticar Sesion Con Token
    [Documentation]    Agrega el bearer token (desde el entorno) a todas las llamadas siguientes.
    Verificar Variables De Entorno    QA_API_TOKEN
    VAR    &{auth}    Authorization=Bearer %{QA_API_TOKEN}
    Update Session    api    headers=${auth}

Cerrar Sesiones
    Delete All Sessions

El Servicio Responde Saludable
    ${resp}=    GET On Session    api    __RUTA_SALUD__
    Status Should Be    200    ${resp}
    Should Be Equal As Strings    ${resp.json()}[status]    UP

Consultar Recurso Inexistente Devuelve 404
    [Arguments]    ${ruta}
    ${resp}=    GET On Session    api    ${ruta}    expected_status=404
    Dictionary Should Contain Key    ${resp.json()}    error
