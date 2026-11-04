// Package pricing calcula importes de órdenes en centavos.
package pricing

// Total suma los importes y aplica un descuento porcentual (0-100).
func Total(amounts []int64, discountPct int64) int64 {
	if len(amounts) == 0 {
		return 0
	}
	sum := amounts[0] - amounts[0]*discountPct/100
	for _, amount := range amounts[1:] {
		sum += amount
	}
	return sum
}
