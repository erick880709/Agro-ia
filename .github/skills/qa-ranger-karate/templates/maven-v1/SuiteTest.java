import com.intuit.karate.Results;
import com.intuit.karate.Runner;
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
        Results results = Runner.path("classpath:")
                .tags("~@ignore", "~@wip")
                .reportDir(QaEvidence.reportDirectory())
                .outputJunitXml(true)
                .outputCucumberJson(true)
                .parallel(5);
        assertEquals(0, results.getFailCount(), results.getErrorMessages());
    }
}
