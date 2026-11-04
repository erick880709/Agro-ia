package co.com.bank.jpa;

import co.com.bank.model.card.Card;
import co.com.bank.model.card.gateways.CardRepository;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Repository
public class CardJpaAdapter implements CardRepository {

    private final CardDataRepository repository;

    public CardJpaAdapter(CardDataRepository repository) {
        this.repository = repository;
    }

    @Override
    public Optional<Card> findById(String id) {
        return repository.findById(id).map(CardData::toDomain);
    }

    @Override
    @Transactional
    public Card save(Card card) {
        return repository.save(CardData.fromDomain(card)).toDomain();
    }
}
