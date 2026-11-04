package co.com.bank.model.payment.gateways;

import java.math.BigDecimal;

public interface AccountGateway {
    /** Acredita el monto; puede lanzar excepción ante fallos técnicos. */
    void credit(String accountId, BigDecimal amount);
}
