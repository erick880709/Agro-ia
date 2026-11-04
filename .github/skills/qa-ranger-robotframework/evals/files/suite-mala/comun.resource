*** Settings ***
Library    DatabaseLibrary
Library    RequestsLibrary

*** Keywords ***
Conectar BD
    ${output}    Connect To Database    psycopg2    %{DB}    %{USER}    clave123    %{HOST}    %{PORT}
    Should Be Equal As Strings    ${output}    None
    [Return]    ${output}

Crear Sesion Api
    Create Session    api    https://api.qa.ejemplo.com
