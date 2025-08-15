-- migrations/0010_create_ajustes_stock_table.sql
CREATE TABLE AjustesStock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articulo_id INTEGER NOT NULL,
    fecha DATETIME NOT NULL,
    tipo_ajuste TEXT NOT NULL, -- 'INGRESO' o 'EGRESO'
    cantidad REAL NOT NULL,
    concepto TEXT,
    stock_anterior REAL NOT NULL,
    stock_nuevo REAL NOT NULL,
    FOREIGN KEY (articulo_id) REFERENCES Articulos(id)
);