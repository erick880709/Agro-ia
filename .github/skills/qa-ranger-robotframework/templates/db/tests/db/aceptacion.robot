*** Settings ***
Documentation     Aceptación de base de datos. Reemplazar tabla, columnas y reglas por las de la HU/modelo de datos.
Resource          ../../resources/db.resource
Suite Setup       Conectar A La Base De Datos
Suite Teardown    Desconectar De La Base De Datos
Test Tags         database

*** Test Cases ***
TC-01 [critical] La tabla principal existe en el esquema desplegado
    [Tags]    TC-01    smoke
    La Tabla Principal Existe

TC-02 [high] Ningún registro queda sin el campo obligatorio
    [Tags]    TC-02
    No Hay Registros Sin Campo Obligatorio

TC-03 [high] Un registro de referencia conserva su valor
    [Tags]    TC-03
    El Registro "${REGISTRO_CONOCIDO}" Tiene El Valor "${VALOR_ESPERADO}"
