from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# TODO(verificar-locator): ajustar a la pantalla real (scripts/explorar_pagina.py o DevTools).
class LoginPage:
    USUARIO = (By.NAME, "__CAMPO_USUARIO__")
    CLAVE = (By.NAME, "__CAMPO_CLAVE__")
    INGRESAR = (By.XPATH, "//button[normalize-space()='__BOTON_INGRESAR__']")
    ERROR = (By.CSS_SELECTOR, "[role='alert']")
    INICIO = (By.XPATH, "//h1[normalize-space()='__HEADING_INICIO__']")

    def __init__(self, driver, base_url, espera=10):
        self.driver, self.base_url = driver, base_url
        self.wait = WebDriverWait(driver, espera)

    def abrir(self):
        self.driver.get(f"{self.base_url}__RUTA_LOGIN__")
        self.wait.until(EC.visibility_of_element_located(self.USUARIO))
        return self

    def ingresar(self, usuario, clave):
        """Inicia sesión y espera la página de inicio."""
        self.intentar(usuario, clave)
        self.wait.until(EC.visibility_of_element_located(self.INICIO))
        return self

    def intentar(self, usuario, clave):
        """Envía credenciales sin asumir el resultado (casos negativos)."""
        self._escribir(self.USUARIO, usuario)
        self._escribir(self.CLAVE, clave)
        self.driver.find_element(*self.INGRESAR).click()
        return self

    def error(self):
        return self.wait.until(EC.visibility_of_element_located(self.ERROR)).text.strip()

    def en_inicio(self):
        return bool(self.driver.find_elements(*self.INICIO))

    def _escribir(self, localizador, valor):
        campo = self.wait.until(EC.element_to_be_clickable(localizador))
        campo.clear()
        campo.send_keys(valor)
