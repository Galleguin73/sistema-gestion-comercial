# Archivo: crear_admin.py
import sqlite3
import bcrypt
import os

# --- Configuración de la Base de Datos (ajusta si es necesario) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DB_DIR, 'gestion.db')

def crear_usuario_admin():
    """
    Script para crear el primer usuario administrador.
    """
    print("--- Creación de Usuario Administrador ---")
    
    # Pedir datos por consola
    nombre_usuario = input("Ingrese el nombre de usuario para el admin: ")
    clave = input("Ingrese la contraseña para el admin: ")
    
    if not nombre_usuario or not clave:
        print("Error: El nombre de usuario y la contraseña no pueden estar vacíos.")
        return

    # Encriptar (hashear) la contraseña
    clave_hasheada = bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt())

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Insertar el nuevo usuario con el rol 'admin'
        query = "INSERT INTO Usuarios (nombre_usuario, clave, rol) VALUES (?, ?, ?)"
        cursor.execute(query, (nombre_usuario, clave_hasheada, 'admin'))
        
        conn.commit()
        print(f"\n¡Éxito! Usuario administrador '{nombre_usuario}' creado correctamente.")
        print("Ya puedes ejecutar 'python main.py' e iniciar sesión.")

    except sqlite3.IntegrityError:
        print(f"\nError: El nombre de usuario '{nombre_usuario}' ya existe.")
    except sqlite3.Error as e:
        print(f"\nError de base de datos: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    crear_usuario_admin()