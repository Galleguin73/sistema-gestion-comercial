import sqlite3
import os

# --- CONFIGURACIÓN ---
# Nombre del archivo de la base de datos
DB_FILENAME = 'gestion.db'
# Lista de tablas a vaciar (solo datos transaccionales)
TABLAS_A_LIMPIAR = [
    'Ventas',
    'VentasDetalle',
    'Compras',
    'ComprasDetalle',
    'Caja',
    'MovimientosCaja',
    'CuentasCorrientesClientes',
    'CuentasCorrientesProveedores',
    'AjustesStock'
]
# --- FIN DE LA CONFIGURACIÓN ---

# Construir la ruta a la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', DB_FILENAME)

def limpiar_base_de_datos():
    """
    Script para borrar todos los registros de las tablas transaccionales,
    manteniendo los datos maestros como artículos, clientes y proveedores.
    """
    print("--- SCRIPT DE LIMPIEZA DE BASE DE DATOS ---")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encontró el archivo de la base de datos en '{DB_PATH}'")
        return

    print(f"Base de datos a modificar: {DB_PATH}")
    print("\nEste script borrará TODOS los registros de las siguientes tablas:")
    for tabla in TABLAS_A_LIMPIAR:
        print(f"  - {tabla}")
    
    print("\nLas tablas de Articulos, Clientes, Proveedores, Usuarios, Marcas, Rubros y Configuración NO serán modificadas.")
    print("\n¡ESTA ACCIÓN ES IRREVERSIBLE! Se recomienda hacer una copia de seguridad.")
    
    # --- CONFIRMACIÓN DE SEGURIDAD ---
    confirmacion = input("Escriba 'SI' en mayúsculas para confirmar y proceder con la limpieza: ")
    
    if confirmacion != 'SI':
        print("\nLimpieza cancelada por el usuario.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("\nIniciando limpieza...")
        
        for tabla in TABLAS_A_LIMPIAR:
            print(f"Vaciando tabla: {tabla}...")
            # Borrar todos los registros de la tabla
            cursor.execute(f"DELETE FROM {tabla};")
            # Resetear el contador de autoincremento para que los IDs comiencen de nuevo
            try:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabla}';")
            except sqlite3.OperationalError:
                # Esta tabla podría no tener un contador de autoincremento, lo cual está bien.
                pass
        
        conn.commit()
        print("\n¡Limpieza completada exitosamente!")
        print("Las tablas transaccionales han sido vaciadas.")

    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        print(f"\nOcurrió un error durante la limpieza: {e}")
        print("Se revirtieron todos los cambios.")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    limpiar_base_de_datos()