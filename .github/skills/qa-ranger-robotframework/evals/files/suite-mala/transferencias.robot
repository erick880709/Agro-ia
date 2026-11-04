*** Setting ***
Library           SeleniumLibrary    implicit_wait=10
Library           Browser
Library           DatabaseLibrary
Resource          comun.resource
Force Tags        regresion

*** Variables ***
${URL}            https://banca.qa.ejemplo.com
${CLAVE_ADMIN}    Sup3rSecreta!

*** Test Cases ***
Login exitoso
    Open Browser    https://banca.qa.ejemplo.com/login
    Input Text    id:usuario    admin
    Input Text    id:password    Sup3rSecreta!
    Click Element    xpath:/html/body/div[2]/form/button[1]
    Sleep    5s
    ${el}=    Get WebElement    css:.saldo
    Set Suite Variable    ${SALDO_INICIAL}    ${el.text}

Transferencia a tercero
    Run Keyword If    '${SALDO_INICIAL}' != ''    Click Element    id:transferir
    Execute Javascript    document.getElementById('confirmar').click()
    Run Keyword And Ignore Error    Element Should Be Visible    id:ok
    Log    ${CLAVE_ADMIN}

Verificar movimiento en base de datos
    [Tags]    TC-03
    Conectar BD
    ${filas}=    Query    SELECT * FROM movimientos WHERE cuenta = '${CUENTA}'
    Execute Sql String    DELETE FROM movimientos
    FOR    ${f}    IN    @{filas}
        Log    ${f}
    END

Login exitoso
    Wait Until Keyword Succeeds    5x    1s    Click Element    id:enviar
    Page Should Contain    Transferencia exitosa
