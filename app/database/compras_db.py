import sqlite3
from datetime import datetime
from app.utils.db_manager import crear_conexion

def _format_vencimiento_para_db(vencimiento):
    """Función auxiliar para manejar fechas de forma segura."""
    if hasattr(vencimiento, 'strftime'): # Si es un objeto de fecha/datetime
        return vencimiento.strftime('%Y-%m-%d')
    elif isinstance(vencimiento, str) and vencimiento: # Si ya es un string
        return vencimiento.split(' ')[0] # Nos aseguramos que no tenga hora
    return None

def guardar_borrador(datos_factura, items_compra, compra_id=None):
    """
    Guarda o actualiza una compra con estado 'BORRADOR'.
    NO afecta el stock.
    """
    conn = crear_conexion()
    if conn is None: return "Error de conexión.", None
    
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        datos_factura['estado'] = 'BORRADOR'
        datos_factura['saldo_pendiente'] = datos_factura['monto_total']

        if compra_id is None:
            columnas = ', '.join(datos_factura.keys())
            placeholders = ', '.join(['?'] * len(datos_factura))
            valores = tuple(datos_factura.values())
            query_compra = f"INSERT INTO Compras ({columnas}) VALUES ({placeholders})"
            cursor.execute(query_compra, valores)
            compra_id = cursor.lastrowid
        else:
            set_clause = ', '.join([f"{col} = ?" for col in datos_factura.keys()])
            valores = tuple(datos_factura.values()) + (compra_id,)
            query_update = f"UPDATE Compras SET {set_clause} WHERE id = ?"
            cursor.execute(query_update, valores)
            cursor.execute("DELETE FROM ComprasDetalle WHERE compra_id = ?", (compra_id,))

        detalle_query = """
            INSERT INTO ComprasDetalle (compra_id, articulo_id, cantidad, precio_costo_unitario, iva, lote, fecha_vencimiento, subtotal) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        for item in items_compra:
            subtotal = item['cantidad'] * item['costo_unitario']
            vencimiento_str = _format_vencimiento_para_db(item.get('vencimiento')) # CORRECCIÓN
            cursor.execute(detalle_query, (
                compra_id, item['articulo_id'], item['cantidad'], item['costo_unitario'], 
                item['iva'], item.get('lote'), vencimiento_str, subtotal
            ))
        
        conn.commit()
        return "Borrador guardado correctamente.", compra_id
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error al guardar el borrador: {e}", None
    finally:
        if conn: conn.close()


def finalizar_compra(datos_factura, items_compra, compra_id=None):
    """
    Crea o finaliza una compra. Si ya estaba finalizada, primero revierte
    el stock anterior y luego aplica el nuevo.
    """
    conn = crear_conexion()
    if conn is None: return "Error de conexión."

    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        if compra_id:
            cursor.execute("SELECT estado FROM Compras WHERE id = ?", (compra_id,))
            estado_anterior = cursor.fetchone()
            if estado_anterior and estado_anterior[0] not in ['BORRADOR', 'ANULADA']:
                print(f"Detectada edición de compra finalizada ID {compra_id}. Reviertiendo stock anterior.")
                cursor.execute("DELETE FROM StockLotes WHERE compra_id = ?", (compra_id,))

        estado_final = 'PAGADA' if datos_factura.get('condicion') == 'Contado' else 'IMPAGA'
        datos_factura['estado'] = estado_final
        datos_factura['saldo_pendiente'] = datos_factura['monto_total'] if estado_final == 'IMPAGA' else 0.0

        if compra_id:
            set_clause = ', '.join([f"{col} = ?" for col in datos_factura.keys()])
            valores = tuple(datos_factura.values()) + (compra_id,)
            query_update = f"UPDATE Compras SET {set_clause} WHERE id = ?"
            cursor.execute(query_update, valores)
            cursor.execute("DELETE FROM ComprasDetalle WHERE compra_id = ?", (compra_id,))
        else:
            columnas = ', '.join(datos_factura.keys())
            placeholders = ', '.join(['?'] * len(datos_factura))
            valores = tuple(datos_factura.values())
            query_compra = f"INSERT INTO Compras ({columnas}) VALUES ({placeholders})"
            cursor.execute(query_compra, valores)
            compra_id = cursor.lastrowid
        
        detalle_query = """
            INSERT INTO ComprasDetalle (compra_id, articulo_id, cantidad, precio_costo_unitario, iva, lote, fecha_vencimiento, subtotal) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        lote_query = """
            INSERT INTO StockLotes (articulo_id, cantidad, lote, fecha_vencimiento, activo, compra_id)
            VALUES (?, ?, ?, ?, 1, ?)
        """
        
        for item in items_compra:
            subtotal = item['cantidad'] * item['costo_unitario']
            vencimiento_str = _format_vencimiento_para_db(item.get('vencimiento')) # CORRECCIÓN
            
            cursor.execute(detalle_query, (
                compra_id, item['articulo_id'], item['cantidad'], item['costo_unitario'],
                item['iva'], item.get('lote'), vencimiento_str, subtotal
            ))
            cursor.execute(lote_query, (
                item['articulo_id'], item['cantidad'], item.get('lote'),
                vencimiento_str, compra_id
            ))
        
        if estado_final == 'IMPAGA':
            cursor.execute("DELETE FROM CuentasCorrientesProveedores WHERE compra_id = ?", (compra_id,))
            cursor.execute("SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1", (datos_factura['proveedor_id'],))
            ultimo_saldo = (cursor.fetchone() or [0.0])[0]
            nuevo_saldo = ultimo_saldo + datos_factura['monto_total']
            query_cc = "INSERT INTO CuentasCorrientesProveedores (proveedor_id, compra_id, fecha, tipo_movimiento, monto, saldo_resultante) VALUES (?, ?, ?, 'COMPRA', ?, ?)"
            cursor.execute(query_cc, (datos_factura['proveedor_id'], compra_id, datos_factura['fecha_compra'], datos_factura['monto_total'], nuevo_saldo))

        conn.commit()
        return "Compra finalizada y stock actualizado exitosamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error al finalizar la compra: {e}"
    finally:
        if conn: conn.close()

