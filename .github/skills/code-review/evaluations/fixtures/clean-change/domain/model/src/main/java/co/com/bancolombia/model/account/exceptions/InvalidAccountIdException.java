package co.com.bancolombia.model.account.exceptions;

public class InvalidAccountIdException extends RuntimeException {
    public InvalidAccountIdException() {
        super("El identificador de cuenta es obligatorio");
    }
}
