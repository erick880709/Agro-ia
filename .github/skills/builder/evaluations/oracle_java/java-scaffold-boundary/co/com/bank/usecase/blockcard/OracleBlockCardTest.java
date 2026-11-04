package co.com.bank.usecase.blockcard;

import co.com.bank.model.audit.AuditEvent;
import co.com.bank.model.audit.gateways.AuditGateway;
import co.com.bank.model.card.Card;
import co.com.bank.model.card.CardStatus;
import co.com.bank.model.card.gateways.CardRepository;
import co.com.bank.model.exception.BusinessErrorType;
import co.com.bank.model.exception.BusinessException;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class OracleBlockCardTest {

    static final class FakeCards implements CardRepository {
        final Map<String, Card> cards = new HashMap<>();
        int saves;

        public Optional<Card> findById(String id) {
            return Optional.ofNullable(cards.get(id));
        }

        public Card save(Card card) {
            saves++;
            cards.put(card.id(), card);
            return card;
        }
    }

    static final class FakeAudit implements AuditGateway {
        final List<AuditEvent> events = new ArrayList<>();

        public void record(AuditEvent event) {
            events.add(event);
        }
    }

    @Test
    void blocksActiveCardAndAuditsOnce() {
        FakeCards cards = new FakeCards();
        FakeAudit audit = new FakeAudit();
        cards.cards.put("c-1", new Card("c-1", "h-1", CardStatus.ACTIVE));
        Card result = new BlockCardUseCase(cards, audit).block("c-1", "LOST");
        assertEquals(CardStatus.BLOCKED, result.status());
        assertEquals(CardStatus.BLOCKED, cards.cards.get("c-1").status());
        assertEquals(1, audit.events.size());
        AuditEvent event = audit.events.get(0);
        assertEquals("CARD_BLOCKED", event.action());
        assertEquals("c-1", event.resourceId());
        assertTrue(event.detail().contains("LOST"), "detail must include the reason");
    }

    @Test
    void alreadyBlockedIsIdempotent() {
        FakeCards cards = new FakeCards();
        FakeAudit audit = new FakeAudit();
        cards.cards.put("c-2", new Card("c-2", "h-1", CardStatus.BLOCKED));
        Card result = new BlockCardUseCase(cards, audit).block("c-2", "LOST");
        assertEquals(CardStatus.BLOCKED, result.status());
        assertEquals(0, cards.saves);
        assertEquals(0, audit.events.size());
    }

    @Test
    void missingCardIsBusinessError() {
        BusinessException error = assertThrows(BusinessException.class,
                () -> new BlockCardUseCase(new FakeCards(), new FakeAudit()).block("nope", "LOST"));
        assertEquals(BusinessErrorType.CARD_NOT_FOUND, error.getType());
    }
}
