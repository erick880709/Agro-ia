*** Settings ***
Documentation     Pruebas de API de ejemplo. Reemplazar rutas y reglas por las del contrato real (OpenAPI/HU).
Resource          ../../resources/api.resource
Suite Setup       Abrir Sesion De La Api
Suite Teardown    Cerrar Sesiones
Test Tags         api

*** Test Cases ***
API-01 [critical] El servicio reporta estado UP
    [Tags]    API-01    smoke
    El Servicio Responde Saludable

API-02 [high] Un recurso inexistente responde 404 con cuerpo de error
    [Tags]    API-02
    Consultar Recurso Inexistente Devuelve 404    /recursos/no-existe-0000
