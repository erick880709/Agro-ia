package co.com.bank.usecase.payment;

import co.com.bank.model.exception.BusinessErrorType;
import co.com.bank.model.exception.BusinessException;
import co.com.bank.model.payment.PaymentEvent;
import co.com.bank.model.payment.gateways.AccountGateway;
import co.com.bank.model.payment.gateways.ProcessedEventGateway;

public class PaymentEventUseCase {

    private final AccountGateway accountGateway;
    private final ProcessedEventGateway processedEvents;

    public PaymentEventUseCase(AccountGateway accountGateway, ProcessedEventGateway processedEvents) {
        this.accountGateway = accountGateway;
        this.processedEvents = processedEvents;
    }

    /** Devuelve true si el evento se aplicó en esta invocación. */
    public boolean handle(PaymentEvent event) {
        if (event.amount().signum() <= 0) {
            throw new BusinessException(BusinessErrorType.INVALID_AMOUNT);
        }
        if (processedEvents.exists(event.eventId())) {
            return false;
        }
        accountGateway.credit(event.accountId(), event.amount());
        processedEvents.save(event.eventId());
        return true;
    }
}
