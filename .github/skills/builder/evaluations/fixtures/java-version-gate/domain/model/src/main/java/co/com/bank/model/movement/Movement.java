package co.com.bank.model.movement;

import java.math.BigDecimal;
import java.time.LocalDate;

public sealed interface Movement permits Deposit, Withdrawal, Fee {
    LocalDate date();

    BigDecimal amount();
}
