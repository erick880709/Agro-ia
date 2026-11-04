*** Settings ***
Documentation     Ciclo de vida del navegador con evidencia por caso (video, trace y screenshot, también en los exitosos).
...               Navegador por suite; contexto y página nuevos por test (aislamiento de cookies y storage).
Library           Browser    timeout=${TIMEOUT}
Resource          common.resource

*** Keywords ***
Abrir Navegador De La Suite
    New Browser    ${BROWSER}    headless=${HEADLESS}

Iniciar Caso Con Evidencia
    [Documentation]    Contexto nuevo con video y trace en la carpeta del caso; abre la URL base.
    ${carpeta}=    Carpeta De Evidencia Del Caso
    New Context    viewport={'width': 1280, 'height': 800}
    ...    recordVideo={'dir': '${carpeta}/_video'}    tracing=${carpeta}/trace.zip
    ${pagina}=    New Page    ${BASE_URL}
    VAR    ${VIDEO_DEL_CASO}    ${pagina}[video_path]    scope=TEST

Cerrar Caso Con Evidencia
    [Documentation]    Screenshot final, cierre del contexto (escribe video y trace) y video a la carpeta del caso.
    ${carpeta}=    Carpeta De Evidencia Del Caso
    Take Screenshot    ${carpeta}/screenshot
    Close Context
    Mover Video Al Caso    ${VIDEO_DEL_CASO}

Cerrar Navegador De La Suite
    Close Browser    ALL
