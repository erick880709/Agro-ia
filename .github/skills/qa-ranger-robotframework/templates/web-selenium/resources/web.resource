*** Settings ***
Documentation     Ciclo de vida WebDriver con evidencia por caso: screenshot y traza diagnóstica (page source,
...               URL y consola). El video solo existe si la infraestructura lo graba (Grid/docker-selenium).
Library           SeleniumLibrary    timeout=${TIMEOUT}    implicit_wait=0s
Resource          common.resource

*** Keywords ***
Iniciar Caso Con Evidencia
    [Documentation]    Un navegador por test (aislamiento y paralelismo con pabot).
    Open Browser    ${BASE_URL}    ${BROWSER}    options=${OPCIONES}    remote_url=${GRID_URL}

Cerrar Caso Con Evidencia
    [Documentation]    Screenshot y traza también en los casos exitosos; luego cierra la sesión.
    ${carpeta}=    Carpeta De Evidencia Del Caso
    Capture Page Screenshot    ${carpeta}/screenshot.png
    Guardar Traza Selenium
    Close Browser

Cerrar Navegadores
    Close All Browsers
