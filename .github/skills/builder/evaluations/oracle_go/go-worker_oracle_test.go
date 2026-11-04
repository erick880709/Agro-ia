package credits

import (
	"context"
	"errors"
	"sync"
	"testing"
)

func TestOracleLifecycle(t *testing.T) {
	w := NewCreditWorker()
	if _, err := w.Handle(context.Background(), "m-0", 5); !errors.Is(err, ErrNotRunning) {
		t.Fatalf("before Start: err = %v, want ErrNotRunning", err)
	}
	w.Start()
	if got, err := w.Handle(context.Background(), "m-1", 10); err != nil || got != 10 {
		t.Fatalf("Handle = %d, %v; want 10, nil", got, err)
	}
	w.Stop()
	if _, err := w.Handle(context.Background(), "m-2", 5); !errors.Is(err, ErrNotRunning) {
		t.Fatalf("after Stop: err = %v, want ErrNotRunning", err)
	}
}

func TestOracleConcurrentDuplicatesAppliedOnce(t *testing.T) {
	w := NewCreditWorker()
	w.Start()
	var wg sync.WaitGroup
	for i := 0; i < 64; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if _, err := w.Handle(context.Background(), "dup", 10); err != nil {
				t.Errorf("Handle: %v", err)
			}
		}()
	}
	wg.Wait()
	if got, err := w.Handle(context.Background(), "m-2", 5); err != nil || got != 15 {
		t.Fatalf("balance after 64 duplicates + 1 new = %d, %v; want 15, nil", got, err)
	}
}

func TestOracleCanceledContextHasNoEffect(t *testing.T) {
	w := NewCreditWorker()
	w.Start()
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := w.Handle(ctx, "m-1", 10); !errors.Is(err, context.Canceled) {
		t.Fatalf("canceled ctx: err = %v, want context.Canceled", err)
	}
	if got, err := w.Handle(context.Background(), "m-1", 10); err != nil || got != 10 {
		t.Fatalf("message after canceled attempt = %d, %v; want 10, nil (not marked processed)", got, err)
	}
}
