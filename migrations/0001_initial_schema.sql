CREATE TABLE IF NOT EXISTS Clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cuit_dni TEXT UNIQUE, razon_social TEXT NOT NULL,
    nombre_fantasia TEXT, domicilio TEXT, localidad TEXT, provincia TEXT, email TEXT,
    telefono TEXT, persona_de_contacto TEXT, observaciones TEXT, condicion_iva TEXT,
    tipo_cuenta TEXT, cuenta_corriente_habilitada INTEGER DEFAULT 0,
    limite_cuenta_corriente REAL DEFAULT 0.00, saldo_cuenta_corriente REAL DEFAULT 0.00,
    fecha_alta DATE DEFAULT (date('now')), estado TEXT DEFAULT 'Activo'
);
CREATE TABLE IF NOT EXISTS Proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cuit_dni TEXT UNIQUE, razon_social TEXT NOT NULL,
    domicilio TEXT, localidad TEXT, provincia TEXT, email TEXT, telefono TEXT,
    persona_de_contacto TEXT, observaciones TEXT
);
CREATE TABLE IF NOT EXISTS Marcas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS Rubros (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS Subrubros (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, rubro_id INTEGER,
    FOREIGN KEY (rubro_id) REFERENCES Rubros(id)
);
CREATE TABLE IF NOT EXISTS Articulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_barras TEXT UNIQUE, nombre TEXT NOT NULL,
    marca_id INTEGER, subrubro_id INTEGER, stock REAL NOT NULL, precio_costo REAL,
    iva REAL, utilidad REAL, precio_venta REAL, unidad_de_medida TEXT,
    FOREIGN KEY (marca_id) REFERENCES Marcas(id),
    FOREIGN KEY (subrubro_id) REFERENCES Subrubros(id)
);
CREATE TABLE IF NOT EXISTS MediosDePago (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS Provincias (id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS Localidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, provincia_id INTEGER,
    FOREIGN KEY (provincia_id) REFERENCES Provincias(id)
);
CREATE TABLE IF NOT EXISTS Configuracion (
    id INTEGER PRIMARY KEY, razon_social TEXT, nombre_fantasia TEXT, cuit TEXT,
    condicion_iva TEXT, iibb TEXT, domicilio TEXT, ciudad TEXT, provincia TEXT,
    logo_path TEXT
);
CREATE TABLE IF NOT EXISTS Compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor_id INTEGER NOT NULL,
    numero_factura TEXT,
    fecha_compra DATE DEFAULT (date('now')),
    monto_total REAL,
    FOREIGN KEY (proveedor_id) REFERENCES Proveedores(id)
);
CREATE TABLE IF NOT EXISTS ComprasDetalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT, compra_id INTEGER NOT NULL, articulo_id INTEGER NOT NULL,
    cantidad REAL NOT NULL, precio_costo_unitario REAL NOT NULL,
    FOREIGN KEY (compra_id) REFERENCES Compras(id), FOREIGN KEY (articulo_id) REFERENCES Articulos(id)
);
CREATE TABLE IF NOT EXISTS CuentasCorrientesProveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT, proveedor_id INTEGER NOT NULL, compra_id INTEGER,
    fecha DATE DEFAULT (date('now')), tipo_movimiento TEXT NOT NULL, monto REAL NOT NULL,
    saldo_resultante REAL NOT NULL,
    FOREIGN KEY (proveedor_id) REFERENCES Proveedores(id), FOREIGN KEY (compra_id) REFERENCES Compras(id)
);
CREATE TABLE IF NOT EXISTS Caja (
    id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_apertura DATETIME NOT NULL, monto_inicial REAL NOT NULL,
    fecha_cierre DATETIME, monto_final_esperado REAL, monto_final_real REAL, diferencia REAL,
    estado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS MovimientosCaja (
    id INTEGER PRIMARY KEY AUTOINCREMENT, caja_id INTEGER NOT NULL, fecha DATETIME NOT NULL,
    tipo TEXT NOT NULL, concepto TEXT NOT NULL, monto REAL NOT NULL, medio_pago_id INTEGER,
    FOREIGN KEY (caja_id) REFERENCES Caja(id), FOREIGN KEY (medio_pago_id) REFERENCES MediosDePago(id)
);
CREATE TABLE IF NOT EXISTS Ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    usuario_id INTEGER,
    caja_id INTEGER,
    fecha_venta DATETIME NOT NULL,
    numero_comprobante TEXT, 
    monto_total REAL NOT NULL,
    tipo_comprobante TEXT,
    cae TEXT,
    vencimiento_cae DATE,
    FOREIGN KEY (cliente_id) REFERENCES Clientes(id),
    FOREIGN KEY (usuario_id) REFERENCES Usuarios(id),
    FOREIGN KEY (caja_id) REFERENCES Caja(id)
);
CREATE TABLE IF NOT EXISTS DetalleVenta (
    id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER NOT NULL, articulo_id INTEGER NOT NULL,
    cantidad REAL NOT NULL, precio_unitario REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES Ventas(id), FOREIGN KEY (articulo_id) REFERENCES Articulos(id)
);
CREATE TABLE IF NOT EXISTS VentasPagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER NOT NULL, medio_pago_id INTEGER NOT NULL,
    monto REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES Ventas(id), FOREIGN KEY (medio_pago_id) REFERENCES MediosDePago(id)
);
 CREATE TABLE IF NOT EXISTS CuentasCorrientesClientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    venta_id INTEGER,
    fecha DATE DEFAULT (date('now')),
    tipo_movimiento TEXT NOT NULL,
    monto REAL NOT NULL,
    saldo_resultante REAL NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES Clientes(id),
    FOREIGN KEY (venta_id) REFERENCES Ventas(id)
);
CREATE TABLE IF NOT EXISTS Usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario TEXT NOT NULL UNIQUE,
    clave TEXT NOT NULL,
    rol TEXT NOT NULL
);