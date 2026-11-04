package co.com.bank.model.card;

public record Card(String id, String holderId, CardStatus status) {

    public Card withStatus(CardStatus newStatus) {
        return new Card(id, holderId, newStatus);
    }
}
