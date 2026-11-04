package co.com.bank.usecase.interest;

import co.com.bank.model.exception.BusinessException;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.assertThrows;

class InterestUseCaseTest {

    private final InterestUseCase useCase = new InterestUseCase();

    @Test
    void rejectsNegativeRate() {
        assertThrows(BusinessException.class,
                () -> useCase.monthlyInterest(BigDecimal.TEN, BigDecimal.valueOf(-1)));
    }
}
