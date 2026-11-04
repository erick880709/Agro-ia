package co.com.bancolombia.usecase.getaccount;

import co.com.bancolombia.model.account.Account;
import co.com.bancolombia.model.account.gateways.AccountRepository;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class GetAccountUseCaseTest {
    private final AccountRepository repository = mock(AccountRepository.class);
    private final GetAccountUseCase useCase = new GetAccountUseCase(repository);

    @Test
    void returnsAccountForOwner() {
        Account account = Account.builder().id("1").ownerId("u1").build();
        when(repository.findById("1")).thenReturn(Mono.just(account));
        StepVerifier.create(useCase.execute("1", "u1")).expectNext(account).verifyComplete();
    }

    @Test
    void hidesAccountFromOtherUser() {
        Account account = Account.builder().id("1").ownerId("u1").build();
        when(repository.findById("1")).thenReturn(Mono.just(account));
        StepVerifier.create(useCase.execute("1", "u2")).verifyComplete();
    }
}
