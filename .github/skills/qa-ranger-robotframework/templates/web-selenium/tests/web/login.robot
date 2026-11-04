*** Settings ***
Documentation     Login. Reemplazar reglas y datos por los de la HU; sin credenciales en este archivo.
Resource          ../../resources/web.resource
Resource          ../../resources/pages/login.resource
Test Setup        Iniciar Caso Con Evidencia
Test Teardown     Cerrar Caso Con Evidencia
Suite Teardown    Cerrar Navegadores
Test Tags         web    login

*** Test Cases ***
TC-01 [critical] Un usuario autorizado ingresa y ve el inicio
    [Tags]    TC-01    smoke
    Ir Al Login
    Ingresar Con Usuario "%{E2E_USER}" Y Clave "%{E2E_PASSWORD}"
    Debe Ver El Inicio

TC-02 [high] Una clave incorrecta muestra error y conserva el login
    [Tags]    TC-02
    Ir Al Login
    Ingresar Con Usuario "%{E2E_USER}" Y Clave "%{QA_CLAVE_INVALIDA}"
    Debe Ver Un Error De Acceso
