*** Settings ***
Documentation     Conexión y verificaciones de aceptación de base de datos (DatabaseLibrary 2.x).
...               Solo lectura contra ambientes compartidos; parámetros enlazados, nunca SQL concatenado.
Library           DatabaseLibrary    log_query_results=False
Resource          common.resource

*** Keywords ***
Conectar A La Base De Datos
    [Documentation]    Valida las variables de entorno y abre la conexión ``default``.
__CONNECT__

Desconectar De La Base De Datos
    Disconnect From All Databases

La Tabla Principal Existe
    Table Must Exist    __TABLA__

No Hay Registros Sin Campo Obligatorio
    Check Row Count    SELECT 1 FROM __TABLA__ WHERE __COLUMNA__ IS NULL    ==    0
    ...    assertion_message=Hay registros de __TABLA__ con __COLUMNA__ nulo

El Registro "${clave}" Tiene El Valor "${esperado}"
    VAR    @{params}    ${clave}
    Check Query Result    SELECT __COLUMNA__ FROM __TABLA__ WHERE __CLAVE__ = __PH__    ==    ${esperado}
    ...    parameters=${params}    assert_as_string=True
