package co.com.bank.usecase.interest;

import co.com.bank.model.exception.BusinessException;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class OracleInterestTest {

    private final InterestUseCase useCase = new InterestUseCase();

    private static BigDecimal bd(String v) {
        return new BigDecimal(v);
    }

    @Test
    void roundsOnlyAtTheEnd() {
        assertEquals(bd("19583.33"), useCase.monthlyInterest(bd("1000000"), bd("23.5")));
        assertEquals(bd("1000.00"), useCase.monthlyInterest(bd("100000"), bd("12")));
    }

    @Test
    void usesBankersRounding() {
        assertEquals(bd("0.12"), useCase.monthlyInterest(bd("1200"), bd("0.125")));
        assertEquals(bd("0.14"), useCase.monthlyInterest(bd("1200"), bd("0.135")));
    }

    @Test
    void keepsTwoDecimalsAndZeroRate() {
        assertEquals(bd("0.00"), useCase.monthlyInterest(bd("5000"), BigDecimal.ZERO));
        assertEquals(2, useCase.monthlyInterest(bd("333"), bd("7")).scale());
    }

    @Test
    void keepsRateValidation() {
        assertThrows(BusinessException.class, () -> useCase.monthlyInterest(BigDecimal.TEN, bd("-1")));
        assertThrows(BusinessException.class, () -> useCase.monthlyInterest(BigDecimal.TEN, bd("100.01")));
    }
}
