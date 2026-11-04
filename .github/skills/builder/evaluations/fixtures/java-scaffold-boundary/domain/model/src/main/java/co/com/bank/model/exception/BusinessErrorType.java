package co.com.bank.model.exception;

public enum BusinessErrorType {
    CARD_NOT_FOUND("La tarjeta no existe");

    private final String message;

    BusinessErrorType(String message) {
        this.message = message;
    }

    public String message() {
        return message;
    }
}
