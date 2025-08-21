-- migrations/0024_add_saldo_to_compras.sql

-- Añade las nuevas columnas a la tabla de Compras
ALTER TABLE Compras ADD COLUMN saldo_pendiente REAL;
ALTER TABLE Compras ADD COLUMN fecha_vencimiento DATE;

-- Inicializa el saldo pendiente para las facturas que ya existen
-- A las impagas, les asigna el monto total como saldo pendiente.
UPDATE Compras
SET saldo_pendiente = monto_total
WHERE estado = 'IMPAGA';

-- A las pagadas o anuladas, les asigna saldo cero.
UPDATE Compras
SET saldo_pendiente = 0
WHERE estado IN ('PAGADA', 'ANULADA');