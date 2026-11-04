package co.com.bank.model.payment;

import java.math.BigDecimal;

public record PaymentEvent(String eventId, String accountId, BigDecimal amount) {
}
