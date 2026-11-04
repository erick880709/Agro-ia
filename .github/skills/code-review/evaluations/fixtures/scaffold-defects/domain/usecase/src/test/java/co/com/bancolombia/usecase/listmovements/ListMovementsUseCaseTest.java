package co.com.bancolombia.usecase.listmovements;

import co.com.bancolombia.model.movement.MovementResponse;
import co.com.bancolombia.model.movement.gateways.MovementGateway;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class ListMovementsUseCaseTest {
    private final MovementGateway gateway = mock(MovementGateway.class);
    private final ListMovementsUseCase useCase = new ListMovementsUseCase(gateway);

    @Test
    void listsMovements() {
        when(gateway.findByAccount("1", "date")).thenReturn(Flux.just(MovementResponse.builder().id("m1").build()));
        StepVerifier.create(useCase.execute("1", "date"));
    }
}
