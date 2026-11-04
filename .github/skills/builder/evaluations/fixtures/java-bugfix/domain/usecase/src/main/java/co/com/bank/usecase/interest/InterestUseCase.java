package co.com.bank.usecase.interest;

import co.com.bank.model.exception.BusinessErrorType;
import co.com.bank.model.exception.BusinessException;

import java.math.BigDecimal;
import java.math.RoundingMode;

public class InterestUseCase {

    private static final BigDecimal MONTHS_PERCENT = BigDecimal.valueOf(1200);

    /**
     * Interés mensual simple: capital x tasaAnual% / 12, en pesos con 2 decimales.
     */
    public BigDecimal monthlyInterest(BigDecimal principal, BigDecimal annualRatePercent) {
        if (annualRatePercent.signum() < 0 || annualRatePercent.compareTo(BigDecimal.valueOf(100)) > 0) {
            throw new BusinessException(BusinessErrorType.INVALID_RATE);
        }
        BigDecimal monthlyRate = annualRatePercent.divide(MONTHS_PERCENT, 2, RoundingMode.HALF_UP);
        return principal.multiply(monthlyRate).setScale(2, RoundingMode.HALF_UP);
    }
}
