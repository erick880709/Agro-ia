package co.com.bank.config;

import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.FilterType;

/** Registra como beans todas las clases cuyo nombre termina en UseCase. */
@Configuration
@ComponentScan(basePackages = "co.com.bank.usecase",
        includeFilters = @ComponentScan.Filter(type = FilterType.REGEX, pattern = "^.+UseCase$"),
        useDefaultFilters = false)
public class UseCasesConfig {
}
