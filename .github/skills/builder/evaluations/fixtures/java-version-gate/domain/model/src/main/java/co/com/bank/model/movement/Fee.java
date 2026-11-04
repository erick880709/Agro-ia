package co.com.bank.model.movement;

import java.math.BigDecimal;
import java.time.LocalDate;

public record Fee(LocalDate date, BigDecimal amount, String concept) implements Movement {
}
