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

        estado = 'PAGADA' if datos_factura.get('condicion') == 'Contado' else 'IMPAGA'
        # --- CAMBIO: Añadimos saldo_pendiente a la inserción ---
        query_compra = """
            INSERT INTO Compras (proveedor_id, numero_factura, fecha_compra, monto_total, tipo_compra, estado, condicion, saldo_pendiente)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query_compra, (
            datos_factura['proveedor_id'],
            datos_factura['numero_factura'],
            datos_factura['fecha_compra'],
            datos_factura['monto_total'],
            datos_factura['tipo_compra'],
            estado,
            datos_factura.get('condicion'),
            datos_factura['monto_total'] # El saldo inicial es el total de la factura
        ))
        compra_id = cursor.lastrowid

        for item in items_factura:
            subtotal = item['cantidad'] * item['costo_unit']
            query_detalle = "INSERT INTO ComprasDetalle (compra_id, articulo_id, cantidad, precio_costo_unitario, subtotal) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(query_detalle, (compra_id, item['articulo_id'], item['cantidad'], item['costo_unit'], subtotal))
            
            query_update_articulo = "UPDATE Articulos SET stock = stock + ? WHERE id = ?"
            cursor.execute(query_update_articulo, (item['cantidad'], item['articulo_id']))

        if datos_factura.get('condicion') == 'Cuenta Corriente':
            cursor.execute("SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1", (datos_factura['proveedor_id'],))
            ultimo_saldo = (cursor.fetchone() or [0.0])[0]
            nuevo_saldo = ultimo_saldo + datos_factura['monto_total']
            query_cc = "INSERT INTO CuentasCorrientesProveedores (proveedor_id, compra_id, fecha, tipo_movimiento, monto, saldo_resultante) VALUES (?, ?, ?, 'COMPRA', ?, ?)"
            cursor.execute(query_cc, (datos_factura['proveedor_id'], compra_id, datos_factura['fecha_compra'], datos_factura['monto_total'], nuevo_saldo))

        conn.commit()
        return "Compra registrada exitosamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error al registrar la compra: {e}"
    finally:
        if conn: conn.close()

def obtener_resumen_compras(criterio=None):
    """Obtiene una lista resumida de todas las compras para la vista principal."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT c.id, c.fecha_compra, p.razon_social, c.numero_factura, c.monto_total, c.estado
            FROM Compras c
            LEFT JOIN Proveedores p ON c.proveedor_id = p.id
        """
        params = []
        if criterio:
            query += " WHERE p.razon_social LIKE ? OR c.numero_factura LIKE ?"
            params.extend([f'%{criterio}%', f'%{criterio}%'])
        query += " ORDER BY c.id DESC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def obtener_detalle_compra(compra_id):
    """Obtiene el encabezado y los items de una compra específica para visualización."""
    conn = _crear_conexion()
    if conn is None: return None, []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.fecha_compra, p.razon_social, c.numero_factura, c.monto_total, c.condicion, c.estado
            FROM Compras c
            LEFT JOIN Proveedores p ON c.proveedor_id = p.id
            WHERE c.id = ?
        """, (compra_id,))
        encabezado = cursor.fetchone()

        cursor.execute("""
            SELECT a.nombre, cd.cantidad, cd.precio_costo_unitario, cd.subtotal
            FROM ComprasDetalle cd
            JOIN Articulos a ON cd.articulo_id = a.id
            WHERE cd.compra_id = ?
        """, (compra_id,))
        detalles = cursor.fetchall()
        return encabezado, detalles
    finally:
        if conn: conn.close()

def obtener_compra_completa_por_id(compra_id):
    """Obtiene todos los datos de una compra para poder editarla."""
    conn = _crear_conexion()
    if conn is None: return None, []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Compras WHERE id = ?", (compra_id,))
        encabezado_data = cursor.fetchone()
        
        cursor.execute("""
            SELECT cd.articulo_id, a.codigo_barras, m.nombre, a.nombre, cd.cantidad, cd.precio_costo_unitario, a.iva
            FROM ComprasDetalle cd
            JOIN Articulos a ON cd.articulo_id = a.id
            LEFT JOIN Marcas m ON a.marca_id = m.id
            WHERE cd.compra_id = ?
        """, (compra_id,))
        detalles_data = cursor.fetchall()
        return encabezado_data, detalles_data
    finally:
        if conn: conn.close()

