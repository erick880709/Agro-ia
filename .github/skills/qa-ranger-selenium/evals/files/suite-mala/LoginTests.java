package tests;

import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.ui.WebDriverWait;
import static org.junit.jupiter.api.Assertions.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class LoginTests {
  static WebDriver driver;
  static String referencia;

  @FindBy(id = "usuario") WebElement usuario;

  @BeforeAll
  static void setup() {
    System.setProperty("webdriver.chrome.driver", "C:/drivers/chromedriver.exe");
    driver = new ChromeDriver();
    driver.manage().timeouts().implicitlyWait(10, TimeUnit.SECONDS);
  }

  @Test @Order(1)
  void test1() throws Exception {
    driver.get("https://qa.banco-demo.com/login");
    driver.findElementById("usuario").sendKeys("usuario.qa");
    driver.findElement(By.name("clave")).sendKeys("Clave-Prueba-1");
    driver.findElement(By.xpath("/html/body/main/form/button")).click();
    Thread.sleep(3000);
    assertTrue(driver.getCurrentUrl().contains("inicio"));
  }

  @Test @Order(2)
  void test2() throws Exception {
    driver.get("https://qa.banco-demo.com/transferencias/nueva");
    new WebDriverWait(driver, 10);
    driver.findElement(By.cssSelector(".css-1x9ab2c input")).sendKeys("150000");
    ((JavascriptExecutor) driver).executeScript("document.querySelector('#confirmar').click()");
    try {
      referencia = driver.findElement(By.xpath("(//div)[7]/span")).getText();
    } catch (Exception e) {}
  }

  @Test @Order(3) @Disabled
  void test3() {
    driver.get("https://qa.banco-demo.com/historial");
    assertTrue(driver.getPageSource().contains(referencia));
  }

  @AfterAll
  static void cerrar() { driver.close(); }
}
