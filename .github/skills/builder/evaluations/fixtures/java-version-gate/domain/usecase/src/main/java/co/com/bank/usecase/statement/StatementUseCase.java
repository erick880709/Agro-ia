package co.com.bank.usecase.statement;

import co.com.bank.model.movement.Movement;

import java.util.List;

public class StatementUseCase {

    /**
     * Devuelve los últimos {@code limit} movimientos, del más reciente al más antiguo.
     * La lista de entrada viene ordenada del más antiguo al más reciente y no debe modificarse.
     */
    public List<Movement> latest(List<Movement> movements, int limit) {
        throw new UnsupportedOperationException("TODO");
    }

    /**
     * Texto para el extracto: "Consignación <origin> +<amount>", "Retiro <channel> -<amount>"
     * o "Comisión <concept> -<amount>", con amount en formato plano (toPlainString).
     */
    public String describe(Movement movement) {
        throw new UnsupportedOperationException("TODO");
    }
}
