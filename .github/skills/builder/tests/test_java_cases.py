import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'evaluate_builder.py'
spec = importlib.util.spec_from_file_location('evaluate_builder_java', SCRIPT)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)

CASES = ('java-bugfix', 'java-scaffold-boundary', 'java-version-gate', 'java-idempotency')
HAS_JDK = all(shutil.which(t) for t in ('javac', 'java')) and harness.requirement_available('junit-standalone')
SKIP = 'Requires a JDK and the JUnit console standalone jar (BUILDER_JUNIT_STANDALONE)'
UC = 'domain/usecase/src/main/java/co/com/bank/usecase/'

INTEREST_OK = '''package co.com.bank.usecase.interest;

import co.com.bank.model.exception.BusinessErrorType;
import co.com.bank.model.exception.BusinessException;

import java.math.BigDecimal;
import java.math.RoundingMode;

public class InterestUseCase {

    private static final BigDecimal MONTHS_PERCENT = BigDecimal.valueOf(1200);

    public BigDecimal monthlyInterest(BigDecimal principal, BigDecimal annualRatePercent) {
        if (annualRatePercent.signum() < 0 || annualRatePercent.compareTo(BigDecimal.valueOf(100)) > 0) {
            throw new BusinessException(BusinessErrorType.INVALID_RATE);
        }
        return principal.multiply(annualRatePercent).divide(MONTHS_PERCENT, 2, RoundingMode.HALF_EVEN);
    }
}
'''
INTEREST_HALF_UP = INTEREST_OK.replace('RoundingMode.HALF_EVEN', 'RoundingMode.HALF_UP')

BLOCK_OK = '''package co.com.bank.usecase.blockcard;

import co.com.bank.model.audit.AuditEvent;
import co.com.bank.model.audit.gateways.AuditGateway;
import co.com.bank.model.card.Card;
import co.com.bank.model.card.CardStatus;
import co.com.bank.model.card.gateways.CardRepository;
import co.com.bank.model.exception.BusinessErrorType;
import co.com.bank.model.exception.BusinessException;

public class BlockCardUseCase {

    private final CardRepository cardRepository;
    private final AuditGateway auditGateway;

    public BlockCardUseCase(CardRepository cardRepository, AuditGateway auditGateway) {
        this.cardRepository = cardRepository;
        this.auditGateway = auditGateway;
    }

    public Card block(String cardId, String reason) {
        Card card = cardRepository.findById(cardId)
                .orElseThrow(() -> new BusinessException(BusinessErrorType.CARD_NOT_FOUND));
        if (card.status() == CardStatus.BLOCKED) {
            return card;
        }
        Card saved = cardRepository.save(card.withStatus(CardStatus.BLOCKED));
        auditGateway.record(new AuditEvent("CARD_BLOCKED", cardId, "reason=" + reason));
        return saved;
    }
}
'''
BLOCK_SPRING = BLOCK_OK.replace('public class BlockCardUseCase {',
    '@org.springframework.transaction.annotation.Transactional\npublic class BlockCardUseCase {')
BLOCK_ADAPTER = BLOCK_OK.replace('import co.com.bank.model.audit.gateways.AuditGateway;',
    'import co.com.bank.model.audit.gateways.AuditGateway;\nimport co.com.bank.audit.AuditLogAdapter;')
BLOCK_NOT_IDEMPOTENT = BLOCK_OK.replace('''        if (card.status() == CardStatus.BLOCKED) {
            return card;
        }
''', '')
REQUEST_CLASS = 'package co.com.bank.usecase.blockcard;\n\npublic record BlockCardRequest(String cardId, String reason) {\n}\n'

STATEMENT_OK = '''package co.com.bank.usecase.statement;

import co.com.bank.model.exception.BusinessErrorType;
import co.com.bank.model.exception.BusinessException;
import co.com.bank.model.movement.Deposit;
import co.com.bank.model.movement.Fee;
import co.com.bank.model.movement.Movement;
import co.com.bank.model.movement.Withdrawal;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class StatementUseCase {

    public List<Movement> latest(List<Movement> movements, int limit) {
        if (limit <= 0) {
            throw new BusinessException(BusinessErrorType.INVALID_LIMIT);
        }
        List<Movement> copy = new ArrayList<>(movements);
        Collections.reverse(copy);
        return List.copyOf(copy.subList(0, Math.min(limit, copy.size())));
    }

    public String describe(Movement movement) {
        if (movement instanceof Deposit d) {
            return "Consignación " + d.origin() + " +" + d.amount().toPlainString();
        }
        if (movement instanceof Withdrawal w) {
            return "Retiro " + w.channel() + " -" + w.amount().toPlainString();
        }
        if (movement instanceof Fee f) {
            return "Comisión " + f.concept() + " -" + f.amount().toPlainString();
        }
        throw new IllegalArgumentException("Unknown movement " + movement);
    }
}
'''
STATEMENT_JAVA21 = STATEMENT_OK.replace('''        List<Movement> copy = new ArrayList<>(movements);
        Collections.reverse(copy);
        return List.copyOf(copy.subList(0, Math.min(limit, copy.size())));''',
'''        List<Movement> reversed = movements.reversed();
        return List.copyOf(reversed.subList(0, Math.min(limit, reversed.size())));''')
