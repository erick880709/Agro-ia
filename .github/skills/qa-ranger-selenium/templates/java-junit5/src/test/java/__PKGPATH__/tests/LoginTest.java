package __PKG__.tests;

import static org.assertj.core.api.Assertions.assertThat;

import __PKG__.config.Config;
import __PKG__.pages.LoginPage;
import __PKG__.support.BaseTest;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

@Tag("login")
class LoginTest extends BaseTest {

  @Test
  @Tag("smoke")
  @DisplayName("[HU-000][CA-1] ingresa con credenciales válidas")
  void ingresaConCredencialesValidas() {
    LoginPage login = new LoginPage(driver).abrir();
    login.ingresar(Config.secreto("E2E_USER"), Config.secreto("E2E_PASSWORD"));
    assertThat(login.enInicio()).as("debe mostrarse la página de inicio").isTrue();
  }

  @Test
  @DisplayName("[HU-000][CA-2] rechaza una contraseña incorrecta")
  void rechazaContrasenaIncorrecta() {
    LoginPage login = new LoginPage(driver).abrir()
        .intentar(Config.secreto("E2E_USER"), "incorrecta-" + System.nanoTime());
    assertThat(login.error()).isNotBlank();
    assertThat(login.enInicio()).isFalse();
  }
}
