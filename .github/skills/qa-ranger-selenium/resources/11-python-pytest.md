# 11 — Python con pytest

## Estructura
```
ui-tests-py/
├── requirements.txt           # selenium==4.50.0, pytest, pytest-xdist, pytest-html
├── pytest.ini
├── conftest.py                # fixture driver, config, evidencia en fallos
├── pages/
│   ├── login_page.py
│   └── transferencia_page.py
└── tests/
    └── test_transferencias.py
```

## pytest.ini
```ini
[pytest]
addopts = -ra --strict-markers --junitxml=reports/junit.xml
markers =
    smoke: pruebas críticas de cada despliegue
    regresion: suite completa
testpaths = tests
```

## conftest.py
```python
import os, pathlib, pytest
from selenium import webdriver

def pytest_addoption(parser):
    parser.addoption("--browser", default=os.getenv("BROWSER", "chrome"))
    parser.addoption("--base-url-app", default=os.getenv("BASE_URL", "http://localhost:3000"))
    parser.addoption("--grid-url", default=os.getenv("GRID_URL"))
    parser.addoption("--headed", action="store_true")

@pytest.fixture(scope="session")
def base_url(request):
    return request.config.getoption("--base-url-app").rstrip("/")

@pytest.fixture
def driver(request):
    opts = webdriver.ChromeOptions()
    if not request.config.getoption("--headed"):
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    grid = request.config.getoption("--grid-url")
    d = webdriver.Remote(command_executor=grid, options=opts) if grid else webdriver.Chrome(options=opts)
    d.implicitly_wait(0)
    yield d
    d.quit()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = (yield).get_result()
    if resultado.when == "call" and resultado.failed and "driver" in item.fixturenames:
        d = item.funcargs["driver"]
        carpeta = pathlib.Path("reports/evidencia"); carpeta.mkdir(parents=True, exist_ok=True)
        d.save_screenshot(str(carpeta / f"{item.name}.png"))
        (carpeta / f"{item.name}.html").write_text(d.page_source, encoding="utf-8")
```
El hook de evidencia corre **antes** del teardown de la fixture (el driver sigue vivo).

## Page object
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TransferenciaPage:
    CUENTA = (By.ID, "cuentaDestino")
    MONTO = (By.CSS_SELECTOR, "input[name='monto']")
    CONTINUAR = (By.XPATH, "//button[normalize-space()='Continuar']")
    CONFIRMAR = (By.XPATH, "//button[normalize-space()='Confirmar transferencia']")
    MENSAJE = (By.CSS_SELECTOR, "[role='alert']")

    def __init__(self, driver, base_url, espera=10):
        self.driver, self.base_url = driver, base_url
        self.wait = WebDriverWait(driver, espera)

    def abrir(self):
        self.driver.get(f"{self.base_url}/transferencias/nueva")
        self.wait.until(EC.visibility_of_element_located(self.CUENTA))
        return self

    def transferir(self, cuenta, monto):
        self._escribir(self.CUENTA, cuenta)
        self._escribir(self.MONTO, monto)
        self.driver.find_element(*self.CONTINUAR).click()
        self.wait.until(EC.element_to_be_clickable(self.CONFIRMAR)).click()
        return self.mensaje()

    def mensaje(self):
        return self.wait.until(lambda d: d.find_element(*self.MENSAJE).text.strip() or False)

    def _escribir(self, loc, valor):
        campo = self.wait.until(EC.element_to_be_clickable(loc))
        campo.clear(); campo.send_keys(valor)
```

## Tests
```python
import os, re, pytest

@pytest.mark.smoke
def test_hu245_ca1_transfiere_con_saldo_suficiente(sesion, transferencias):
    """[HU-245][CA-1] transfiere con saldo suficiente"""
    assert re.fullmatch(r"Transferencia exitosa\. Referencia REF-[0-9A-F]{6}", transferencias.transferir("00998877665", "150000"))

@pytest.mark.parametrize("caso,cuenta,monto,error", [
    ("monto cero", "00998877665", "0", "El monto debe ser mayor a cero"),
    ("cuenta de 10 digitos", "1234567890", "1000", "La cuenta destino debe tener 11 dígitos"),
], ids=lambda v: v if isinstance(v, str) and " " in v else None)
def test_hu245_ca2_rechaza_datos_invalidos(sesion, transferencias, caso, cuenta, monto, error):
    assert transferencias.transferir(cuenta, monto) == error
```
- Paralelo: `pytest -n 4` (pytest-xdist); cada test tiene su driver por la fixture de alcance `function`.
- Trazabilidad: el ID en el nombre de la función (`test_hu245_ca1_...`) llega al JUnit XML; `rtm_from_junit.py` reconoce `hu245_ca1` y `[HU-245][CA-1]`.
- Selenium 3 → 4 en Python: `find_element_by_id(...)` → `find_element(By.ID, ...)`; `executable_path=` → `Service(...)`.