# El resto de las funciones no necesitan cambios
def anular_o_eliminar_compra(compra_id):
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("SELECT estado, proveedor_id, monto_total, condicion FROM Compras WHERE id = ?", (compra_id,))
        compra = cursor.fetchone()
        if not compra: raise Exception("La compra no existe.")
        estado, proveedor_id, monto_total, condicion = compra
        if estado == 'ANULADA': return "Error: Esta compra ya ha sido anulada."
        if estado == 'BORRADOR':
            cursor.execute("DELETE FROM ComprasDetalle WHERE compra_id = ?", (compra_id,))
            cursor.execute("DELETE FROM Compras WHERE id = ?", (compra_id,))
            mensaje = "Borrador de compra eliminado exitosamente."
        else:
            cursor.execute("UPDATE Compras SET estado = 'ANULADA' WHERE id = ?", (compra_id,))
            cursor.execute("DELETE FROM StockLotes WHERE compra_id = ?", (compra_id,))
            if condicion == 'Cuenta Corriente':
                cursor.execute("SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1", (proveedor_id,))
                ultimo_saldo = (cursor.fetchone() or [0.0])[0]
                nuevo_saldo = ultimo_saldo - monto_total
                query_cc = "INSERT INTO CuentasCorrientesProveedores (proveedor_id, fecha, tipo_movimiento, monto, saldo_resultante, compra_id) VALUES (?, date('now'), 'ANULACIÓN COMPRA', ?, ?, ?)"
                cursor.execute(query_cc, (proveedor_id, -monto_total, nuevo_saldo, compra_id))
            mensaje = "Compra anulada y stock revertido exitosamente."
        conn.commit()
        return mensaje
    except Exception as e:
        conn.rollback()
        return f"Error al anular/eliminar la compra: {e}"
    finally:
        if conn: conn.close()

def obtener_resumen_compras(criterio=None):
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT c.id, c.fecha_compra, p.razon_social, c.numero_factura, c.monto_total, c.estado
            FROM Compras c
            JOIN Proveedores p ON c.proveedor_id = p.id
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
    conn = crear_conexion()
    if conn is None: return None, []
    try:
        cursor = conn.cursor()
        q_enc = """SELECT c.fecha_compra, p.razon_social, c.numero_factura, c.monto_total, c.condicion, c.estado
                   FROM Compras c JOIN Proveedores p ON c.proveedor_id = p.id WHERE c.id = ?"""
        cursor.execute(q_enc, (compra_id,))
        encabezado = cursor.fetchone()
        
        q_det = """SELECT a.nombre, cd.cantidad, cd.precio_costo_unitario, cd.subtotal
                   FROM ComprasDetalle cd JOIN Articulos a ON cd.articulo_id = a.id WHERE cd.compra_id = ?"""
        cursor.execute(q_det, (compra_id,))
        detalles = cursor.fetchall()
        
        return encabezado, detalles
    finally:
        if conn: conn.close()

def obtener_compra_completa_por_id(compra_id):
    conn = crear_conexion()
    if conn is None: return None, []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Compras WHERE id = ?", (compra_id,))
        encabezado_data = cursor.fetchone()
        
        cursor.execute("""
            SELECT cd.articulo_id, a.codigo_barras, m.nombre, a.nombre, cd.cantidad, cd.precio_costo_unitario, cd.iva, cd.lote, cd.fecha_vencimiento
            FROM ComprasDetalle cd
            JOIN Articulos a ON cd.articulo_id = a.id
            LEFT JOIN Marcas m ON a.marca_id = m.id
            WHERE cd.compra_id = ?
        """, (compra_id,))
        detalles_data = cursor.fetchall()
        return encabezado_data, detalles_data
    finally:
        if conn: conn.close()

def get_compra_column_names():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Compras)")
        return [info[1] for info in cursor.fetchall()]
    finally:
        if conn: conn.close()

def obtener_compras_por_periodo(fecha_desde, fecha_hasta):
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT c.id, c.fecha_compra, p.razon_social, c.numero_factura, c.monto_total, c.estado
            FROM Compras c
            LEFT JOIN Proveedores p ON c.proveedor_id = p.id
            WHERE DATE(c.fecha_compra) BETWEEN ? AND ?
            ORDER BY c.fecha_compra ASC
        """
        cursor.execute(query, (fecha_desde, fecha_hasta))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener compras por período: {e}")
        return []
    finally:
        if conn: conn.close()