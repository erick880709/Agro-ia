package batching

import (
	"errors"
	"reflect"
	"testing"
)

func TestOracleBatches(t *testing.T) {
	cases := []struct {
		name string
		ids  []string
		size int
		want [][]string
	}{
		{"exact", []string{"a", "b", "c", "d"}, 2, [][]string{{"a", "b"}, {"c", "d"}}},
		{"partial last", []string{"a", "b", "c"}, 2, [][]string{{"a", "b"}, {"c"}}},
		{"bigger than input", []string{"a"}, 5, [][]string{{"a"}}},
		{"empty", nil, 3, nil},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got, err := Batches(tc.ids, tc.size)
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if len(got) == 0 && len(tc.want) == 0 {
				return
			}
			if !reflect.DeepEqual(got, tc.want) {
				t.Fatalf("Batches(%v, %d) = %v, want %v", tc.ids, tc.size, got, tc.want)
			}
		})
	}
	for _, size := range []int{0, -1} {
		if _, err := Batches([]string{"a"}, size); !errors.Is(err, ErrInvalidSize) {
			t.Fatalf("size %d: err = %v, want ErrInvalidSize", size, err)
		}
	}
}

func TestOracleBatchesDoNotAlias(t *testing.T) {
	ids := []string{"a", "b", "c", "d"}
	got, err := Batches(ids, 2)
	if err != nil || len(got) != 2 {
		t.Fatalf("Batches = %v, %v", got, err)
	}
	got[0] = append(got[0], "x")
	if ids[2] != "c" {
		t.Fatalf("appending to a batch overwrote the input: %v", ids)
	}
}

func TestOracleRegion(t *testing.T) {
	if got := Region(""); got != "co-central" {
		t.Fatalf(`Region("") = %q, want "co-central"`, got)
	}
	if got := Region("co-north"); got != "co-north" {
		t.Fatalf(`Region("co-north") = %q`, got)
	}
}
