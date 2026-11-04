# Patrones de Appium (Testing Móvil Android/iOS)

Reference para automatizar apps móviles **nativas o híbridas**, no para un
sitio web responsive (eso sigue siendo Playwright/Cypress con emulación de
viewport — ver `../test_automation_patterns.md`). Usar este playbook solo
cuando el Paso 0.1 de `../../SKILL.md` confirma que el proyecto es una app
móvil (React Native, Flutter, Android/iOS nativo) o el usuario lo pide
explícitamente.

Appium normalmente se usa con Python (más común en la comunidad Appium) o
JS/WebdriverIO. Este reference cubre Python, que es el setup más
documentado; para JS ver la sección final.

---

## Índice

- [Prerrequisito: Dispositivo/Emulador/Simulador Real](#prerrequisito-dispositivoemuladorsimulador-real)
- [Setup Python](#setup-python)
- [Capabilities Android/iOS](#capabilities-androidios)
- [Page Object Model Móvil](#page-object-model-móvil)
- [Gestos W3C](#gestos-w3c)
- [Appium Inspector y Estrategia de Locators](#appium-inspector-y-estrategia-de-locators)
- [Evidencia (Allure)](#evidencia-allure)
- [Appium en JS (WebdriverIO)](#appium-en-js-webdriverio)
- [CI](#ci)
- [Convención de Id de Caso](#convención-de-id-de-caso)

---

## Prerrequisito: Dispositivo/Emulador/Simulador Real

**No generar specs de Appium sin confirmar primero que hay algo real donde
correrlos** — un emulador Android (AVD), un simulador iOS, un dispositivo
físico conectado, o un device farm en la nube al que el proyecto ya tiene
acceso. Un spec de Appium que nadie puede ejecutar no es evidencia de
nada; preguntar al usuario qué entorno tiene disponible antes de escribir
el primer test.

## Setup Python

```bash
pip install Appium-Python-Client pytest pytest-html Appium
npm install -g appium
appium driver install uiautomator2   # Android
appium driver install xcuitest       # iOS (requiere macOS + Xcode)
appium  # levanta el servidor Appium, por defecto en localhost:4723
```

## Capabilities Android/iOS

```python
# config/capabilities.py
import os

ANDROID_CAPS = {
    "platformName": "Android",
    "automationName": "UiAutomator2",
    "deviceName": os.getenv("QA_ANDROID_DEVICE", "emulator-5554"),
    "app": os.getenv("QA_ANDROID_APP_PATH"),  # ruta al .apk
    "autoGrantPermissions": True,
}

IOS_CAPS = {
    "platformName": "iOS",
    "automationName": "XCUITest",
    "deviceName": os.getenv("QA_IOS_DEVICE", "iPhone 15"),
    "platformVersion": os.getenv("QA_IOS_VERSION", "17.5"),
    "app": os.getenv("QA_IOS_APP_PATH"),  # ruta al .app/.ipa
}
```

```python
# conftest.py
import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from config.capabilities import ANDROID_CAPS

@pytest.fixture
def android_driver():
    options = UiAutomator2Options().load_capabilities(ANDROID_CAPS)
    driver = webdriver.Remote("http://localhost:4723", options=options)
    yield driver
    driver.quit()
```

## Page Object Model Móvil

```python
from appium.webdriver.common.appiumby import AppiumBy

class LoginPage:
    def __init__(self, driver):
        self.driver = driver

    def login(self, email, password):
        self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, "email-input").send_keys(email)
        self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, "password-input").send_keys(password)
        self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, "login-button").click()
```

`AppiumBy.ACCESSIBILITY_ID` (equivalente al locator por rol/label del
resto del skill) es la primera opción — depende de que la app tenga
`accessibilityLabel`/`contentDescription` seteados; si no los tiene,
señalarlo como hallazgo de accesibilidad además de usar un locator más
frágil como fallback.

## Gestos W3C

```python
from appium.webdriver.common.touch_action import TouchAction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

def swipe_up(driver, start_y=1500, end_y=500, x=540, duration_ms=400):
    actions = ActionBuilder(driver, mouse=PointerInput(PointerInput.POINTER_TOUCH, "touch"))
    actions.pointer_action.move_to_location(x, start_y)
    actions.pointer_action.pointer_down()
    actions.pointer_action.move_to_location(x, end_y)
    actions.pointer_action.release()
    actions.perform()
```

Gestos cubiertos habitualmente: swipe (arriba/abajo/lateral), scroll hasta
un elemento, long press, double tap, drag & drop, pinch/zoom — todos vía
la W3C Actions API, no la `TouchAction` legacy (deprecada en Appium 2.x).

## Appium Inspector y Estrategia de Locators

Antes de automatizar un flujo nuevo, usar **Appium Inspector** (app
gráfica separada) conectado al mismo servidor Appium para:

1. Inspeccionar el árbol de accesibilidad de la pantalla real.
2. Validar que el locator elegido (`Accessibility ID` > `UIAutomator
   Selector`/`iOS Predicate String` > `Class Chain` > XPath) resuelve al
   elemento correcto antes de escribirlo en el spec — evita el ciclo de
   prueba-error corriendo el test completo por cada ajuste de locator.

## Evidencia (Allure)

```python
import allure

@allure.epic("Login")
@allure.story("TC-01")
def test_login_con_credenciales_validas(android_driver):
    with allure.step("Ingresar credenciales"):
        LoginPage(android_driver).login(email, password)
    with allure.step("Verificar dashboard"):
        assert android_driver.find_element(AppiumBy.ACCESSIBILITY_ID, "dashboard-title").is_displayed()
```

```python
# conftest.py — screenshot automático en fallo
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        driver = item.funcargs.get("android_driver") or item.funcargs.get("ios_driver")
        if driver:
            allure.attach(driver.get_screenshot_as_png(), name="failure", attachment_type=allure.attachment_type.PNG)
```

```bash
pytest --alluredir=resources/qa/appium-results/<runId>
allure generate resources/qa/appium-results/<runId> --clean -o resources/qa/reports/<runId>/allure-report
```

Organizar manualmente bajo `resources/qa/<runId>/` siguiendo la
misma convención del resto del skill — el kit todavía no convierte
estos resultados a CTRF.

## Appium en JS (WebdriverIO)

Si el equipo prefiere quedarse en npm:

```typescript
// wdio.conf.ts
export const config: WebdriverIO.Config = {
  services: ['appium'],
  capabilities: [{
    platformName: 'Android',
    'appium:automationName': 'UiAutomator2',
    'appium:app': process.env.QA_ANDROID_APP_PATH,
  }],
};
```

Mismos principios (locators de accesibilidad, gestos vía Actions API, sin
sleeps duros) con la sintaxis de WebdriverIO.

## CI

Requiere un runner con emuladores/simuladores disponibles — típicamente
`macos-latest` para iOS (Xcode preinstalado) y una acción de emulador
Android para Android:

```yaml
# GitHub Actions, fragmento Android
- uses: reactivecircus/android-emulator-runner@v2
  with:
    api-level: 34
    script: pytest --alluredir=resources/qa/appium-results/${{ github.run_id }}
```

## Convención de Id de Caso

Igual convención que el resto del skill: `@allure.story("TC-01")` o en el
nombre del test (`test_TC01_login_credenciales_validas`), según lo que el
proyecto ya use para navegar el reporte Allure.
