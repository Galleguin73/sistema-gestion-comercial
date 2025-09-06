# Ubicación: app/database/usuarios_db.py (MODIFICADO)
import sqlite3
import bcrypt
from app.utils.db_manager import crear_conexion


def validar_usuario(nombre_usuario, clave):
    """Valida las credenciales del usuario."""
    conn = crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_usuario, clave, rol FROM Usuarios WHERE nombre_usuario = ?", (nombre_usuario,))
        usuario = cursor.fetchone()
        if usuario:
            clave_guardada = usuario[2]
            if bcrypt.checkpw(clave.encode('utf-8'), clave_guardada):
                return {'id': usuario[0], 'nombre': usuario[1], 'rol': usuario[3]}
        return None
    finally:
        if conn:
            conn.close()

def obtener_permisos_usuario(usuario_id):
    """Obtiene un diccionario con los módulos permitidos para un usuario."""
    conn = crear_conexion()
    if conn is None: return {}
    try:
        cursor = conn.cursor()
        query = "SELECT modulo_nombre FROM PermisosUsuario WHERE usuario_id = ? AND permitido = 1"
        cursor.execute(query, (usuario_id,))
        # Usamos un set para una búsqueda más eficiente
        permisos = {row[0] for row in cursor.fetchall()}
        return permisos
    except sqlite3.Error as e:
        print(f"Error al obtener permisos: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def obtener_todos_los_usuarios():
    """Obtiene una lista de todos los usuarios (sin la clave)."""
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_usuario, rol FROM Usuarios ORDER BY nombre_usuario")
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()

def crear_usuario(nombre_usuario, clave, rol):
    """Crea un nuevo usuario con la contraseña hasheada."""
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        clave_hasheada = bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt())
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Usuarios (nombre_usuario, clave, rol) VALUES (?, ?, ?)",
                       (nombre_usuario, clave_hasheada, rol))
        conn.commit()
        return "Usuario creado exitosamente."
    except sqlite3.IntegrityError:
        return "Error: El nombre de usuario ya existe."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def eliminar_usuario(usuario_id):
    """Elimina un usuario de la base de datos."""
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Usuarios WHERE id = ?", (usuario_id,))
        conn.commit()
        return "Usuario eliminado exitosamente."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def guardar_permisos_usuario(usuario_id, permisos):
    """
    Guarda la configuración de permisos para un usuario.
    permisos es un diccionario ej: {'Caja': True, 'Artículos': False}
    """
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        # Primero, borramos los permisos antiguos para este usuario
        cursor.execute("DELETE FROM PermisosUsuario WHERE usuario_id = ?", (usuario_id,))
        
        # Luego, insertamos los nuevos permisos
        for modulo, permitido in permisos.items():
            cursor.execute("INSERT INTO PermisosUsuario (usuario_id, modulo_nombre, permitido) VALUES (?, ?, ?)",
                           (usuario_id, modulo, int(permitido)))
        
        conn.commit()
        return "Permisos guardados exitosamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error al guardar permisos: {e}"
    finally:
        if conn:
            conn.close()

def modificar_clave_usuario(usuario_id, nueva_clave):
    """Modifica la contraseña de un usuario existente."""
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        clave_hasheada = bcrypt.hashpw(nueva_clave.encode('utf-8'), bcrypt.gensalt())
        cursor = conn.cursor()
        cursor.execute("UPDATE Usuarios SET clave = ? WHERE id = ?", (clave_hasheada, usuario_id))
        conn.commit()
        return "Contraseña modificada exitosamente."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()