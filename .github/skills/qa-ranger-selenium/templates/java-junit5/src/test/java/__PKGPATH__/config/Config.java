package __PKG__.config;

import java.io.IOException;
import java.io.InputStream;
import java.time.Duration;
import java.util.Properties;

/** Configuración: -Dpropiedad > variable de entorno > config/<env>.properties > valor por defecto. */
public final class Config {
  private static final String ENV = valor0("env", "TEST_ENV", "__ENV__");
  private static final Properties ARCHIVO = cargar(ENV);

  private Config() {}

  public static String env()        { return ENV; }
  public static String baseUrl()    { return quitarBarra(requerido("baseUrl", "BASE_URL")); }
  public static String browser()    { return valor("browser", "BROWSER", "chrome").toLowerCase(); }
  public static boolean headless()  { return Boolean.parseBoolean(valor("headless", "HEADLESS", "true")); }
  /** URL del Selenium Grid / nube; null = navegador local. */
  public static String gridUrl()    { return valor("gridUrl", "GRID_URL", null); }
  public static Duration espera()   { return Duration.ofSeconds(Long.parseLong(valor("esperaSeg", "ESPERA_SEG", "10"))); }

  /** Secretos: SOLO desde variables de entorno (nunca en archivos del repositorio). */
  public static String secreto(String variable) {
    String v = System.getenv(variable);
    if (v == null || v.isBlank()) {
      throw new IllegalStateException("Falta la variable de entorno " + variable);
    }
    return v;
  }

  private static String valor(String prop, String envVar, String porDefecto) {
    String v = valor0(prop, envVar, null);
    if (v == null) v = ARCHIVO.getProperty(prop);
    return (v == null || v.isBlank()) ? porDefecto : v;
  }

  private static String valor0(String prop, String envVar, String porDefecto) {
    String v = System.getProperty(prop);
    if (v == null || v.isBlank()) v = System.getenv(envVar);
    return (v == null || v.isBlank()) ? porDefecto : v;
  }

  private static String requerido(String prop, String envVar) {
    String v = valor(prop, envVar, null);
    if (v == null) {
      throw new IllegalStateException("Falta '" + prop + "' (-D" + prop + ", " + envVar + " o config/" + ENV + ".properties)");
    }
    return v;
  }

  private static String quitarBarra(String url) {
    return url.endsWith("/") ? url.substring(0, url.length() - 1) : url;
  }

  private static Properties cargar(String env) {
    Properties p = new Properties();
    try (InputStream in = Config.class.getClassLoader().getResourceAsStream("config/" + env + ".properties")) {
      if (in != null) p.load(new java.io.InputStreamReader(in, java.nio.charset.StandardCharsets.UTF_8));
    } catch (IOException e) {
      throw new IllegalStateException("No se pudo leer config/" + env + ".properties", e);
    }
    return p;
  }
}
