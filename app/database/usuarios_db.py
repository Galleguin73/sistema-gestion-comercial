# Archivo: app/database/usuarios_db.py
import sqlite3
import os
import bcrypt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'database')
DB_PATH = os.path.join(DB_DIR, 'gestion.db')

def _crear_conexion():
    try:
        return sqlite3.connect(DB_PATH, timeout=10)
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def validar_usuario(nombre_usuario, clave):
    """
    Valida las credenciales del usuario.
    Devuelve los datos del usuario si son correctos, de lo contrario None.
    """
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_usuario, clave, rol FROM Usuarios WHERE nombre_usuario = ?", (nombre_usuario,))
        usuario = cursor.fetchone()
        if usuario:
            clave_guardada = usuario[2]
            # Verificar la contraseña hasheada
            if bcrypt.checkpw(clave.encode('utf-8'), clave_guardada):
                return {'id': usuario[0], 'nombre': usuario[1], 'rol': usuario[3]}
        return None
    finally:
        if conn:
            conn.close()

def obtener_permisos_usuario(usuario_id):
    """
    Obtiene un diccionario con los módulos permitidos para un usuario.
    """
    conn = _crear_conexion()
    if conn is None: return {}
    try:
        cursor = conn.cursor()
        query = "SELECT modulo_nombre, permitido FROM PermisosUsuario WHERE usuario_id = ?"
        cursor.execute(query, (usuario_id,))
        permisos = {row[0]: bool(row[1]) for row in cursor.fetchall()}
        return permisos
    except sqlite3.Error as e:
        print(f"Error al obtener permisos: {e}")
        return {}
    finally:
        if conn:
            conn.close()

# Nota: Más adelante añadiremos aquí funciones para que el admin pueda
# crear usuarios y modificar permisos.