-- migrations/0003_add_estado_to_compras.sql
ALTER TABLE Compras ADD COLUMN estado TEXT DEFAULT 'IMPAGA';