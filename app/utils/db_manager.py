# Ubicación: app/utils/db_manager.py

import sqlite3
import os

# --- CÁLCULO DE LA RUTA A LA BASE DE DATOS ---
# Esto calcula la ruta al directorio raíz del proyecto de forma dinámica.
# No importa dónde ejecutes el script, siempre encontrará el archivo de la base de datos.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT_DIR, 'database', 'gestion.db')


def crear_conexion():
    """
    Crea y devuelve una conexión a la base de datos.
    Esta es la ÚNICA función que se usará en toda la aplicación para conectarse.
    """
    try:
        # Nos conectamos a la ruta de la base de datos definida arriba.
        # El timeout es una buena práctica para evitar que la aplicación se congele.
        conn = sqlite3.connect(DB_PATH, timeout=10)
        return conn
    except sqlite3.Error as e:
        # Si algo sale mal, imprimimos un error claro en la consola.
        print(f"Error al conectar con la base de datos en '{DB_PATH}': {e}")
        return None