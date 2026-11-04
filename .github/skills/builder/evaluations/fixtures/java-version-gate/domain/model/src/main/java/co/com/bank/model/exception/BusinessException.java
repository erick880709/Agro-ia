package co.com.bank.model.exception;

/** Error de negocio con un código estable consumido por los canales. */
public class BusinessException extends RuntimeException {
    private final BusinessErrorType type;

    public BusinessException(BusinessErrorType type) {
        super(type.message());
        this.type = type;
    }

    public BusinessErrorType getType() {
        return type;
    }
}
