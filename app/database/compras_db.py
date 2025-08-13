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

def registrar_compra(datos_factura, items_factura):
    """
    Registra una factura de compra completa, actualiza stock, precios
    y genera el movimiento en la cuenta corriente del proveedor.
    """
    conn = _crear_conexion()
    if conn is None: return "Error de conexión con la base de datos."

    try:
        cursor = conn.cursor()
        
        cursor.execute("BEGIN TRANSACTION")

        # 1. Insertar la cabecera de la compra
        query_compra = """
            INSERT INTO Compras (proveedor_id, numero_factura, fecha_compra, monto_total, tipo_compra)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query_compra, (
            datos_factura['proveedor_id'],
            datos_factura['numero_factura'],
            datos_factura['fecha_compra'],
            datos_factura['monto_total'],
            datos_factura['tipo_compra']
        ))
        compra_id = cursor.lastrowid

        # 2. Procesar cada artículo del detalle
        for item in items_factura:
            # 2a. Insertar en ComprasDetalle
            query_detalle = """
                INSERT INTO ComprasDetalle (compra_id, articulo_id, cantidad, precio_costo_unitario)
                VALUES (?, ?, ?, ?)
            """
            cursor.execute(query_detalle, (
                compra_id,
                item['articulo_id'],
                item['cantidad'],
                item['costo_unit']
            ))

            # 2b. Actualizar stock y precio de costo del artículo
            query_update_articulo = """
                UPDATE Articulos
                SET stock = stock + ?, 
                    precio_costo = ?
                WHERE id = ?
            """
            cursor.execute(query_update_articulo, (
                item['cantidad'],
                item['costo_unit'],
                item['articulo_id']
            ))

        # 3. Generar movimiento en la cuenta corriente del proveedor
        if datos_factura.get('condicion') == 'Cuenta Corriente':
            cursor.execute(
                "SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1",
                (datos_factura['proveedor_id'],)
            )
            ultimo_saldo_res = cursor.fetchone()
            ultimo_saldo = ultimo_saldo_res[0] if ultimo_saldo_res else 0.0
            nuevo_saldo = ultimo_saldo + datos_factura['monto_total']
            
            query_cc = """
                INSERT INTO CuentasCorrientesProveedores 
                (proveedor_id, compra_id, tipo_movimiento, monto, saldo_resultante)
                VALUES (?, ?, 'COMPRA', ?, ?)
            """
            cursor.execute(query_cc, (
                datos_factura['proveedor_id'],
                compra_id,
                datos_factura['monto_total'],
                nuevo_saldo
            ))

        conn.commit()
        return "Compra registrada exitosamente."

    except sqlite3.Error as e:
        conn.rollback()
        return f"Error al registrar la compra: {e}"
    finally:
        if conn:
            conn.close()