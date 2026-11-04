package co.com.bancolombia.model.movement.gateways;

import co.com.bancolombia.model.movement.MovementResponse;
import reactor.core.publisher.Flux;

public interface MovementGateway {
    Flux<MovementResponse> findByAccount(String accountId, String orderBy);
}
