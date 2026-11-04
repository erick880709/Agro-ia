package __PKG__.pages;

import __PKG__.config.Config;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

// TODO(verificar-locator): ajustar a la pantalla real (explorar con scripts/explorar_pagina.py o DevTools).
public class LoginPage {
  private static final By USUARIO = By.name("__CAMPO_USUARIO__");
  private static final By CLAVE = By.name("__CAMPO_CLAVE__");
  private static final By INGRESAR = By.xpath("//button[normalize-space()='__BOTON_INGRESAR__']");
  private static final By ERROR = By.cssSelector("[role='alert']");
  private static final By INICIO = By.xpath("//h1[normalize-space()='__HEADING_INICIO__']");

  private final WebDriver driver;
  private final WebDriverWait wait;

  public LoginPage(WebDriver driver) {
    this.driver = driver;
    this.wait = new WebDriverWait(driver, Config.espera());
  }

  public LoginPage abrir() {
    driver.get(Config.baseUrl() + "__RUTA_LOGIN__");
    wait.until(ExpectedConditions.visibilityOfElementLocated(USUARIO));
    return this;
  }

  /** Inicia sesión y espera la página de inicio. */
  public void ingresar(String usuario, String clave) {
    intentar(usuario, clave);
    wait.until(ExpectedConditions.visibilityOfElementLocated(INICIO));
  }

  /** Envía credenciales sin asumir el resultado (para casos negativos). */
  public LoginPage intentar(String usuario, String clave) {
    escribir(USUARIO, usuario);
    escribir(CLAVE, clave);
    driver.findElement(INGRESAR).click();
    return this;
  }

  public String error() {
    return wait.until(ExpectedConditions.visibilityOfElementLocated(ERROR)).getText().trim();
  }

  public boolean enInicio() {
    return !driver.findElements(INICIO).isEmpty();
  }

  private void escribir(By campo, String valor) {
    WebElement e = wait.until(ExpectedConditions.elementToBeClickable(campo));
    e.clear();
    e.sendKeys(valor);
  }
}
