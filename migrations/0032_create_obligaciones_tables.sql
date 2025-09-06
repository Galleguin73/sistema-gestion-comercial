-- Tabla para configurar los tipos de obligaciones que se pueden pagar
CREATE TABLE TiposDeObligacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    categoria TEXT NOT NULL, -- Impuestos, Servicios, Alquileres, Otros
    descripcion TEXT
);

-- Tabla principal para la agenda de pagos
CREATE TABLE AgendaDeObligaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_obligacion_id INTEGER NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    periodo TEXT, -- Ej: 'Septiembre 2025'
    monto_original REAL NOT NULL,
    monto_pagado REAL DEFAULT 0.0,
    estado TEXT NOT NULL, -- PENDIENTE, PAGADA, ANULADA
    fecha_pago DATE,
    observaciones TEXT,
    caja_id_pago INTEGER, -- Para saber desde qué caja se pagó
    FOREIGN KEY (tipo_obligacion_id) REFERENCES TiposDeObligacion(id),
    FOREIGN KEY (caja_id_pago) REFERENCES Caja(id)
);