# BDD/Gherkin con Selenium Java

Usa Cucumber-JVM cuando ya forme parte del proyecto o el encargo lo requiera. Consulta los [criterios BDD comunes](../../ranger/references/tools/bdd_gherkin_patterns.md) y la [arquitectura del framework](03-arquitectura-framework.md). Los fragmentos ilustran los steps; completa imports y dependencias según el runner instalado.

## Índice

- [BDD sobre Selenium Java (Cucumber-JVM)](#bdd-sobre-selenium-java-cucumber-jvm)
- [Hooks, evidencia y trazabilidad](#hooks-evidencia-y-trazabilidad)

## BDD sobre Selenium Java (Cucumber-JVM)

```xml
<!-- pom.xml, sumar al proyecto Selenium existente; setup en qa-ranger-selenium -->
<dependency>
  <groupId>io.cucumber</groupId>
  <artifactId>cucumber-java</artifactId>
  <version>7.20.1</version>
</dependency>
<dependency>
  <groupId>io.cucumber</groupId>
  <artifactId>cucumber-junit-platform-engine</artifactId>
  <version>7.20.1</version>
</dependency>
```

```java
// steps/LoginSteps.java
public class LoginSteps {
    private final WebDriver driver = DriverFactory.actual();
    private LoginPage loginPage;

    @Given("el usuario está en la página de login")
    public void elUsuarioEstaEnLaPaginaDeLogin() {
        driver.get(System.getenv("QA_BASE_URL") + "/login");
        loginPage = new LoginPage(driver);
    }

    @When("ingresa un email y password válidos")
    public void ingresaCredencialesValidas() {
        loginPage.login(System.getenv("QA_USER_EMAIL"), System.getenv("QA_USER_PASSWORD"));
    }
}
```

Inyección de dependencias entre archivos de steps (para compartir el
`WebDriver`/estado entre `Given`/`When`/`Then` de clases distintas) vía
PicoContainer o Guice — evita pasar el driver como parámetro manualmente
por todos lados.

## Hooks, evidencia y trazabilidad

Adapta el ciclo de vida de captura del proyecto a Cucumber. Conserva los tags de caso y prioridad en el reporte nativo y su conversión CTRF, y vincula cada escenario con su sesión WebDriver. Captura antes de cerrar el driver. Un hook que adjunta una screenshot solo al fallar no satisface la política browser para casos exitosos. Consulta [reportes y evidencia](14-reportes-y-evidencia.md).
