package accounts

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

type oracleFailingStore struct{}

func (oracleFailingStore) Find(context.Context, string) (Account, error) {
	return Account{}, errors.New("dial tcp 10.9.8.7:5432: secret-host refused")
}

func oracleGet(t *testing.T, h http.Handler, path string) *httptest.ResponseRecorder {
	t.Helper()
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, path, nil))
	return rec
}

func TestOracleServicePreservesErrorChain(t *testing.T) {
	svc := NewService(NewMemoryStore(Account{ID: "a-1", Balance: 100}))
	_, err := svc.Balance(context.Background(), "missing")
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("Balance(missing) err = %v; errors.Is(err, ErrNotFound) must hold", err)
	}
}

func TestOracleHandlerContract(t *testing.T) {
	h := NewHandler(NewService(NewMemoryStore(Account{ID: "a-1", Balance: 100})))
	rec := oracleGet(t, h, "/accounts/a-1/balance")
	if rec.Code != http.StatusOK || !strings.HasPrefix(rec.Header().Get("Content-Type"), "application/json") {
		t.Fatalf("existing: code %d, content-type %q", rec.Code, rec.Header().Get("Content-Type"))
	}
	var body map[string]int64
	if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil || body["balance"] != 100 || len(body) != 1 {
		t.Fatalf("existing: body %q", rec.Body.String())
	}
	if rec := oracleGet(t, h, "/accounts/missing/balance"); rec.Code != http.StatusNotFound {
		t.Fatalf("missing: code %d, want 404", rec.Code)
	}
	failing := NewHandler(NewService(oracleFailingStore{}))
	rec = oracleGet(t, failing, "/accounts/a-1/balance")
	if rec.Code != http.StatusInternalServerError {
		t.Fatalf("store failure: code %d, want 500", rec.Code)
	}
	if strings.Contains(rec.Body.String(), "secret-host") || strings.Contains(rec.Body.String(), "10.9.8.7") {
		t.Fatalf("store failure leaks internal detail: %q", rec.Body.String())
	}
}
