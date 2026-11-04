package __PKG__.driver;

import __PKG__.config.Config;
import java.net.MalformedURLException;
import java.net.URI;
import java.time.Duration;
import org.openqa.selenium.Capabilities;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.edge.EdgeDriver;
import org.openqa.selenium.edge.EdgeOptions;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.firefox.FirefoxOptions;
import org.openqa.selenium.remote.RemoteWebDriver;

/** Un WebDriver por hilo (seguro para ejecución paralela). Los drivers los resuelve Selenium Manager. */
public final class DriverFactory {
  private static final ThreadLocal<WebDriver> DRIVER = new ThreadLocal<>();

  private DriverFactory() {}

  public static WebDriver iniciar() {
    if (DRIVER.get() != null) {
      throw new IllegalStateException("Ya hay un WebDriver en este hilo: falta cerrar() en el teardown");
    }
    Capabilities opciones = opciones();
    WebDriver driver;
    if (Config.gridUrl() != null) {
      try {
        driver = new RemoteWebDriver(URI.create(Config.gridUrl()).toURL(), opciones);
      } catch (MalformedURLException e) {
        throw new IllegalArgumentException("gridUrl inválida: " + Config.gridUrl(), e);
      }
    } else {
      driver = switch (Config.browser()) {
        case "firefox" -> new FirefoxDriver((FirefoxOptions) opciones);
        case "edge" -> new EdgeDriver((EdgeOptions) opciones);
        default -> new ChromeDriver((ChromeOptions) opciones);
      };
    }
    driver.manage().timeouts().implicitlyWait(Duration.ZERO);   // solo esperas explícitas
    driver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(30));
    DRIVER.set(driver);
    return driver;
  }

  public static WebDriver actual() {
    WebDriver d = DRIVER.get();
    if (d == null) throw new IllegalStateException("No hay WebDriver iniciado en este hilo");
    return d;
  }

  public static boolean activo() {
    return DRIVER.get() != null;
  }

  public static void cerrar() {
    WebDriver d = DRIVER.get();
    if (d != null) {
      try {
        d.quit();
      } finally {
        DRIVER.remove();
      }
    }
  }

  private static Capabilities opciones() {
    switch (Config.browser()) {
      case "firefox": {
        FirefoxOptions o = new FirefoxOptions();
        if (Config.headless()) o.addArguments("-headless");
        o.addArguments("--width=1920", "--height=1080");
        return o;
      }
      case "edge": {
        EdgeOptions o = new EdgeOptions();
        if (Config.headless()) o.addArguments("--headless=new");
        o.addArguments("--window-size=1920,1080");
        return o;
      }
      default: {
        ChromeOptions o = new ChromeOptions();
        if (Config.headless()) o.addArguments("--headless=new");
        o.addArguments("--window-size=1920,1080", "--lang=es-CO");
        String binario = System.getenv("CHROME_BINARY");          // opcional: navegador corporativo/portable
        if (binario != null && !binario.isBlank()) o.setBinary(binario);
        if ("true".equals(System.getenv("CONTAINER"))) o.addArguments("--no-sandbox", "--disable-dev-shm-usage");
        return o;
      }
    }
  }
}
