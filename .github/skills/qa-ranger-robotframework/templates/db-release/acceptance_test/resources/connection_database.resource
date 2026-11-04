*** Settings ***
Documentation     Conexión estándar del stage "Acceptance Test" (pool de agentes Linux).
...               Las variables del pipeline llegan como variables de entorno en MAYÚSCULA: DB, HOST, PORT, USER, PASSWORD.
...               Sintaxis compatible con RF 5+ y DatabaseLibrary 1.x/2.x (argumentos posicionales), porque la
...               versión que trae la tarea RobotFramework-DBLibrary del agente se verifica, no se supone.
Library           DatabaseLibrary
Library           ../libraries/QaEvidencia.py

*** Variables ***
${DBName}         %{DB}
${DBHost}         %{HOST}
${DBPort}         %{PORT}
${DBUser}         %{USER}
${DBPass}         %{PASSWORD}

*** Keywords ***
Conectar A La Base De Datos
    [Documentation]    Falla con un mensaje claro si una variable falta o conserva el valor del agente
    ...    (p. ej. %{USER} = usuario del sistema porque el secreto no se inyectó).
    Verificar Variables De Entorno    DB    HOST    PORT    USER    PASSWORD
    Connect To Database    __DB_MODULE__    ${DBName}    ${DBUser}    ${DBPass}    ${DBHost}    ${DBPort}

Desconectar De La Base De Datos
    Disconnect From Database
