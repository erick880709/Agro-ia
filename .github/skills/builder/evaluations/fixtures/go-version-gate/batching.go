// Package batching agrupa identificadores para envíos a un proveedor.
package batching

import "errors"

// ErrInvalidSize indica un tamaño de lote no positivo.
var ErrInvalidSize = errors.New("batch size must be positive")

// Batches divide ids en lotes consecutivos de como máximo size elementos.
func Batches(ids []string, size int) ([][]string, error) {
	// TODO: implementar.
	return nil, nil
}

// Region devuelve region o la región por defecto "co-central" si está vacía.
func Region(region string) string {
	// TODO: implementar.
	return ""
}
