"""Cálculo de totales y payload de órdenes."""


def total(prices):
    """prices: lista de importes como strings ('10.10'). Devuelve el total con 2 decimales."""
    return round(sum(float(p) for p in prices), 2)


def to_payload(order_id, account_id, prices):
    return {"order_id": order_id, "account_id": account_id, "total": str(total(prices))}
