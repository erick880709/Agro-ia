"""Fixtures: configuración, un navegador por test y evidencia al fallar."""
import os
import pathlib
import re

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


def pytest_addoption(parser):
    parser.addoption("--env", default=os.getenv("TEST_ENV", "__ENV__"))
    parser.addoption("--base-url-app", default=os.getenv("BASE_URL", "__BASE_URL__"))
    parser.addoption("--grid-url", default=os.getenv("GRID_URL"))
    parser.addoption("--headed", action="store_true")


@pytest.fixture(scope="session")
def base_url(request):
    return request.config.getoption("--base-url-app").rstrip("/")


def secreto(variable: str) -> str:
    """Secretos SOLO desde variables de entorno."""
    valor = os.getenv(variable)
    if not valor:
        raise RuntimeError(f"Falta la variable de entorno {variable}")
    return valor


@pytest.fixture
def driver(request):
    opciones = webdriver.ChromeOptions()
    if not request.config.getoption("--headed"):
        opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1920,1080")
    opciones.add_argument("--lang=es-CO")
    if os.getenv("CHROME_BINARY"):                 # opcional: navegador corporativo/portable
        opciones.binary_location = os.environ["CHROME_BINARY"]
    if os.getenv("CONTAINER") == "true":
        opciones.add_argument("--no-sandbox")
        opciones.add_argument("--disable-dev-shm-usage")
    grid = request.config.getoption("--grid-url")
    if grid:
        d = webdriver.Remote(command_executor=grid, options=opciones)
    else:
        # Selenium Manager resuelve el driver; CHROMEDRIVER_PATH solo si la política lo exige
        servicio = Service(os.environ["CHROMEDRIVER_PATH"]) if os.getenv("CHROMEDRIVER_PATH") else Service()
        d = webdriver.Chrome(service=servicio, options=opciones)
    d.implicitly_wait(0)                           # solo esperas explícitas
    yield d
    d.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Screenshot + page source en el momento del fallo (antes del teardown del driver)."""
    resultado = (yield).get_result()
    if resultado.when == "call" and resultado.failed and "driver" in item.fixturenames:
        d = item.funcargs["driver"]
        carpeta = pathlib.Path("reports/evidencia")
        carpeta.mkdir(parents=True, exist_ok=True)
        nombre = re.sub(r"[^A-Za-z0-9._-]+", "_", item.nodeid)
        try:
            d.save_screenshot(str(carpeta / f"{nombre}.png"))
            (carpeta / f"{nombre}.html").write_text(f"<!-- {d.current_url} -->\n{d.page_source}", encoding="utf-8")
        except Exception as e:  # la evidencia nunca debe ocultar el fallo original
            item.add_report_section("call", "evidencia", f"no se pudo capturar evidencia: {e}")
