package co.com.bancolombia.usecase.listmovements;

import co.com.bancolombia.model.movement.MovementResponse;
import co.com.bancolombia.model.movement.gateways.MovementGateway;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Flux;

@RequiredArgsConstructor
public class ListMovementsUseCase {
    private final MovementGateway movementGateway;
    private String lastAccountId;

    public Flux<MovementResponse> execute(String accountId, String orderBy) {
        this.lastAccountId = accountId;
        return movementGateway.findByAccount(accountId, orderBy);
    }
}
