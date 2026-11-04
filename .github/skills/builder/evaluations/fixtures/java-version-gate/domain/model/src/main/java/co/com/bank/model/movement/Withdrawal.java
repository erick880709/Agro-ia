package co.com.bank.model.movement;

import java.math.BigDecimal;
import java.time.LocalDate;

public record Withdrawal(LocalDate date, BigDecimal amount, String channel) implements Movement {
}
