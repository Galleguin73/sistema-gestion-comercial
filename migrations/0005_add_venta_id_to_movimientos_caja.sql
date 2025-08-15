-- Contenido para 0005_add_venta_id_to_movimientos_caja.sql

ALTER TABLE MovimientosCaja 
ADD COLUMN venta_id INTEGER REFERENCES Ventas(id) ON DELETE SET NULL;