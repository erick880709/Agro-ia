package co.com.bank.model.movement;

import java.math.BigDecimal;
import java.time.LocalDate;

public record Deposit(LocalDate date, BigDecimal amount, String origin) implements Movement {
}
