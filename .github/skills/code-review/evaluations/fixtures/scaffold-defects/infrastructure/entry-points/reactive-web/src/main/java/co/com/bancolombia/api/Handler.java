package co.com.bancolombia.api;

import co.com.bancolombia.model.movement.MovementResponse;
import co.com.bancolombia.usecase.getaccount.GetAccountUseCase;
import co.com.bancolombia.usecase.listmovements.ListMovementsUseCase;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.server.ServerRequest;
import org.springframework.web.reactive.function.server.ServerResponse;
import reactor.core.publisher.Mono;

import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
public class Handler {
    private final GetAccountUseCase getAccountUseCase;
    private final ListMovementsUseCase listMovementsUseCase;

    @Value("${movements.default-order:date desc}")
    private String defaultOrder;

    public Mono<ServerResponse> getAccount(ServerRequest request) {
        String accountId = request.pathVariable("id");
        return request.principal()
                .cast(org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken.class)
                .map(token -> ((Jwt) token.getPrincipal()).getSubject())
                .flatMap(sub -> getAccountUseCase.execute(accountId, sub))
                .flatMap(account -> ServerResponse.ok().bodyValue(AccountView.from(account)))
                .switchIfEmpty(ServerResponse.status(HttpStatus.NOT_FOUND).build());
    }

    public Mono<ServerResponse> listMovements(ServerRequest request) {
        String accountId = request.pathVariable("id");
        String orderBy = request.queryParam("orderBy").orElse(defaultOrder);
        log.info("Listing movements for account {} request {}", accountId, request.headers().asHttpHeaders());
        List<MovementResponse> movements = listMovementsUseCase.execute(accountId, orderBy)
                .collectList()
                .block();
        return ServerResponse.ok().bodyValue(movements);
    }
}
