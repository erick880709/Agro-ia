package __PKG__.support;

import __PKG__.driver.DriverFactory;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.extension.ExtensionContext;
import org.junit.jupiter.api.extension.LifecycleMethodExecutionExceptionHandler;
import org.junit.jupiter.api.extension.TestExecutionExceptionHandler;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;

/**
 * Captura screenshot, page source y URL en el momento del fallo y relanza la excepción.
 * Cubre fallos en el test Y en @BeforeEach (p. ej. un login que falla): TestExecutionExceptionHandler
 * NO se invoca para métodos de ciclo de vida, por eso también se implementa LifecycleMethodExecutionExceptionHandler.
 * Se ejecuta antes de @AfterEach (que cierra el driver). Evidencia en target/evidencia/.
 */
public class EvidenciaAlFallar implements TestExecutionExceptionHandler, LifecycleMethodExecutionExceptionHandler {

  @Override
  public void handleTestExecutionException(ExtensionContext ctx, Throwable causa) throws Throwable {
    capturar(ctx, causa, "");
    throw causa;
  }

  @Override
  public void handleBeforeEachMethodExecutionException(ExtensionContext ctx, Throwable causa) throws Throwable {
    capturar(ctx, causa, "_beforeEach");
    throw causa;
  }

  private static void capturar(ExtensionContext ctx, Throwable causa, String sufijo) {
    if (!DriverFactory.activo()) return;
    WebDriver d = DriverFactory.actual();
    String nombre = (ctx.getRequiredTestClass().getSimpleName() + "_" + ctx.getDisplayName() + sufijo)
        .replaceAll("[^A-Za-z0-9._-]+", "_");
    Path dir = Path.of("target", "evidencia");
    try {
      Files.createDirectories(dir);
      Files.write(dir.resolve(nombre + ".png"), ((TakesScreenshot) d).getScreenshotAs(OutputType.BYTES));
      Files.writeString(dir.resolve(nombre + ".html"),
          "<!-- " + d.getCurrentUrl() + " -->\n" + d.getPageSource(), StandardCharsets.UTF_8);
    } catch (IOException | RuntimeException e) {
      causa.addSuppressed(e);       // la evidencia nunca debe ocultar el fallo original
    }
  }
}
