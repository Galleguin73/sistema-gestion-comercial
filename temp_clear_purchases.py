import sqlite3
import os

# --- Configuración de la Base de Datos ---
# Asegúrate de que esta ruta sea correcta desde la raíz de tu proyecto
DB_PATH = os.path.join('database', 'gestion.db')

def _crear_conexion():
    """Crea y devuelve una conexión a la base de datos."""
    try:
        return sqlite3.connect(DB_PATH, timeout=10)
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

# --- Función para Limpiar las Tablas ---
def clear_purchase_data():
    """
    Elimina todos los registros de las tablas relacionadas con compras y 
    cuentas corrientes de proveedores.
    """
    conn = _crear_conexion()
    if conn is None:
        print("No se pudo conectar a la base de datos.")
        return

    tables_to_clear = [
        "ComprasDetalle",
        "Compras",
        "CuentasCorrientesProveedores"
    ]

    try:
        cursor = conn.cursor()
        print("Iniciando limpieza de datos de compras...")

        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
            # Opcional: Resetea el contador de autoincremento para que los IDs empiecen de 1
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name = '{table}'")
            print(f" - Tabla '{table}' limpiada.")

        conn.commit()
        print("\n¡Éxito! Se ha limpiado todo el historial de compras y cuentas corrientes de proveedores.")

    except sqlite3.Error as e:
        print(f"Ocurrió un error al limpiar las tablas: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

# --- Ejecución del Script ---
if __name__ == "__main__":
    print("="*60)
    print("  ADVERTENCIA: Este script borrará permanentemente TODOS los")
    print("  datos de las siguientes tablas:")
    print("    - Compras")
    print("    - ComprasDetalle")
    print("    - CuentasCorrientesProveedores")
    print("="*60)

    confirmacion = input("¿Estás absolutamente seguro de que deseas continuar? (escribe 'si' para confirmar): ")

    if confirmacion.lower() == 'si':
        clear_purchase_data()
    else:
        print("Operación cancelada por el usuario.")