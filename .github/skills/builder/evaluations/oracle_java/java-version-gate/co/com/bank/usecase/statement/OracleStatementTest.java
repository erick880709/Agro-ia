package co.com.bank.usecase.statement;

import co.com.bank.model.movement.Deposit;
import co.com.bank.model.movement.Fee;
import co.com.bank.model.movement.Movement;
import co.com.bank.model.movement.Withdrawal;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class OracleStatementTest {

    private final StatementUseCase useCase = new StatementUseCase();
    private final Movement d1 = new Deposit(LocalDate.of(2026, 1, 1), new BigDecimal("100.50"), "NOMINA");
    private final Movement w1 = new Withdrawal(LocalDate.of(2026, 1, 2), new BigDecimal("20"), "ATM");
    private final Movement f1 = new Fee(LocalDate.of(2026, 1, 3), new BigDecimal("3.90"), "CUOTA");

    @Test
    void latestNewestFirstWithoutMutatingInput() {
        List<Movement> input = new ArrayList<>(List.of(d1, w1, f1));
        assertEquals(List.of(f1, w1), useCase.latest(input, 2));
        assertEquals(List.of(f1, w1, d1), useCase.latest(input, 10));
        assertEquals(List.of(d1, w1, f1), input);
        assertEquals(List.of(), useCase.latest(List.of(), 3));
    }

    @Test
    void rejectsNonPositiveLimit() {
        assertThrows(RuntimeException.class, () -> useCase.latest(List.of(d1), 0));
    }

    @Test
    void describesEachMovementType() {
        assertEquals("Consignación NOMINA +100.50", useCase.describe(d1));
        assertEquals("Retiro ATM -20", useCase.describe(w1));
        assertEquals("Comisión CUOTA -3.90", useCase.describe(f1));
    }
}
