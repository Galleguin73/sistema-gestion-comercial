-- migrations/0017_create_composicion_articulos_table.sql
CREATE TABLE ComposicionArticulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articulo_final_id INTEGER NOT NULL,       -- El ID del producto empaquetado
    articulo_componente_id INTEGER NOT NULL,  -- El ID del producto a granel que lo compone
    cantidad_componente REAL NOT NULL,        -- Cuánto del componente se usa
    FOREIGN KEY (articulo_final_id) REFERENCES Articulos(id) ON DELETE CASCADE,
    FOREIGN KEY (articulo_componente_id) REFERENCES Articulos(id) ON DELETE CASCADE
);