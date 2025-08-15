import sqlite3
import os
from datetime import datetime

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
            INSERT INTO Compras (proveedor_id, numero_factura, fecha_compra, monto_total, tipo_compra, estado)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        # Se establece el estado inicial basado en la condición de pago
        estado = 'PAGADA' if datos_factura.get('condicion') == 'Contado' else 'IMPAGA'
        cursor.execute(query_compra, (
            datos_factura['proveedor_id'],
            datos_factura['numero_factura'],
            datos_factura['fecha_compra'],
            datos_factura['monto_total'],
            datos_factura['tipo_compra'],
            estado
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
                (proveedor_id, compra_id, fecha, tipo_movimiento, monto, saldo_resultante)
                VALUES (?, ?, ?, 'COMPRA', ?, ?)
            """
            cursor.execute(query_cc, (
                datos_factura['proveedor_id'],
                compra_id,
                datos_factura['fecha_compra'],
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

# --- NUEVAS FUNCIONES AÑADIDAS ---

def obtener_compras_por_periodo(fecha_desde, fecha_hasta):
    """
    Obtiene un listado de compras realizadas en un período de fechas.
    """
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT c.id, c.fecha_compra, p.razon_social, c.numero_factura, c.monto_total, c.estado
            FROM Compras c
            JOIN Proveedores p ON c.proveedor_id = p.id
            WHERE DATE(c.fecha_compra) BETWEEN ? AND ?
            ORDER BY c.fecha_compra DESC
        """
        cursor.execute(query, (fecha_desde, fecha_hasta))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener compras por período: {e}")
        return []
    finally:
        if conn:
            conn.close()

def anular_compra(compra_id):
    """
    Anula una compra y realiza todas las operaciones asociadas:
    1. Ajusta (reduce) el stock de los artículos comprados.
    2. Crea contraasientos en la caja para los pagos realizados.
    3. Actualiza la cuenta corriente del proveedor.
    4. Cambia el estado de la compra a 'ANULADA'.
    """
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."

    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        # --- Paso 0: Verificar que la compra no esté ya anulada ---
        cursor.execute("SELECT estado, proveedor_id, monto_total FROM Compras WHERE id = ?", (compra_id,))
        compra = cursor.fetchone()
        if not compra:
            raise Exception("La compra no existe.")
        if compra[0] == 'ANULADA':
            return "Error: Esta compra ya ha sido anulada."
        
        proveedor_id = compra[1]
        monto_total_compra = compra[2]

        # --- Paso 1: Ajustar (Reducir) Stock ---
        cursor.execute("SELECT articulo_id, cantidad FROM ComprasDetalle WHERE compra_id = ?", (compra_id,))
        detalles_compra = cursor.fetchall()
        
        for articulo_id, cantidad in detalles_compra:
            cursor.execute("UPDATE Articulos SET stock = stock - ? WHERE id = ?", (cantidad, articulo_id))

        # --- Paso 2: Crear Contraasiento(s) en Caja (si la compra fue 'PAGADA') ---
        cursor.execute("SELECT id, caja_id, monto, medio_pago_id FROM MovimientosCaja WHERE compra_id = ?", (compra_id,))
        pagos_asociados = cursor.fetchall()

        for mov_id, caja_id, monto_pago, medio_pago_id in pagos_asociados:
            concepto = f"ANULACIÓN Pago Compra ID {compra_id}"
            query_contraasiento = """
                INSERT INTO MovimientosCaja 
                (caja_id, fecha, tipo, concepto, monto, medio_pago_id, compra_id)
                VALUES (?, ?, 'INGRESO', ?, ?, ?, ?)
            """
            cursor.execute(query_contraasiento, 
                           (caja_id, datetime.now(), concepto, monto_pago, medio_pago_id, compra_id))
        
        # --- Paso 3: Actualizar Cuenta Corriente del Proveedor ---
        cursor.execute(
            "SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1",
            (proveedor_id,)
        )
        ultimo_saldo_res = cursor.fetchone()
        ultimo_saldo = ultimo_saldo_res[0] if ultimo_saldo_res else 0.0
        nuevo_saldo = ultimo_saldo - monto_total_compra # Se resta (devuelve) el monto de la compra al saldo

        query_cc = """
            INSERT INTO CuentasCorrientesProveedores
            (proveedor_id, fecha, tipo_movimiento, monto, saldo_resultante, compra_id)
            VALUES (?, date('now'), 'ANULACIÓN COMPRA', ?, ?, ?)
        """
        cursor.execute(query_cc, (proveedor_id, -monto_total_compra, nuevo_saldo, compra_id))

        # --- Paso 4: Marcar la Compra como Anulada ---
        cursor.execute("UPDATE Compras SET estado = 'ANULADA' WHERE id = ?", (compra_id,))

        conn.commit()
        return f"Compra ID {compra_id} anulada exitosamente."

    except Exception as e:
        conn.rollback()
        return f"Error al anular la compra: {e}"
    finally:
        if conn:
            conn.close()