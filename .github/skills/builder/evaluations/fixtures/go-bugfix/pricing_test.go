package pricing

import "testing"

func TestTotalEmpty(t *testing.T) {
	if got := Total(nil, 20); got != 0 {
		t.Fatalf("Total(nil, 20) = %d, want 0", got)
	}
}
