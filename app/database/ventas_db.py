# Ubicación: app/database/ventas_db.py (MODIFICADO)
import sqlite3
from datetime import datetime
from app.utils.db_manager import crear_conexion


def registrar_venta(datos_venta, carrito_items, pagos):
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        query_venta = """
            INSERT INTO Ventas (fecha_venta, cliente_id, cliente_nombre, tipo_comprobante, monto_total, estado, caja_id, descuento_total, cae, cae_vencimiento, numero_comprobante)
            VALUES (?, ?, ?, ?, ?, 'FINALIZADA', ?, ?, ?, ?, ?)
        """
        cursor.execute(query_venta, (
            datetime.now(), 
            datos_venta.get('cliente_id'), 
            datos_venta.get('cliente_nombre'), 
            datos_venta.get('tipo_comprobante'), 
            datos_venta.get('total'),
            datos_venta.get('caja_id'), 
            datos_venta.get('descuento_total'),
            datos_venta.get('cae'),
            datos_venta.get('cae_vencimiento'),
            datos_venta.get('numero_factura')
        ))
        venta_id = cursor.lastrowid

        query_detalle = "INSERT INTO VentasDetalle (venta_id, articulo_id, descripcion, cantidad, precio_unitario, subtotal, descuento) VALUES (?, ?, ?, ?, ?, ?, ?)"
        for item_id, data in carrito_items.items():
            subtotal = (data['cantidad'] * data['precio_unit']) - data.get('descuento', 0.0)
            cursor.execute(query_detalle, (
                venta_id, item_id, data['descripcion'], data['cantidad'], 
                data['precio_unit'], subtotal, data.get('descuento', 0.0)
            ))
            cursor.execute("UPDATE Articulos SET stock = stock - ? WHERE id = ?", (data['cantidad'], item_id))
        
        for pago in pagos:
            concepto = f"Venta - Comprobante ID: {venta_id}"
            query_caja = "INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id, venta_id) VALUES (?, ?, 'INGRESO', ?, ?, ?, ?)"
            cursor.execute(query_caja, (datos_venta['caja_id'], datetime.now(), concepto, pago['monto'], pago['medio_pago_id'], venta_id))

        conn.commit()
        return venta_id
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error al registrar la venta: {e}"
    finally:
        if conn: conn.close()

def obtener_ventas_por_periodo(fecha_desde, fecha_hasta):
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT v.id, v.fecha_venta, c.razon_social, v.tipo_comprobante, v.monto_total, v.estado, v.cae
            FROM Ventas v
            LEFT JOIN Clientes c ON v.cliente_id = c.id
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
            ORDER BY v.fecha_venta DESC
        """
        cursor.execute(query, (fecha_desde, fecha_hasta))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener ventas por período: {e}")
        return []
    finally:
        if conn:
            conn.close()

def anular_venta(venta_id):
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("SELECT estado, cliente_id, caja_id FROM Ventas WHERE id = ?", (venta_id,))
        venta = cursor.fetchone()
        if not venta:
            raise Exception("La venta no existe.")
        if venta[0] == 'ANULADA':
            return "Error: Esta venta ya ha sido anulada."
        cliente_id, caja_id = venta[1], venta[2]
        cursor.execute("SELECT articulo_id, cantidad FROM VentasDetalle WHERE venta_id = ?", (venta_id,))
        detalles_venta = cursor.fetchall()
        for articulo_id, cantidad in detalles_venta:
            cursor.execute("UPDATE Articulos SET stock = stock + ? WHERE id = ?", (cantidad, articulo_id))
        
        cursor.execute("DELETE FROM MovimientosCaja WHERE venta_id = ? AND tipo = 'INGRESO'", (venta_id,))

        if cliente_id:
            cursor.execute("SELECT monto_total FROM Ventas WHERE id = ?", (venta_id,))
            monto_total_venta = cursor.fetchone()[0]
            cursor.execute("SELECT saldo_resultante FROM CuentasCorrientesClientes WHERE cliente_id = ? ORDER BY id DESC LIMIT 1", (cliente_id,))
            ultimo_saldo_res = cursor.fetchone()
            ultimo_saldo = ultimo_saldo_res[0] if ultimo_saldo_res else 0.0
            nuevo_saldo = ultimo_saldo - monto_total_venta
            query_cc = "INSERT INTO CuentasCorrientesClientes (cliente_id, fecha, tipo_movimiento, monto, saldo_resultante, venta_id) VALUES (?, date('now'), 'ANULACIÓN VENTA', ?, ?, ?)"
            cursor.execute(query_cc, (cliente_id, -monto_total_venta, nuevo_saldo, venta_id))

        cursor.execute("UPDATE Ventas SET estado = 'ANULADA' WHERE id = ?", (venta_id,))
        conn.commit()
        return f"Venta ID {venta_id} anulada exitosamente."
    except Exception as e:
        conn.rollback()
        return f"Error al anular la venta: {e}"
    finally:
        if conn:
            conn.close()

def obtener_ventas_mes_actual():
    conn = crear_conexion()
    if conn is None: return 0.0
    try:
        cursor = conn.cursor()
        query = "SELECT SUM(monto_total) FROM Ventas WHERE estado != 'ANULADA' AND STRFTIME('%Y-%m', fecha_venta) = STRFTIME('%Y-%m', 'now', 'localtime')"
        cursor.execute(query)
        resultado = cursor.fetchone()[0]
        return resultado if resultado is not None else 0.0
    except sqlite3.Error as e:
        print(f"Error al obtener ventas del mes: {e}")
        return 0.0
    finally:
        if conn:
            conn.close()

def obtener_top_10_productos_vendidos():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                a.nombre, 
                SUM(dv.cantidad) as total_vendido 
            FROM VentasDetalle dv 
            JOIN Articulos a ON dv.articulo_id = a.id 
            JOIN Ventas v ON dv.venta_id = v.id 
            WHERE v.estado != 'ANULADA' 
            GROUP BY a.id, a.nombre
            ORDER BY total_vendido DESC 
            LIMIT 10
        """
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener top 10 productos: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_top_10_productos_rentables():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT
                a.nombre,
                SUM(dv.cantidad * (dv.precio_unitario - a.precio_costo)) as ganancia_total
            FROM VentasDetalle dv
            JOIN Articulos a ON dv.articulo_id = a.id
            JOIN Ventas v ON dv.venta_id = v.id
            WHERE v.estado != 'ANULADA' AND a.precio_costo > 0
            GROUP BY a.id, a.nombre
            ORDER BY ganancia_total DESC
            LIMIT 10
        """
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener top 10 productos rentables: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_ventas_ultimo_mes_por_dia():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                STRFTIME('%Y-%m-%d', fecha_venta) as dia,
                SUM(monto_total) as total_diario
            FROM Ventas
            WHERE estado != 'ANULADA' AND fecha_venta >= DATE('now', '-1 month', 'localtime')
            GROUP BY dia
            ORDER BY dia ASC
        """
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener ventas del último mes por día: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_ventas_dia_actual():
    conn = crear_conexion()
    if conn is None: return 0.0
    try:
        cursor = conn.cursor()
        query = """
            SELECT SUM(monto_total) 
            FROM Ventas 
            WHERE estado != 'ANULADA' AND DATE(fecha_venta) = DATE('now', 'localtime')
        """
        cursor.execute(query)
        resultado = cursor.fetchone()[0]
        return resultado if resultado is not None else 0.0
    except sqlite3.Error as e:
        print(f"Error al obtener ventas del día: {e}")
        return 0.0
    finally:
        if conn:
            conn.close()

