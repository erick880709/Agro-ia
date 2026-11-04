package co.com.bank.model.audit;

public record AuditEvent(String action, String resourceId, String detail) {
}
