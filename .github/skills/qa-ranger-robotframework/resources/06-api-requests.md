# 06 — API con RequestsLibrary

## 1. Sesión

```robotframework
*** Settings ***
Library           RequestsLibrary
Suite Setup       Create Session    api    ${API_URL}    verify=${TLS_VERIFY}    timeout=${TIMEOUT}
Suite Teardown    Delete All Sessions
```

- `Create Session` **no verifica TLS por defecto** (`verify=False`): pasa `verify=${True}` o la ruta del bundle CA corporativo.
- Las sesiones son globales: créalas en Suite Setup y bórralas en el teardown.
- Llamadas con ruta: `GET On Session    api    /cuentas/0001`.

## 2. Respuestas y negativos

- Toda llamada sin `expected_status` falla con 4xx/5xx. Negativos: `expected_status=404` (un código, un nombre o `any`; no rangos tipo `2xx`).
- `Status Should Be    201    ${resp}` (el estado va primero). Cuerpo: `${resp.json()}[campo]`; cabeceras: `${resp.headers}[Content-Type]`.
- `json=${dict}` envía JSON; `data=` envía formulario. Números como `${1}`, no `"1"`.
- `=` en la URL se interpreta como argumento nombrado: usa `params=${query}`.

## 3. Autenticación

Token desde el entorno, nunca en el `.robot`:

```robotframework
Autenticar Sesion Con Token
    Verificar Variables De Entorno    QA_API_TOKEN
    VAR    &{auth}    Authorization=Bearer %{QA_API_TOKEN}
    Update Session    api    headers=${auth}
```

Básica/digest/NTLM/certificado: `Create Session … auth=`, `Create Digest Session`, `Create Ntlm Session`, `Create Client Cert Session`.

## 4. Contrato y RESTinstance

Para validar contra JSON Schema/OpenAPI usa RESTinstance (`Library    REST    ${API_URL}`; Python ≥ 3.11) o valida el esquema en una keyword Python. Prefijo de casos de API: `API-`; seguridad: `SEC-`; fraude/abuso: `FRAUD-` (playbooks de Ranger). Idempotencia y doble envío se prueban con llamadas repetidas reales, no con mocks del servicio bajo prueba.
