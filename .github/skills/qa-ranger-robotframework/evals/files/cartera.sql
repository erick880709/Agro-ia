-- Esquema y datos SINTÉTICOS para evaluación (SQLite). Crear con: sqlite3 cartera.db < cartera.sql
CREATE TABLE cuentas (
  numero   TEXT PRIMARY KEY,
  estado   TEXT NOT NULL,
  saldo    NUMERIC NOT NULL
);
CREATE TABLE movimientos (
  id       INTEGER PRIMARY KEY,
  cuenta   TEXT REFERENCES cuentas(numero),
  monto    NUMERIC NOT NULL
);
CREATE TABLE parametros (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
INSERT INTO cuentas VALUES ('9001','ACTIVA',1000),('9002','BLOQUEADA',0),('9003','CERRADA',0);
INSERT INTO movimientos VALUES (1,'9001',250),(2,'9001',-50),(3,'9999',10);
INSERT INTO parametros VALUES ('TOPE_DIARIO','5000000');
