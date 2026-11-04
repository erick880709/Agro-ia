package __PKG__.support;

import __PKG__.driver.DriverFactory;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.extension.ExtendWith;
import org.openqa.selenium.WebDriver;

/** Un navegador nuevo por test, cerrado siempre al final. */
@ExtendWith(EvidenciaAlFallar.class)
public abstract class BaseTest {
  protected WebDriver driver;

  @BeforeEach
  void abrirNavegador() {
    driver = DriverFactory.iniciar();
  }

  @AfterEach
  void cerrarNavegador() {
    DriverFactory.cerrar();
  }
}
