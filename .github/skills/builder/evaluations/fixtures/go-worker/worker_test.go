package credits

import (
	"context"
	"errors"
	"testing"
)

func TestHandleRequiresRunning(t *testing.T) {
	w := NewCreditWorker()
	if _, err := w.Handle(context.Background(), "m-1", 10); !errors.Is(err, ErrNotRunning) {
		t.Fatalf("Handle before Start: err = %v, want ErrNotRunning", err)
	}
}

func TestHandleDuplicateAppliedOnce(t *testing.T) {
	w := NewCreditWorker()
	w.Start()
	ctx := context.Background()
	if got, _ := w.Handle(ctx, "m-1", 10); got != 10 {
		t.Fatalf("first Handle = %d, want 10", got)
	}
	if got, _ := w.Handle(ctx, "m-1", 10); got != 10 {
		t.Fatalf("duplicate Handle = %d, want 10", got)
	}
}
