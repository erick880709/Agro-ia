package co.com.bancolombia.api;

import co.com.bancolombia.usecase.getaccount.GetAccountUseCase;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.server.ServerRequest;
import org.springframework.web.reactive.function.server.ServerResponse;
import reactor.core.publisher.Mono;

@Component
@RequiredArgsConstructor
public class Handler {
    private final GetAccountUseCase getAccountUseCase;

    public Mono<ServerResponse> getAccount(ServerRequest request) {
        String accountId = request.pathVariable("id");
        return request.principal()
                .cast(org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken.class)
                .map(token -> ((Jwt) token.getPrincipal()).getSubject())
                .flatMap(sub -> getAccountUseCase.execute(accountId, sub))
                .flatMap(account -> ServerResponse.ok().bodyValue(AccountView.from(account)))
                .switchIfEmpty(ServerResponse.status(HttpStatus.NOT_FOUND).build());
    }
}
