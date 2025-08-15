-- migrations/0012_create_permisos_usuario_table.sql
CREATE TABLE PermisosUsuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    modulo_nombre TEXT NOT NULL,
    permitido INTEGER NOT NULL DEFAULT 0, -- 1 para sí, 0 para no
    FOREIGN KEY (usuario_id) REFERENCES Usuarios(id) ON DELETE CASCADE,
    UNIQUE(usuario_id, modulo_nombre)
);