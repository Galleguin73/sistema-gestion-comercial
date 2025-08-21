-- migrations/0023_add_subtotal_to_compras_detalle.sql
ALTER TABLE ComprasDetalle
ADD COLUMN subtotal REAL;