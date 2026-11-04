package __PKG__.support;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedCondition;

/** Condiciones de espera reutilizables que no trae ExpectedConditions. */
public final class Esperas {
  private Esperas() {}

  /** Devuelve el texto del elemento cuando deja de estar vacío (null = seguir esperando). */
  public static ExpectedCondition<String> textoNoVacio(By locator) {
    return new ExpectedCondition<>() {
      @Override public String apply(WebDriver d) {
        String t = d.findElement(locator).getText();
        return (t == null || t.isBlank()) ? null : t.trim();
      }
      @Override public String toString() {
        return "texto no vacío en " + locator;
      }
    };
  }
}
