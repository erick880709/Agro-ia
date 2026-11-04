package co.com.bank.model.exception;

public enum BusinessErrorType {
    INVALID_RATE("La tasa debe estar entre 0 y 100");

    private final String message;

    BusinessErrorType(String message) {
        this.message = message;
    }

    public String message() {
        return message;
    }
}
