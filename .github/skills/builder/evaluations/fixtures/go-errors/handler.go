package accounts

import (
	"encoding/json"
	"net/http"
)

// NewHandler expone GET /accounts/{id}/balance.
func NewHandler(svc *Service) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /accounts/{id}/balance", func(w http.ResponseWriter, r *http.Request) {
		balance, err := svc.Balance(r.Context(), r.PathValue("id"))
		if err != nil {
			if err.Error() == "account not found" {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]int64{"balance": balance})
	})
	return mux
}
