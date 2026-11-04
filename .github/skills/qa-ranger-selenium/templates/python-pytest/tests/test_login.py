import time

import pytest

from conftest import secreto
from pages.login_page import LoginPage


@pytest.mark.smoke
def test_hu000_ca1_ingresa_con_credenciales_validas(driver, base_url):
    """[HU-000][CA-1] ingresa con credenciales válidas"""
    login = LoginPage(driver, base_url).abrir().ingresar(secreto("E2E_USER"), secreto("E2E_PASSWORD"))
    assert login.en_inicio(), "debe mostrarse la página de inicio"


def test_hu000_ca2_rechaza_contrasena_incorrecta(driver, base_url):
    """[HU-000][CA-2] rechaza una contraseña incorrecta"""
    login = LoginPage(driver, base_url).abrir().intentar(secreto("E2E_USER"), f"incorrecta-{time.time_ns()}")
    assert login.error(), "debe mostrarse un mensaje de error"
    assert not login.en_inicio()
