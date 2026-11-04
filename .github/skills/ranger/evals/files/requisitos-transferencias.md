# Transferencias — requisitos confirmados

- RF-01 / CA-01: con saldo suficiente, una transferencia positiva descuenta exactamente el monto y crea un movimiento con referencia única.
- RF-02 / CA-02: una transferencia con monto mayor al saldo se rechaza sin cambiar saldo ni movimientos.
- RF-03 / CA-03: un monto menor o igual a cero se rechaza sin cambiar estado.

Alcance de esta solicitud: plan documental de pruebas unitarias del servicio de dominio. No hay navegador ni entorno desplegado. Casos en memoria. No se solicitan tests implementados ni ejecución.
