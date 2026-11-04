// Package credits aplica créditos recibidos desde una cola.
package credits

import (
	"context"
	"errors"
	"sync"
)

// ErrNotRunning indica que el worker no acepta mensajes.
var ErrNotRunning = errors.New("worker is not running")

// CreditWorker aplica créditos a un saldo en memoria.
type CreditWorker struct {
	mu        sync.Mutex
	running   bool
	balance   int64
	processed map[string]struct{}
}

// NewCreditWorker crea un worker detenido.
func NewCreditWorker() *CreditWorker {
	return &CreditWorker{processed: make(map[string]struct{})}
}

// Start habilita el procesamiento.
func (w *CreditWorker) Start() {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.running = true
}

// Stop deshabilita el procesamiento.
func (w *CreditWorker) Stop() {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.running = false
}

// Handle aplica el crédito del mensaje y devuelve el saldo resultante.
func (w *CreditWorker) Handle(ctx context.Context, messageID string, amount int64) (int64, error) {
	if !w.running {
		return 0, ErrNotRunning
	}
	w.balance += amount
	w.processed[messageID] = struct{}{}
	return w.balance, nil
}
