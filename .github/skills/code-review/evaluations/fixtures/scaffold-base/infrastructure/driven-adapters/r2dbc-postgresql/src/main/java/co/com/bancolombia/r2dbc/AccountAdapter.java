package co.com.bancolombia.r2dbc;

import co.com.bancolombia.model.account.Account;
import co.com.bancolombia.model.account.gateways.AccountRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;

@Repository
@RequiredArgsConstructor
public class AccountAdapter implements AccountRepository {
    private final DatabaseClient client;

    @Override
    public Mono<Account> findById(String id) {
        return client.sql("SELECT id, owner_id, number, balance FROM accounts WHERE id = :id")
                .bind("id", id)
                .map((row, meta) -> Account.builder()
                        .id(row.get("id", String.class))
                        .ownerId(row.get("owner_id", String.class))
                        .number(row.get("number", String.class))
                        .balance(row.get("balance", BigDecimal.class))
                        .build())
                .one();
    }
}
