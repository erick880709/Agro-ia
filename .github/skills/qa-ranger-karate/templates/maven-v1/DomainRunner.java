package {{DOMAIN}};

import com.intuit.karate.junit5.Karate;

/** Ejecuta las pruebas de un dominio desde el IDE. La integración continua usa SuiteTest. */
class {{DOMAIN_CLASS}}Runner {

    @Karate.Test
    Karate {{DOMAIN}}() {
        return Karate.run().relativeTo(getClass());
    }
}
