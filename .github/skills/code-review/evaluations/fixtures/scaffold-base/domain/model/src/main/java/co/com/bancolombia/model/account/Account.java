package co.com.bancolombia.model.account;

import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;

@Getter
@Builder(toBuilder = true)
public class Account {
    private final String id;
    private final String ownerId;
    private final String number;
    private final BigDecimal balance;
}
