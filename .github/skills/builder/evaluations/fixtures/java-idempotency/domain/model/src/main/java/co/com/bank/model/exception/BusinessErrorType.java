package co.com.bank.model.exception;

public enum BusinessErrorType {
    INVALID_AMOUNT("El monto debe ser positivo");

    private final String message;

    BusinessErrorType(String message) {
        this.message = message;
    }

    public String message() {
        return message;
    }
}
