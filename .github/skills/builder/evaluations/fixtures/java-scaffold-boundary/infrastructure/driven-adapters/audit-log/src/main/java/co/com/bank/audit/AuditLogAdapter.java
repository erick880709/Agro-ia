package co.com.bank.audit;

import co.com.bank.model.audit.AuditEvent;
import co.com.bank.model.audit.gateways.AuditGateway;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class AuditLogAdapter implements AuditGateway {

    private static final Logger log = LoggerFactory.getLogger(AuditLogAdapter.class);

    @Override
    public void record(AuditEvent event) {
        log.info("audit action={} resource={}", event.action(), event.resourceId());
    }
}
