package pricing

import "testing"

func TestOracleTotal(t *testing.T) {
	cases := []struct {
		name     string
		amounts  []int64
		discount int64
		want     int64
	}{
		{"discount over the whole sum", []int64{4000, 6000}, 10, 9000},
		{"zero discount", []int64{2500, 7500}, 0, 10000},
		{"empty", nil, 20, 0},
		{"three items", []int64{1500, 3500, 5000}, 20, 8000},
		{"full discount", []int64{1000}, 100, 0},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := Total(tc.amounts, tc.discount); got != tc.want {
				t.Fatalf("Total(%v, %d) = %d, want %d", tc.amounts, tc.discount, got, tc.want)
			}
		})
	}
}
