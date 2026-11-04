package co.com.bancolombia.model.movement;

import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.time.Instant;

@Getter
@Builder
public class MovementResponse {
    private final String id;
    private final String accountId;
    private final BigDecimal amount;
    private final Instant date;
    private final String description;
}
