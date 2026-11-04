package {{DOMAIN}};

import io.karatelabs.junit6.Karate;
import org.junit.jupiter.api.DynamicNode;

/** Ejecuta las pruebas de un dominio desde el IDE. La integración continua usa SuiteTest. */
class {{DOMAIN_CLASS}}Runner {

    @Karate.Test
    Iterable<DynamicNode> {{DOMAIN}}() {
        return Karate.run().relativeTo(getClass());
    }
}
