*** Settings ***
Documentation     Page object de login. Los selectores marcados TODO(verificar-locator) se confirman contra el DOM real.
Resource          ../web.resource

*** Variables ***
${CAMPO_USUARIO}      id=__CAMPO_USUARIO__    # TODO(verificar-locator)
${CAMPO_CLAVE}        id=__CAMPO_CLAVE__    # TODO(verificar-locator)
${BOTON_INGRESAR}     role=button[name="__BOTON_INGRESAR__"]    # TODO(verificar-locator)
${TITULO_INICIO}      role=heading[name="__HEADING_INICIO__"]    # TODO(verificar-locator)
${MENSAJE_ERROR}      role=alert    # TODO(verificar-locator)

*** Keywords ***
Ir Al Login
    Go To    ${BASE_URL}__RUTA_LOGIN__
    Wait For Elements State    ${CAMPO_USUARIO}    visible

Ingresar Con Usuario "${usuario}" Y Clave Del Entorno "${variable_clave}"
    [Documentation]    La clave se lee del entorno por nombre (Fill Secret no la registra en el log).
    Fill Text    ${CAMPO_USUARIO}    ${usuario}
    Fill Secret    ${CAMPO_CLAVE}    %${variable_clave}
    Click    ${BOTON_INGRESAR}

Debe Ver El Inicio
    Get Element States    ${TITULO_INICIO}    contains    visible

Debe Ver Un Error De Acceso
    Get Element States    ${MENSAJE_ERROR}    contains    visible
    Get Url    contains    __RUTA_LOGIN__