def anular_o_eliminar_compra(compra_id):
    """Anula una compra y revierte el stock y los movimientos de cta. cte."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("SELECT estado, proveedor_id, monto_total, condicion FROM Compras WHERE id = ?", (compra_id,))
        compra = cursor.fetchone()
        if not compra: raise Exception("La compra no existe.")
        if compra[0] == 'ANULADA': return "Error: Esta compra ya ha sido anulada."
        
        proveedor_id, monto_total_compra, condicion = compra[1], compra[2], compra[3]

        cursor.execute("SELECT articulo_id, cantidad FROM ComprasDetalle WHERE compra_id = ?", (compra_id,))
        detalles_compra = cursor.fetchall()
        for articulo_id, cantidad in detalles_compra:
            cursor.execute("UPDATE Articulos SET stock = stock - ? WHERE id = ?", (cantidad, articulo_id))

        if condicion == 'Cuenta Corriente':
            cursor.execute("SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1", (proveedor_id,))
            ultimo_saldo = (cursor.fetchone() or [0.0])[0]
            nuevo_saldo = ultimo_saldo - monto_total_compra
            query_cc = "INSERT INTO CuentasCorrientesProveedores (proveedor_id, fecha, tipo_movimiento, monto, saldo_resultante, compra_id) VALUES (?, date('now'), 'ANULACIÓN COMPRA', ?, ?, ?)"
            cursor.execute(query_cc, (proveedor_id, -monto_total_compra, nuevo_saldo, compra_id))

        cursor.execute("UPDATE Compras SET estado = 'ANULADA' WHERE id = ?", (compra_id,))
        conn.commit()
        return f"Compra ID {compra_id} anulada exitosamente."
    except Exception as e:
        conn.rollback()
        return f"Error al anular la compra: {e}"
    finally:
        if conn: conn.close()

def modificar_compra(compra_id, datos_factura_nuevos, items_factura_nuevos):
    """
    Modifica una compra IMPAGA sobreescribiendo los datos y recalculando
    los saldos posteriores en la cuenta corriente.
    """
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        # 1. Obtener datos originales para calcular diferencias
        cursor.execute("SELECT proveedor_id, fecha_compra FROM Compras WHERE id=?", (compra_id,))
        compra_original = cursor.fetchone()
        proveedor_id_original = compra_original[0]
        fecha_original = compra_original[1]

        cursor.execute("SELECT articulo_id, cantidad FROM ComprasDetalle WHERE compra_id=?", (compra_id,))
        items_originales = {art_id: cant for art_id, cant in cursor.fetchall()}

        # 2. Actualizar stock por diferencia
        items_nuevos = {item['articulo_id']: item for item in items_factura_nuevos}
        todos_los_ids = set(items_originales.keys()) | set(items_nuevos.keys())

        for art_id in todos_los_ids:
            cantidad_original = items_originales.get(art_id, 0)
            item_nuevo = items_nuevos.get(art_id)
            cantidad_nueva = item_nuevo['cantidad'] if item_nuevo else 0
            diferencia_stock = cantidad_nueva - cantidad_original
            if diferencia_stock != 0:
                cursor.execute("UPDATE Articulos SET stock = stock + ? WHERE id = ?", (diferencia_stock, art_id))

        # 3. Borrar detalles viejos y re-insertar los nuevos
        cursor.execute("DELETE FROM ComprasDetalle WHERE compra_id=?", (compra_id,))
        for item in items_factura_nuevos:
            subtotal = item['cantidad'] * item['costo_unit']
            query_detalle = "INSERT INTO ComprasDetalle (compra_id, articulo_id, cantidad, precio_costo_unitario, subtotal) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(query_detalle, (compra_id, item['articulo_id'], item['cantidad'], item['costo_unit'], subtotal))

        # 4. Actualizar el encabezado de la compra
        query_update = "UPDATE Compras SET proveedor_id=?, numero_factura=?, fecha_compra=?, monto_total=?, condicion=?, tipo_compra=? WHERE id=?"
        cursor.execute(query_update, (
            datos_factura_nuevos['proveedor_id'], datos_factura_nuevos['numero_factura'], 
            datos_factura_nuevos['fecha_compra'], datos_factura_nuevos['monto_total'], 
            datos_factura_nuevos['condicion'], datos_factura_nuevos['tipo_compra'], compra_id
        ))

        # 5. Recalcular la cuenta corriente del proveedor si aplica
        if datos_factura_nuevos.get('condicion') == 'Cuenta Corriente':
            # Sobreescribe el movimiento de la compra original
            query_update_cc = "UPDATE CuentasCorrientesProveedores SET monto = ?, fecha = ? WHERE compra_id = ? AND tipo_movimiento LIKE 'COMPRA%'"
            cursor.execute(query_update_cc, (datos_factura_nuevos['monto_total'], datos_factura_nuevos['fecha_compra'], compra_id))

            # Obtiene el saldo justo antes de nuestra transacción
            cursor.execute(
                "SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? AND id < (SELECT id FROM CuentasCorrientesProveedores WHERE compra_id = ?) ORDER BY id DESC LIMIT 1",
                (proveedor_id_original, compra_id)
            )
            saldo_anterior = (cursor.fetchone() or [0.0])[0]

            # Obtiene todos los movimientos desde la compra modificada en adelante para recalcular
            cursor.execute(
                "SELECT id, monto FROM CuentasCorrientesProveedores WHERE proveedor_id = ? AND id >= (SELECT id FROM CuentasCorrientesProveedores WHERE compra_id = ?) ORDER BY id ASC",
                (proveedor_id_original, compra_id)
            )
            movimientos_a_recalcular = cursor.fetchall()

            saldo_acumulado = saldo_anterior
            for mov_id, monto in movimientos_a_recalcular:
                saldo_acumulado += monto
                cursor.execute("UPDATE CuentasCorrientesProveedores SET saldo_resultante = ? WHERE id = ?", (saldo_acumulado, mov_id))

        conn.commit()
        return "Compra modificada exitosamente."
    except Exception as e:
        conn.rollback()
        return f"Error al modificar la compra: {e}"
    finally:
        if conn: conn.close()