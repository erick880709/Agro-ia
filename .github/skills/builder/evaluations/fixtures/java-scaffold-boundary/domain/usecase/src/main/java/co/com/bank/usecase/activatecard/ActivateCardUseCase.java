package co.com.bank.usecase.activatecard;

import co.com.bank.model.audit.AuditEvent;
import co.com.bank.model.audit.gateways.AuditGateway;
import co.com.bank.model.card.Card;
import co.com.bank.model.card.CardStatus;
import co.com.bank.model.card.gateways.CardRepository;
import co.com.bank.model.exception.BusinessErrorType;
import co.com.bank.model.exception.BusinessException;

public class ActivateCardUseCase {

    private final CardRepository cardRepository;
    private final AuditGateway auditGateway;

    public ActivateCardUseCase(CardRepository cardRepository, AuditGateway auditGateway) {
        this.cardRepository = cardRepository;
        this.auditGateway = auditGateway;
    }

    public Card activate(String cardId) {
        Card card = cardRepository.findById(cardId)
                .orElseThrow(() -> new BusinessException(BusinessErrorType.CARD_NOT_FOUND));
        if (card.status() == CardStatus.ACTIVE) {
            return card;
        }
        Card saved = cardRepository.save(card.withStatus(CardStatus.ACTIVE));
        auditGateway.record(new AuditEvent("CARD_ACTIVATED", cardId, ""));
        return saved;
    }
}
