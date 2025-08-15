-- migrations/0011_add_estado_to_articulos.sql
ALTER TABLE Articulos
ADD COLUMN estado TEXT NOT NULL DEFAULT 'Activo';