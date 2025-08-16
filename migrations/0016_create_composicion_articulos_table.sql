CREATE TABLE ComposicionArticulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articulo_final_id INTEGER NOT NULL, -- El ID del producto de "Empaquetado Propio"
    componente_id INTEGER NOT NULL,     -- El ID del artículo a granel que se usa
    cantidad REAL NOT NULL,             -- La cantidad del componente a granel que se descuenta
    FOREIGN KEY (articulo_final_id) REFERENCES Articulos(id),
    FOREIGN KEY (componente_id) REFERENCES Articulos(id)
);