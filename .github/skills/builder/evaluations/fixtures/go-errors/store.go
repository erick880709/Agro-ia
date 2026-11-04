// Package accounts expone saldos de cuentas.
package accounts

import (
	"context"
	"errors"
	"sync"
)

// ErrNotFound indica que la cuenta no existe.
var ErrNotFound = errors.New("account not found")

// Account es una cuenta con saldo en centavos.
type Account struct {
	ID      string
	Balance int64
}

// Store obtiene cuentas.
type Store interface {
	Find(ctx context.Context, id string) (Account, error)
}

// MemoryStore es un Store en memoria.
type MemoryStore struct {
	mu       sync.RWMutex
	accounts map[string]Account
}

// NewMemoryStore crea un MemoryStore con las cuentas dadas.
func NewMemoryStore(accounts ...Account) *MemoryStore {
	s := &MemoryStore{accounts: make(map[string]Account, len(accounts))}
	for _, a := range accounts {
		s.accounts[a.ID] = a
	}
	return s
}

// Find devuelve la cuenta o ErrNotFound.
func (s *MemoryStore) Find(_ context.Context, id string) (Account, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	a, ok := s.accounts[id]
	if !ok {
		return Account{}, ErrNotFound
	}
	return a, nil
}
