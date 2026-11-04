package co.com.bank.jpa;

import co.com.bank.model.card.Card;
import co.com.bank.model.card.CardStatus;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "cards")
public class CardData {
    @Id
    @Column(name = "id")
    private String id;
    @Column(name = "holder_id", nullable = false)
    private String holderId;
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private CardStatus status;

    protected CardData() {
    }

    static CardData fromDomain(Card card) {
        CardData data = new CardData();
        data.id = card.id();
        data.holderId = card.holderId();
        data.status = card.status();
        return data;
    }

    Card toDomain() {
        return new Card(id, holderId, status);
    }
}
