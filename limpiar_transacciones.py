import sqlite3
import os

# --- Configuración de la Base de Datos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DB_DIR, 'gestion.db')

# --- Lista de tablas que contienen datos transaccionales a eliminar ---
# Dejamos fuera las tablas de configuración como Articulos, Clientes, Proveedores, Usuarios, etc.
TABLAS_A_LIMPIAR = [
    'DetalleVenta',
    'VentasPagos',
    'Ventas',
    'ComprasDetalle',
    'Compras',
    'MovimientosCaja',
    'Caja',
    'CuentasCorrientesClientes',
    'CuentasCorrientesProveedores',
    'AjustesStock'
]

def limpiar_base_de_datos():
    """
    Elimina todos los registros de las tablas transaccionales para empezar de cero.
    """
    print("--- SCRIPT DE LIMPIEZA DE BASE DE DATOS ---")
    print("\n¡ADVERTENCIA! Esta acción eliminará permanentemente todos los datos de transacciones:")
    print("- Ventas y sus detalles")
    print("- Compras y sus detalles")
    print("- Movimientos de Caja y sesiones de Caja")
    print("- Cuentas Corrientes de Clientes y Proveedores")
    print("- Historial de Ajustes de Stock")
    print("\nSe conservarán los datos de Artículos, Clientes, Proveedores, Usuarios y Configuración.")
    print("ESTA ACCIÓN ES IRREVERSIBLE.")

    confirmacion = input("\n> Escriba 'CONFIRMAR' en mayúsculas para proceder: ")

    if confirmacion != "CONFIRMAR":
        print("\nLimpieza cancelada por el usuario.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("\nIniciando limpieza...")

        cursor.execute("BEGIN TRANSACTION")

        for tabla in TABLAS_A_LIMPIAR:
            print(f"Limpiando tabla: {tabla}...")
            cursor.execute(f"DELETE FROM {tabla};")
            # Opcional: Reiniciar los contadores de ID para estas tablas
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabla}';")
        
        conn.commit()
        print("\n¡Limpieza completada exitosamente!")
        print("La base de datos está lista para ser utilizada desde cero.")

    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        print(f"\nOcurrió un error durante la limpieza: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    limpiar_base_de_datos()