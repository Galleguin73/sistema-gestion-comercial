-- migrations/0013_add_descuentos_to_ventas.sql

-- Añade una columna a la tabla de detalles para descuentos por ítem
ALTER TABLE DetalleVenta
ADD COLUMN descuento_monto REAL NOT NULL DEFAULT 0.0;

-- Añade una columna a la tabla principal de ventas para descuentos sobre el total
ALTER TABLE Ventas
ADD COLUMN descuento_total REAL NOT NULL DEFAULT 0.0;