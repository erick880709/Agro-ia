import io.karatelabs.core.Runner;
import io.karatelabs.core.SuiteResult;
import org.junit.jupiter.api.Test;
import qa.QaEvidence;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Ejecuta todas las pruebas en paralelo y genera un reporte consolidado para integración continua (CI).
 * Ejecutar: mvn test -Dkarate.env=qa -Dkarate.options="--tags @smoke"
 */
class SuiteTest {

    @Test
    void ejecutarSuite() {
        SuiteResult result = Runner.path("classpath:")
                .tags("~@ignore", "~@wip")
                .outputDir(QaEvidence.reportDirectory())
                .outputJunitXml(true)
                .outputCucumberJson(true)
                .outputJsonLines(true)
                .parallel(5);
        assertEquals(0, result.getScenarioFailedCount(), String.join("\n", result.getErrors()));
    }
}
