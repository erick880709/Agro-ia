*** Settings ***
Documentation     Page object de login. Localizadores TODO(verificar-locator) se confirman contra el DOM real.
Resource          ../web.resource

*** Variables ***
${CAMPO_USUARIO}      id:__CAMPO_USUARIO__    # TODO(verificar-locator)
${CAMPO_CLAVE}        id:__CAMPO_CLAVE__    # TODO(verificar-locator)
${BOTON_INGRESAR}     xpath://button[normalize-space()="__BOTON_INGRESAR__"]    # TODO(verificar-locator)
${TITULO_INICIO}      xpath://h1[normalize-space()="__HEADING_INICIO__"]    # TODO(verificar-locator)
${MENSAJE_ERROR}      css:[role="alert"]    # TODO(verificar-locator)

*** Keywords ***
Ir Al Login
    Go To    ${BASE_URL}__RUTA_LOGIN__
    Wait Until Element Is Visible    ${CAMPO_USUARIO}

Ingresar Con Usuario "${usuario}" Y Clave "${clave}"
    Input Text    ${CAMPO_USUARIO}    ${usuario}
    Input Password    ${CAMPO_CLAVE}    ${clave}
    Wait Until Element Is Enabled    ${BOTON_INGRESAR}
    Click Element    ${BOTON_INGRESAR}

Debe Ver El Inicio
    Wait Until Element Is Visible    ${TITULO_INICIO}

Debe Ver Un Error De Acceso
    Wait Until Element Is Visible    ${MENSAJE_ERROR}
    Location Should Contain    __RUTA_LOGIN__
