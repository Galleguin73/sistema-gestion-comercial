import sqlite3
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(PROJECT_ROOT, 'database')
MIGRATIONS_DIR = os.path.join(PROJECT_ROOT, 'migrations')
DB_PATH = os.path.join(DB_DIR, 'gestion.db')

def _crear_conexion():
    """Crea y devuelve una conexión a la base de datos."""
    try:
        return sqlite3.connect(DB_PATH, timeout=10)
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def ejecutar_migraciones():
    """
    Aplica todos los scripts de migración que no se hayan ejecutado previamente.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = _crear_conexion()
    if conn is None: return

    try:
        cursor = conn.cursor()
        
        # 1. Crear la tabla de control de migraciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                script_name TEXT PRIMARY KEY
            )
        """)
        
        # 2. Obtener las migraciones ya ejecutadas
        cursor.execute("SELECT script_name FROM _migrations")
        migraciones_ejecutadas = {row[0] for row in cursor.fetchall()}
        
        # 3. Obtener los scripts disponibles en la carpeta de migraciones
        scripts_disponibles = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])
        
        # 4. Ejecutar los scripts que no se hayan ejecutado
        for script in scripts_disponibles:
            if script not in migraciones_ejecutadas:
                print(f"Ejecutando migración: {script}...")
                with open(os.path.join(MIGRATIONS_DIR, script), 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                cursor.executescript(sql_script)
                
                # Registrar la migración como ejecutada
                cursor.execute("INSERT INTO _migrations (script_name) VALUES (?)", (script,))
                print(f"Migración {script} completada.")

        conn.commit()

        # Poblar datos iniciales si es la primera vez (opcional)
        cursor.execute("SELECT COUNT(*) FROM Provincias")
        if cursor.fetchone()[0] == 0:
            print("Poblando Provincias y Localidades...")
            poblar_provincias_localidades(conn, cursor)
            print("Datos geográficos poblados.")
        
        cursor.execute("SELECT COUNT(*) FROM Configuracion")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO Configuracion (id) VALUES (1)")
            conn.commit()

    except sqlite3.Error as e:
        print(f"Error durante las migraciones: {e}")
    finally:
        if conn:
            conn.close()

def poblar_provincias_localidades(conn, cursor):
    """Llena las tablas Provincias y Localidades con datos de Argentina."""
    provincias = [(1, 'Buenos Aires'), (2, 'Catamarca'), (3, 'Chaco'), (4, 'Chubut'),(5, 'Córdoba'), (6, 'Corrientes'), (7, 'Entre Ríos'), (8, 'Formosa'),(9, 'Jujuy'), (10, 'La Pampa'), (11, 'La Rioja'), (12, 'Mendoza'),(13, 'Misiones'), (14, 'Neuquén'), (15, 'Río Negro'), (16, 'Salta'),(17, 'San Juan'), (18, 'San Luis'), (19, 'Santa Cruz'), (20, 'Santa Fe'),(21, 'Santiago del Estero'), (22, 'Tierra del Fuego'), (23, 'Tucumán'),(24, 'CABA')]
    cursor.executemany("INSERT INTO Provincias (id, nombre) VALUES (?, ?)", provincias)
    localidades = [('La Plata', 1), ('Mar del Plata', 1), ('Quilmes', 1), ('Bahía Blanca', 1),('San Fernando del Valle de Catamarca', 2), ('Andalgalá', 2),('Resistencia', 3), ('Sáenz Peña', 3),('Rawson', 4), ('Comodoro Rivadavia', 4), ('Trelew', 4),('Córdoba', 5), ('Villa Carlos Paz', 5), ('Río Cuarto', 5),('Corrientes', 6), ('Goya', 6),('Paraná', 7), ('Concordia', 7),('Formosa', 8), ('Clorinda', 8),('San Salvador de Jujuy', 9), ('Libertador General San Martín', 9),('Santa Rosa', 10), ('General Pico', 10),('La Rioja', 11), ('Chilecito', 11),('Mendoza', 12), ('San Rafael', 12),('Posadas', 13), ('Oberá', 13),('Neuquén', 14), ('San Martín de los Andes', 14),('Viedma', 15), ('Bariloche', 15), ('General Roca', 15),('Salta', 16), ('San Ramón de la Nueva Orán', 16),('San Juan', 17), ('Rivadavia', 17),('San Luis', 18), ('Villa Mercedes', 18),('Río Gallegos', 19), ('Caleta Olivia', 19),('Rosario', 20), ('Santa Fe', 20),('Santiago del Estero', 21), ('La Banda', 21),('Ushuaia', 22), ('Río Grande', 22),('San Miguel de Tucumán', 23), ('Yerba Buena', 23),('Belgrano', 24), ('Palermo', 24), ('Flores', 24)]
    cursor.executemany("INSERT INTO Localidades (nombre, provincia_id) VALUES (?, ?)", localidades)
    conn.commit()

if __name__ == '__main__':
    ejecutar_migraciones()