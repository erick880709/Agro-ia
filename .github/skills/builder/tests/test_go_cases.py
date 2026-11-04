import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'evaluate_builder.py'
spec = importlib.util.spec_from_file_location('evaluate_builder_go', SCRIPT)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)

HAS_GO = shutil.which('go') is not None

PRICING_OK = '''package pricing

// Total suma los importes y aplica un descuento porcentual (0-100).
func Total(amounts []int64, discountPct int64) int64 {
	var sum int64
	for _, amount := range amounts {
		sum += amount
	}
	return sum - sum*discountPct/100
}
'''

WORKER_OK = '''package credits

import (
	"context"
	"errors"
	"sync"
)

var ErrNotRunning = errors.New("worker is not running")

type CreditWorker struct {
	mu        sync.Mutex
	running   bool
	balance   int64
	processed map[string]struct{}
}

func NewCreditWorker() *CreditWorker {
	return &CreditWorker{processed: make(map[string]struct{})}
}

func (w *CreditWorker) Start() { w.mu.Lock(); defer w.mu.Unlock(); w.running = true }

func (w *CreditWorker) Stop() { w.mu.Lock(); defer w.mu.Unlock(); w.running = false }

func (w *CreditWorker) Handle(ctx context.Context, messageID string, amount int64) (int64, error) {
	if err := ctx.Err(); err != nil {
		return 0, err
	}
	w.mu.Lock()
	defer w.mu.Unlock()
	if !w.running {
		return 0, ErrNotRunning
	}
	if _, seen := w.processed[messageID]; !seen {
		w.balance += amount
		w.processed[messageID] = struct{}{}
	}
	return w.balance, nil
}
'''

# Deduplicates but keeps the unsynchronized read of running and map access.
WORKER_RACY = WORKER_OK.replace('''	w.mu.Lock()
	defer w.mu.Unlock()
	if !w.running {''', '''	if !w.running {''')

BATCHING_OK = '''package batching

import "errors"

var ErrInvalidSize = errors.New("batch size must be positive")

func Batches(ids []string, size int) ([][]string, error) {
	if size <= 0 {
		return nil, ErrInvalidSize
	}
	var out [][]string
	for start := 0; start < len(ids); start += size {
		end := min(start+size, len(ids))
		out = append(out, ids[start:end:end])
	}
	return out, nil
}

func Region(region string) string {
	if region == "" {
		return "co-central"
	}
	return region
}
'''

BATCHING_TOO_NEW = BATCHING_OK.replace('''	if region == "" {
		return "co-central"
	}
	return region''', '''	return cmp.Or(region, "co-central")''').replace('import "errors"', 'import (\n\t"cmp"\n\t"errors"\n)')

BATCHING_ALIASING = BATCHING_OK.replace('ids[start:end:end]', 'ids[start:end]')

SERVICE_OK = '''package accounts

import (
	"context"
	"fmt"
)

type Service struct {
	store Store
}

func NewService(store Store) *Service {
	return &Service{store: store}
}

func (s *Service) Balance(ctx context.Context, id string) (int64, error) {
	a, err := s.store.Find(ctx, id)
	if err != nil {
		return 0, fmt.Errorf("finding account %s: %w", id, err)
	}
	return a.Balance, nil
}
'''

HANDLER_OK = '''package accounts

import (
	"encoding/json"
	"errors"
	"net/http"
)

func NewHandler(svc *Service) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /accounts/{id}/balance", func(w http.ResponseWriter, r *http.Request) {
		balance, err := svc.Balance(r.Context(), r.PathValue("id"))
		switch {
		case errors.Is(err, ErrNotFound):
			http.Error(w, "not found", http.StatusNotFound)
			return
		case err != nil:
			http.Error(w, "internal error", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]int64{"balance": balance})
	})
	return mux
}
'''


class GoCaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def prepare(self, case):
        path = self.root / case
        harness.prepare(case, path)
        return path

    def test_prepare_never_copies_oracles(self):
        for case in ('go-bugfix', 'go-worker', 'go-version-gate', 'go-errors'):
            with self.subTest(case=case):
                path = self.prepare(case)
                names = {p.name for p in path.rglob('*')}
                self.assertIn('TASK.md', names)
                self.assertFalse(any('oracle' in name for name in names))

    def test_missing_toolchain_is_an_invalid_environment_not_a_failure(self):
        path = self.prepare('go-bugfix')
        with patch.object(harness.shutil, 'which', return_value=None):
            with self.assertRaises(ValueError):
                harness.check('go-bugfix', path)

    @unittest.skipUnless(HAS_GO, 'Go toolchain not available')
    def test_go_bugfix(self):
        path = self.prepare('go-bugfix')
        self.assertFalse(harness.check('go-bugfix', path)['passed'])
        (path / 'pricing.go').write_text(PRICING_OK, encoding='utf-8')
        self.assertTrue(harness.check('go-bugfix', path)['passed'])
        (path / 'go.mod').write_text('module example.com/pricing\n\ngo 1.22\n')
        self.assertFalse(harness.check('go-bugfix', path)['passed'])

    @unittest.skipUnless(HAS_GO, 'Go toolchain not available')
    def test_go_worker_requires_synchronized_idempotency(self):
        path = self.prepare('go-worker')
        self.assertFalse(harness.check('go-worker', path)['passed'])
        (path / 'worker.go').write_text(WORKER_RACY, encoding='utf-8')
        self.assertFalse(harness.check('go-worker', path)['passed'])
        (path / 'worker.go').write_text(WORKER_OK, encoding='utf-8')
        result = harness.check('go-worker', path)
        self.assertTrue(result['passed'], result)
        (path / 'worker_test.go').write_text('package credits\n')
        self.assertFalse(harness.check('go-worker', path)['passed'])

    @unittest.skipUnless(HAS_GO, 'Go toolchain not available')
    def test_go_version_gate(self):
        path = self.prepare('go-version-gate')
        self.assertFalse(harness.check('go-version-gate', path)['passed'])
        (path / 'batching.go').write_text(BATCHING_TOO_NEW, encoding='utf-8')
        self.assertFalse(harness.check('go-version-gate', path)['passed'])
        (path / 'batching.go').write_text(BATCHING_ALIASING, encoding='utf-8')
        self.assertFalse(harness.check('go-version-gate', path)['passed'])
        (path / 'batching.go').write_text(BATCHING_OK, encoding='utf-8')
        result = harness.check('go-version-gate', path)
        self.assertTrue(result['passed'], result)

    @unittest.skipUnless(HAS_GO, 'Go toolchain not available')
    def test_go_errors(self):
        path = self.prepare('go-errors')
        self.assertFalse(harness.check('go-errors', path)['passed'])
        (path / 'service.go').write_text(SERVICE_OK, encoding='utf-8')
        self.assertFalse(harness.check('go-errors', path)['passed'])
        (path / 'handler.go').write_text(HANDLER_OK, encoding='utf-8')
        result = harness.check('go-errors', path)
        self.assertTrue(result['passed'], result)


if __name__ == '__main__':
    unittest.main()
