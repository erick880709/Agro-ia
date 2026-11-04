package co.com.bank.model.card.gateways;

import co.com.bank.model.card.Card;

import java.util.Optional;

public interface CardRepository {
    Optional<Card> findById(String id);

    Card save(Card card);
}