def obtener_venta_completa_por_id(venta_id):
    conn = crear_conexion()
    if not conn: return None
    try:
        conn.row_factory = sqlite3.Row; cursor = conn.cursor()
        query = """
            SELECT v.*, c.cuit_dni as cliente_cuit 
            FROM Ventas v 
            LEFT JOIN Clientes c ON v.cliente_id = c.id 
            WHERE v.id = ?
        """
        cursor.execute(query, (venta_id,))
        venta = cursor.fetchone()
        return dict(venta) if venta else None
    finally:
        if conn: conn.close()

def obtener_detalle_venta_completo(venta_id):
    conn = crear_conexion()
    if not conn: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT vd.descripcion, vd.cantidad, vd.precio_unitario, vd.subtotal, m.nombre as marca_nombre
            FROM VentasDetalle vd
            JOIN Articulos a ON vd.articulo_id = a.id
            LEFT JOIN Marcas m ON a.marca_id = m.id
            WHERE vd.venta_id = ?
        """
        cursor.execute(query, (venta_id,))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def actualizar_venta_con_cae(venta_id, datos_fiscales):
    """Actualiza una venta existente con su CAE, N° de Factura, y nuevo tipo de comprobante."""
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        query = """
            UPDATE Ventas 
            SET cae = ?, cae_vencimiento = ?, numero_comprobante = ?, tipo_comprobante = ?
            WHERE id = ?
        """
        cursor.execute(query, (
            datos_fiscales['cae'],
            datos_fiscales['vencimiento'],
            datos_fiscales['numero_factura'],
            datos_fiscales['tipo_comprobante'],
            venta_id
        ))
        conn.commit()
        return "Factura generada y venta actualizada correctamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error al actualizar la venta con datos fiscales: {e}"
    finally:
        if conn: conn.close()

def obtener_ventas_por_cliente(cliente_id, fecha_desde=None, fecha_hasta=None):
    """Obtiene el historial de ventas para un cliente específico, opcionalmente filtrado por fecha."""
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT id, fecha_venta, tipo_comprobante, monto_total, estado
            FROM Ventas 
            WHERE cliente_id = ? 
        """
        params = [cliente_id]

        if fecha_desde and fecha_hasta:
            query += " AND DATE(fecha_venta) BETWEEN ? AND ?"
            params.extend([fecha_desde, fecha_hasta])

        query += " ORDER BY fecha_venta DESC"
        
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener ventas del cliente: {e}")
        return []
    finally:
        if conn:
            conn.close()