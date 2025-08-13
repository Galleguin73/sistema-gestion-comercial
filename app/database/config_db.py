import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'database')
DB_PATH = os.path.join(DB_DIR, 'gestion.db')

def _crear_conexion():
    """Crea y devuelve una conexión a la base de datos."""
    try:
        return sqlite3.connect(DB_PATH, timeout=10)
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def guardar_configuracion(datos):
    """Guarda o actualiza los datos de configuración de la empresa."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        set_clause = ', '.join([f"{col} = ?" for col in datos.keys()])
        valores = tuple(datos.values())
        query = f"UPDATE Configuracion SET {set_clause} WHERE id = 1"
        cursor.execute(query, valores)
        conn.commit()
        return "Configuración guardada correctamente."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def obtener_configuracion():
    """Obtiene los datos de configuración de la empresa."""
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Configuracion WHERE id = 1")
        config = cursor.fetchone()
        
        cursor.execute("PRAGMA table_info(Configuracion)")
        columnas = [info[1] for info in cursor.fetchall()]
        
        return dict(zip(columnas, config)) if config else None
    except sqlite3.Error as e:
        print(f"Error al obtener configuración: {e}")
        return None
    finally:
        if conn:
            conn.close()
            
def obtener_provincias():
    """Obtiene una lista de todas las provincias."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM Provincias ORDER BY nombre")
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()

def obtener_localidades_por_provincia(provincia_id):
    """Obtiene una lista de localidades para una provincia dada."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM Localidades WHERE provincia_id = ? ORDER BY nombre", (provincia_id,))
        return [item[0] for item in cursor.fetchall()]
    finally:
        if conn:
            conn.close()

def obtener_medios_de_pago():
    """Obtiene una lista de todos los medios de pago."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM MediosDePago ORDER BY nombre")
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()

def agregar_medio_pago(nombre):
    """Agrega un nuevo medio de pago."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO MediosDePago (nombre) VALUES (?)", (nombre,))
        conn.commit()
        return "Medio de pago agregado correctamente."
    except sqlite3.IntegrityError:
        return "Error: Ese medio de pago ya existe."
    finally:
        if conn:
            conn.close()

def modificar_medio_pago(id_pago, nuevo_nombre):
    """Modifica el nombre de un medio de pago."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE MediosDePago SET nombre = ? WHERE id = ?", (nuevo_nombre, id_pago))
        conn.commit()
        return "Medio de pago modificado correctamente."
    except sqlite3.IntegrityError:
        return "Error: Ese nombre ya existe."
    finally:
        if conn:
            conn.close()

def eliminar_medio_pago(id_pago):
    """Elimina un medio de pago."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM MediosDePago WHERE id = ?", (id_pago,))
        conn.commit()
        return "Medio de pago eliminado correctamente."
    except sqlite3.Error as e:
        return f"Error: No se puede eliminar el medio de pago. {e}"
    finally:
        if conn:
            conn.close()