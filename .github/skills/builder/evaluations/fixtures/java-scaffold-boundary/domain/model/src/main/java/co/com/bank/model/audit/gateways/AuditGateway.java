package co.com.bank.model.audit.gateways;

import co.com.bank.model.audit.AuditEvent;

public interface AuditGateway {
    void record(AuditEvent event);
}
