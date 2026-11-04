package accounts

import (
	"context"
	"fmt"
)

// Service resuelve consultas de saldo.
type Service struct {
	store Store
}

// NewService crea un Service.
func NewService(store Store) *Service {
	return &Service{store: store}
}

// Balance devuelve el saldo de la cuenta id.
func (s *Service) Balance(ctx context.Context, id string) (int64, error) {
	a, err := s.store.Find(ctx, id)
	if err != nil {
		return 0, fmt.Errorf("balance lookup failed: %v", err)
	}
	return a.Balance, nil
}
