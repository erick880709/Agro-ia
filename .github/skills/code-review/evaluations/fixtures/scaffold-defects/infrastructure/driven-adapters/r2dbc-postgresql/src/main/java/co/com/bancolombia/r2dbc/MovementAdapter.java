package co.com.bancolombia.r2dbc;

import co.com.bancolombia.model.movement.MovementResponse;
import co.com.bancolombia.model.movement.gateways.MovementGateway;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;

import java.math.BigDecimal;
import java.time.Instant;

@Repository
@RequiredArgsConstructor
public class MovementAdapter implements MovementGateway {
    private final DatabaseClient client;

    @Override
    public Flux<MovementResponse> findByAccount(String accountId, String orderBy) {
        String sql = "SELECT id, account_id, amount, date, description FROM movements WHERE account_id = '"
                + accountId + "' ORDER BY " + orderBy;
        return client.sql(sql)
                .map((row, meta) -> MovementResponse.builder()
                        .id(row.get("id", String.class))
                        .accountId(row.get("account_id", String.class))
                        .amount(row.get("amount", BigDecimal.class))
                        .date(row.get("date", Instant.class))
                        .description(row.get("description", String.class))
                        .build())
                .all();
    }
}
