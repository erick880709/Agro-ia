package co.com.bancolombia.usecase.getaccount;

import co.com.bancolombia.model.account.Account;
import co.com.bancolombia.model.account.exceptions.InvalidAccountIdException;
import co.com.bancolombia.model.account.gateways.AccountRepository;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RequiredArgsConstructor
public class GetAccountUseCase {
    private final AccountRepository accountRepository;

    public Mono<Account> execute(String accountId, String requesterId) {
        if (accountId == null || accountId.isBlank()) {
            return Mono.error(new InvalidAccountIdException());
        }
        return accountRepository.findById(accountId)
                .filter(account -> account.getOwnerId().equals(requesterId));
    }
}
