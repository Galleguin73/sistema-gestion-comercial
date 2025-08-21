import sqlite3
import os

# --- Configuración de la Base de Datos ---
# Se asume que este script está en la carpeta raíz del proyecto
DB_PATH = os.path.join('database', 'gestion.db')

def _crear_conexion():
    """Crea y devuelve una conexión a la base de datos."""
    try:
        # Comprobamos que el archivo de la base de datos exista
        if not os.path.exists(DB_PATH):
            print(f"Error: No se encuentra el archivo de la base de datos en '{DB_PATH}'")
            return None
        return sqlite3.connect(DB_PATH, timeout=10)
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

# --- Función para Resetear el Stock ---
def reset_all_stock():
    """Establece el stock de TODOS los artículos en 0."""
    conn = _crear_conexion()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        # La consulta que pone a cero el stock de todos los artículos
        cursor.execute("UPDATE Articulos SET stock = 0")
        
        # Contamos cuántas filas fueron afectadas para confirmación
        row_count = cursor.rowcount
        
        conn.commit()
        print(f"\n¡Éxito! Se ha reseteado el stock de {row_count} artículos a 0.")
    except sqlite3.Error as e:
        print(f"Ocurrió un error al resetear el stock: {e}")
    finally:
        if conn:
            conn.close()

# --- Ejecución del Script ---
if __name__ == "__main__":
    print("======================================================")
    print("  ADVERTENCIA: Este script pondrá el stock de")
    print("               TODOS los artículos en 0.")
    print("======================================================")
    
    # Pedimos confirmación para mayor seguridad
    confirmacion = input("¿Estás seguro de que deseas continuar? (s/n): ")
    
    if confirmacion.lower() == 's':
        reset_all_stock()
    else:
        print("Operación cancelada por el usuario.")