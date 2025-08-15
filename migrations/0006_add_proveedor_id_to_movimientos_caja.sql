-- Contenido para 0006_add_proveedor_id_to_movimientos_caja.sql

ALTER TABLE MovimientosCaja
ADD COLUMN proveedor_id INTEGER REFERENCES Proveedores(id) ON DELETE SET NULL;