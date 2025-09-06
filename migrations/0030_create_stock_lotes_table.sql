-- migrations/0030_create_stock_lotes_table.sql

-- Creamos la nueva tabla para gestionar el stock por lotes y vencimientos
CREATE TABLE IF NOT EXISTS StockLotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articulo_id INTEGER NOT NULL,
    compra_detalle_id INTEGER, -- Para saber de qué compra vino este lote
    cantidad REAL NOT NULL,
    lote TEXT,
    fecha_vencimiento DATE,
    fecha_ingreso DATETIME DEFAULT CURRENT_TIMESTAMP,
    activo INTEGER DEFAULT 1, -- Para 'desactivar' un lote cuando se agote
    FOREIGN KEY (articulo_id) REFERENCES Articulos(id) ON DELETE CASCADE,
    FOREIGN KEY (compra_detalle_id) REFERENCES ComprasDetalle(id) ON DELETE SET NULL
);

-- Ahora que el stock se gestiona en la nueva tabla, las siguientes columnas
-- en la tabla 'Articulos' ya no son la fuente principal de verdad.
-- Podríamos eliminarlas, pero por seguridad y para mantener datos históricos,
-- simplemente dejaremos de usarlas como fuente principal para el stock actual.
-- El stock total ahora se calculará SUMANDO las cantidades de 'StockLotes'.

-- Nota: No es necesario ejecutar un ALTER TABLE para Articulos aquí,
-- ya que solo cambiaremos la lógica en el código de Python.

-- También agregamos las columnas que faltaban en ComprasDetalle,
-- para que cada línea de una compra guarde su propio lote y vencimiento.
ALTER TABLE ComprasDetalle ADD COLUMN lote TEXT;
ALTER TABLE ComprasDetalle ADD COLUMN fecha_vencimiento DATE;
ALTER TABLE ComprasDetalle ADD COLUMN iva REAL;