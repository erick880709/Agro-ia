*** Settings ***
Documentation     Pruebas de aceptación de BD del release. Reemplazar tabla, columnas y reglas por las de la HU.
...               Solo lectura: el stage corre contra ambientes compartidos.
Resource          ../resources/connection_database.resource
Suite Setup       Conectar A La Base De Datos
Suite Teardown    Desconectar De La Base De Datos
Test Tags         database    acceptance

*** Variables ***
${REGISTRO_CONOCIDO}    __CLAVE_EJEMPLO__
${VALOR_ESPERADO}       __VALOR_EJEMPLO__

*** Test Cases ***
TC-01 [critical] La tabla principal existe en el esquema desplegado
    [Tags]    TC-01    smoke
    Table Must Exist    __TABLA__

TC-02 [high] Ningún registro queda sin el campo obligatorio
    [Tags]    TC-02
    ${filas}=    Query    SELECT COUNT(*) FROM __TABLA__ WHERE __COLUMNA__ IS NULL
    Should Be Equal As Integers    ${filas}[0][0]    0    Hay registros de __TABLA__ con __COLUMNA__ nulo

TC-03 [high] Un registro de referencia conserva su valor
    [Tags]    TC-03
    @{params}=    Create List    ${REGISTRO_CONOCIDO}
    ${filas}=    Query    SELECT __COLUMNA__ FROM __TABLA__ WHERE __CLAVE__ = __PH__    parameters=${params}
    Should Not Be Empty    ${filas}    No existe el registro de referencia ${REGISTRO_CONOCIDO}
    Should Be Equal As Strings    ${filas}[0][0]    ${VALOR_ESPERADO}
