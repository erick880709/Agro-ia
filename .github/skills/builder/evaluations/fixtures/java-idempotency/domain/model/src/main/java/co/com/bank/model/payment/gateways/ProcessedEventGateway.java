package co.com.bank.model.payment.gateways;

/**
 * Registro de eventos procesados respaldado por una restricción única en base de datos.
 */
public interface ProcessedEventGateway {
    /** Consulta no atómica. */
    boolean exists(String eventId);

    /** Inserción no atómica. */
    void save(String eventId);

    /** Inserta el id de forma atómica; devuelve false si ya existía. */
    boolean markIfAbsent(String eventId);

    /** Elimina la marca para permitir un reproceso. */
    void release(String eventId);
}
