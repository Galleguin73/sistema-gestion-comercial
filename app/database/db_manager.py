import sqlite3
import os

BASE_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
ROOT_DIR = os.path.dirname(BASE_APP_DIR) 
DB_PATH = os.path.join(ROOT_DIR, 'database', 'gestion.db')
MIGRATIONS_DIR = os.path.join(ROOT_DIR, 'migrations')

def _crear_conexion():
    """Crea y devuelve una conexión a la base de datos."""
    try:
        return sqlite3.connect(DB_PATH, timeout=10)
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def _crear_tabla_migraciones(cursor):
    """Asegura que la tabla para registrar las migraciones exista."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_archivo TEXT NOT NULL UNIQUE,
            fecha_ejecucion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

def _obtener_migraciones_ejecutadas(cursor):
    """Obtiene una lista de los nombres de archivos de migración ya ejecutados."""
    try:
        cursor.execute("SELECT nombre_archivo FROM _migrations")
        return {row[0] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        return set()

def aplicar_migraciones():
    """
    Busca archivos .sql en la carpeta de migraciones y ejecuta los que no se hayan ejecutado.
    """
    if not os.path.exists(MIGRATIONS_DIR):
        print("Carpeta de migraciones no encontrada. Saltando proceso.")
        return

    conn = _crear_conexion()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        _crear_tabla_migraciones(cursor)
        migraciones_ejecutadas = _obtener_migraciones_ejecutadas(cursor)

        archivos_sql = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])

        for archivo in archivos_sql:
            if archivo not in migraciones_ejecutadas:
                print(f"Ejecutando migración: {archivo}...")
                try:
                    with open(os.path.join(MIGRATIONS_DIR, archivo), 'r', encoding='utf-8') as f:
                        sql_script = f.read()
                        cursor.executescript(sql_script)
                    
                    cursor.execute("INSERT INTO _migrations (nombre_archivo) VALUES (?)", (archivo,))
                    conn.commit()
                    print(f"Migración {archivo} completada.")
                except sqlite3.Error as e:
                    print(f"Error durante la migración {archivo}: {e}")
                    conn.rollback()
                    break 
    except Exception as e:
        print(f"Ocurrió un error inesperado durante el proceso de migración: {e}")
    finally:
        if conn:
            conn.close()