STATEMENT_MUTATES = STATEMENT_OK.replace('''        List<Movement> copy = new ArrayList<>(movements);
        Collections.reverse(copy);''', '''        List<Movement> copy = movements;
        Collections.reverse(copy);''')

PAYMENT_OK = '''package co.com.bank.usecase.payment;

import co.com.bank.model.exception.BusinessErrorType;
import co.com.bank.model.exception.BusinessException;
import co.com.bank.model.payment.PaymentEvent;
import co.com.bank.model.payment.gateways.AccountGateway;
import co.com.bank.model.payment.gateways.ProcessedEventGateway;

public class PaymentEventUseCase {

    private final AccountGateway accountGateway;
    private final ProcessedEventGateway processedEvents;

    public PaymentEventUseCase(AccountGateway accountGateway, ProcessedEventGateway processedEvents) {
        this.accountGateway = accountGateway;
        this.processedEvents = processedEvents;
    }

    public boolean handle(PaymentEvent event) {
        if (event.amount().signum() <= 0) {
            throw new BusinessException(BusinessErrorType.INVALID_AMOUNT);
        }
        if (!processedEvents.markIfAbsent(event.eventId())) {
            return false;
        }
        try {
            accountGateway.credit(event.accountId(), event.amount());
            return true;
        } catch (RuntimeException e) {
            processedEvents.release(event.eventId());
            throw e;
        }
    }
}
'''
PAYMENT_NO_RELEASE = PAYMENT_OK.replace('''        try {
            accountGateway.credit(event.accountId(), event.amount());
            return true;
        } catch (RuntimeException e) {
            processedEvents.release(event.eventId());
            throw e;
        }''', '''        accountGateway.credit(event.accountId(), event.amount());
        return true;''')


class JavaCaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def prepare(self, case):
        path = self.root / case
        harness.prepare(case, path)
        return path

    def write(self, path, relative, text):
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def assertCase(self, case, path, passed):
        result = harness.check(case, path)
        self.assertEqual(result['passed'], passed, result['failures'])

    def test_prepare_never_copies_oracles(self):
        for case in CASES:
            with self.subTest(case=case):
                names = {p.name for p in self.prepare(case).rglob('*')}
                self.assertIn('TASK.md', names)
                self.assertFalse(any(n.startswith('Oracle') for n in names))

    def test_missing_junit_is_an_invalid_environment(self):
        path = self.prepare('java-bugfix')
        with patch.dict(os.environ, {'BUILDER_JUNIT_STANDALONE': '/nonexistent.jar'}):
            with self.assertRaises(ValueError):
                harness.check('java-bugfix', path)

    @unittest.skipUnless(HAS_JDK, SKIP)
    def test_java_bugfix(self):
        path = self.prepare('java-bugfix')
        self.assertCase('java-bugfix', path, False)
        self.write(path, UC + 'interest/InterestUseCase.java', INTEREST_HALF_UP)
        self.assertCase('java-bugfix', path, False)
        self.write(path, UC + 'interest/InterestUseCase.java', INTEREST_OK)
        self.assertCase('java-bugfix', path, True)

    @unittest.skipUnless(HAS_JDK, SKIP)
    def test_java_scaffold_boundary(self):
        path = self.prepare('java-scaffold-boundary')
        self.assertCase('java-scaffold-boundary', path, False)
        target = UC + 'blockcard/BlockCardUseCase.java'
        for wrong in (BLOCK_SPRING, BLOCK_ADAPTER, BLOCK_NOT_IDEMPOTENT):
            self.write(path, target, wrong)
            self.assertCase('java-scaffold-boundary', path, False)
        self.write(path, target, BLOCK_OK)
        self.assertCase('java-scaffold-boundary', path, True)
        self.write(path, UC + 'blockcard/BlockCardRequest.java', REQUEST_CLASS)
        self.assertCase('java-scaffold-boundary', path, False)

    @unittest.skipUnless(HAS_JDK, SKIP)
    def test_java_version_gate(self):
        path = self.prepare('java-version-gate')
        self.assertCase('java-version-gate', path, False)
        target = UC + 'statement/StatementUseCase.java'
        for wrong in (STATEMENT_JAVA21, STATEMENT_MUTATES):
            self.write(path, target, wrong)
            self.assertCase('java-version-gate', path, False)
        self.write(path, target, STATEMENT_OK)
        self.assertCase('java-version-gate', path, True)

    @unittest.skipUnless(HAS_JDK, SKIP)
    def test_java_idempotency(self):
        path = self.prepare('java-idempotency')
        self.assertCase('java-idempotency', path, False)
        target = UC + 'payment/PaymentEventUseCase.java'
        self.write(path, target, PAYMENT_NO_RELEASE)
        self.assertCase('java-idempotency', path, False)
        self.write(path, target, PAYMENT_OK)
        self.assertCase('java-idempotency', path, True)


if __name__ == '__main__':
    unittest.main()
