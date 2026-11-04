package co.com.bank.usecase.payment;

import co.com.bank.model.payment.PaymentEvent;
import co.com.bank.model.payment.gateways.AccountGateway;
import co.com.bank.model.payment.gateways.ProcessedEventGateway;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class OraclePaymentEventTest {

    static final class FakeProcessed implements ProcessedEventGateway {
        final Set<String> ids = ConcurrentHashMap.newKeySet();

        public boolean exists(String id) {
            boolean found = ids.contains(id);
            Thread.yield();
            return found;
        }

        public void save(String id) {
            Thread.yield();
            ids.add(id);
        }

        public boolean markIfAbsent(String id) {
            return ids.add(id);
        }

        public void release(String id) {
            ids.remove(id);
        }
    }

    static final class FakeAccounts implements AccountGateway {
        final AtomicReference<BigDecimal> balance = new AtomicReference<>(BigDecimal.ZERO);
        volatile boolean failNext;

        public void credit(String accountId, BigDecimal amount) {
            if (failNext) {
                failNext = false;
                throw new IllegalStateException("core banking timeout");
            }
            try {
                Thread.sleep(2);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            balance.accumulateAndGet(amount, BigDecimal::add);
        }
    }

    @Test
    void concurrentDuplicatesAreAppliedOnce() throws Exception {
        for (int round = 0; round < 5; round++) {
            FakeAccounts accounts = new FakeAccounts();
            PaymentEventUseCase useCase = new PaymentEventUseCase(accounts, new FakeProcessed());
            PaymentEvent event = new PaymentEvent("evt-" + round, "acc-1", new BigDecimal("10"));
            ExecutorService pool = Executors.newFixedThreadPool(16);
            CountDownLatch start = new CountDownLatch(1);
            List<Future<Boolean>> results = new ArrayList<>();
            for (int i = 0; i < 32; i++) {
                results.add(pool.submit(() -> {
                    start.await();
                    return useCase.handle(event);
                }));
            }
            start.countDown();
            int applied = 0;
            for (Future<Boolean> result : results) {
                if (result.get()) {
                    applied++;
                }
            }
            pool.shutdown();
            assertEquals(1, applied, "exactly one invocation must report applying the event");
            assertEquals(0, new BigDecimal("10").compareTo(accounts.balance.get()), "credited once");
        }
    }

    @Test
    void failedCreditCanBeRetried() {
        FakeAccounts accounts = new FakeAccounts();
        FakeProcessed processed = new FakeProcessed();
        PaymentEventUseCase useCase = new PaymentEventUseCase(accounts, processed);
        PaymentEvent event = new PaymentEvent("evt-x", "acc-1", new BigDecimal("7"));
        accounts.failNext = true;
        assertThrows(RuntimeException.class, () -> useCase.handle(event));
        assertTrue(useCase.handle(event), "redelivery after a failure must apply the event");
        assertEquals(0, new BigDecimal("7").compareTo(accounts.balance.get()));
    }

    @Test
    void invalidAmountIsRejectedWithoutMarking() {
        FakeProcessed processed = new FakeProcessed();
        PaymentEventUseCase useCase = new PaymentEventUseCase(new FakeAccounts(), processed);
        assertThrows(RuntimeException.class,
                () -> useCase.handle(new PaymentEvent("evt-0", "acc-1", BigDecimal.ZERO)));
        assertTrue(processed.ids.isEmpty());
    }
}
