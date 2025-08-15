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

# --- FUNCIÓN MODIFICADA PARA ACEPTAR DESCUENTOS ---
def registrar_venta(datos_venta, items_carrito, pagos):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        query_venta = "INSERT INTO Ventas (cliente_id, caja_id, fecha_venta, monto_total, tipo_comprobante, descuento_total) VALUES (?, ?, ?, ?, ?, ?)"
        cursor.execute(query_venta, (
            datos_venta['cliente_id'], datos_venta['caja_id'], datetime.now(), 
            datos_venta['total'], datos_venta['tipo_comprobante'], datos_venta.get('descuento_total', 0.0)
        ))
        venta_id = cursor.lastrowid

        numero_comprobante = str(venta_id).zfill(8)
        cursor.execute("UPDATE Ventas SET numero_comprobante = ? WHERE id = ?", (numero_comprobante, venta_id))

        for item_id, item_data in items_carrito.items():
            cantidad = item_data['cantidad']
            descuento_item = item_data.get('descuento', 0.0)
            query_detalle = "INSERT INTO DetalleVenta (venta_id, articulo_id, cantidad, precio_unitario, descuento_monto) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(query_detalle, (venta_id, item_id, cantidad, item_data['precio_unit'], descuento_item))
            query_stock = "UPDATE Articulos SET stock = stock - ? WHERE id = ?"
            cursor.execute(query_stock, (cantidad, item_id))

        for pago in pagos:
            query_pago = "INSERT INTO VentasPagos (venta_id, medio_pago_id, monto) VALUES (?, ?, ?)"
            cursor.execute(query_pago, (venta_id, pago['medio_pago_id'], pago['monto']))
            query_mov_caja = "INSERT INTO MovimientosCaja (caja_id, venta_id, fecha, tipo, concepto, monto, medio_pago_id) VALUES (?, ?, ?, 'INGRESO', ?, ?, ?)"
            concepto = f"Venta - Comprobante N°{numero_comprobante}"
            cursor.execute(query_mov_caja, (datos_venta['caja_id'], venta_id, datetime.now(), concepto, pago['monto'], pago['medio_pago_id']))

        conn.commit()
        return venta_id # <--- CAMBIO IMPORTANTE: Devolvemos el ID
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

# --- FUNCIONES ORIGINALES (SIN CAMBIOS) ---
def obtener_ventas_por_periodo(fecha_desde, fecha_hasta):
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT v.id, v.fecha_venta, c.razon_social, v.tipo_comprobante, v.monto_total, v.estado
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
    conn = _crear_conexion()
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
        cursor.execute("SELECT articulo_id, cantidad FROM DetalleVenta WHERE venta_id = ?", (venta_id,))
        detalles_venta = cursor.fetchall()
        for articulo_id, cantidad in detalles_venta:
            cursor.execute("UPDATE Articulos SET stock = stock + ? WHERE id = ?", (cantidad, articulo_id))
        cursor.execute("SELECT monto, medio_pago_id FROM VentasPagos WHERE venta_id = ?", (venta_id,))
        pagos_venta = cursor.fetchall()
        for monto_pago, medio_pago_id in pagos_venta:
            concepto = f"ANULACIÓN Venta ID {venta_id}"
            query_contraasiento = "INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id, venta_id) VALUES (?, ?, 'EGRESO', ?, ?, ?, ?)"
            cursor.execute(query_contraasiento, (caja_id, datetime.now(), concepto, monto_pago, medio_pago_id, venta_id))
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
    conn = _crear_conexion()
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
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = "SELECT a.nombre, SUM(dv.cantidad) as total_vendido FROM DetalleVenta dv JOIN Articulos a ON dv.articulo_id = a.id JOIN Ventas v ON dv.venta_id = v.id WHERE v.estado != 'ANULADA' GROUP BY a.nombre ORDER BY total_vendido DESC LIMIT 10"
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener top 10 productos: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_producto_mayor_utilidad():
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT a.nombre, a.utilidad FROM Articulos a WHERE a.utilidad = (SELECT MAX(utilidad) FROM Articulos WHERE id IN (SELECT DISTINCT articulo_id FROM DetalleVenta)) LIMIT 1"
        cursor.execute(query)
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Error al obtener producto con mayor utilidad: {e}")
        return None
    finally:
        if conn:
            conn.close()

def obtener_ventas_ultimo_trimestre():
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = "SELECT STRFTIME('%Y-%m', fecha_venta) as mes, SUM(monto_total) FROM Ventas WHERE estado != 'ANULADA' AND fecha_venta >= DATE('now', '-3 months', 'localtime') GROUP BY mes ORDER BY mes ASC"
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener ventas del trimestre: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_ventas_del_dia():
    """Obtiene un listado de las ventas realizadas en la fecha actual."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        query = """
            SELECT v.id, v.fecha_venta, v.numero_comprobante, c.razon_social, v.monto_total
            FROM Ventas v
            LEFT JOIN Clientes c ON v.cliente_id = c.id
            WHERE DATE(v.fecha_venta) = ?
            ORDER BY v.fecha_venta DESC
        """
        cursor.execute(query, (fecha_hoy,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener ventas del día: {e}")
        return []
    finally:
        if conn:
            conn.close()

def reporte_ventas_por_articulo(fecha_desde, fecha_hasta):
    """Genera un reporte de ventas agrupado por artículo."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                a.codigo_barras, a.nombre, m.nombre,
                SUM(dv.cantidad) as cantidad_total,
                SUM(dv.cantidad * dv.precio_unitario) as monto_total
            FROM DetalleVenta dv
            JOIN Articulos a ON dv.articulo_id = a.id
            JOIN Ventas v ON dv.venta_id = v.id
            LEFT JOIN Marcas m ON a.marca_id = m.id
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ? AND v.estado != 'ANULADA'
            GROUP BY a.id
            ORDER BY monto_total DESC
        """
        cursor.execute(query, (fecha_desde, fecha_hasta))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error en reporte de ventas por artículo: {e}")
        return []
    finally:
        if conn:
            conn.close()

def reporte_ventas_por_marca(fecha_desde, fecha_hasta):
    """Genera un reporte de ventas agrupado por marca."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                m.nombre,
                SUM(dv.cantidad) as cantidad_total,
                SUM(dv.cantidad * dv.precio_unitario) as monto_total
            FROM DetalleVenta dv
            JOIN Articulos a ON dv.articulo_id = a.id
            JOIN Ventas v ON dv.venta_id = v.id
            JOIN Marcas m ON a.marca_id = m.id
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ? AND v.estado != 'ANULADA'
            GROUP BY m.id
            ORDER BY monto_total DESC
        """
        cursor.execute(query, (fecha_desde, fecha_hasta))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error en reporte de ventas por marca: {e}")
        return []
    finally:
        if conn:
            conn.close()

def reporte_ventas_por_rubro(fecha_desde, fecha_hasta):
    """Genera un reporte de ventas agrupado por rubro."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                r.nombre,
                SUM(dv.cantidad) as cantidad_total,
                SUM(dv.cantidad * dv.precio_unitario) as monto_total
            FROM DetalleVenta dv
            JOIN Articulos a ON dv.articulo_id = a.id
            JOIN Ventas v ON dv.venta_id = v.id
            JOIN Subrubros s ON a.subrubro_id = s.id
            JOIN Rubros r ON s.rubro_id = r.id
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ? AND v.estado != 'ANULADA'
            GROUP BY r.id
            ORDER BY monto_total DESC
        """
        cursor.execute(query, (fecha_desde, fecha_hasta))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error en reporte de ventas por rubro: {e}")
        return []
    finally:
        if conn:
            conn.close()

def reporte_ventas_por_subrubro(fecha_desde, fecha_hasta):
    """Genera un reporte de ventas agrupado por subrubro."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                s.nombre,
                r.nombre as rubro_nombre,
                SUM(dv.cantidad) as cantidad_total,
                SUM(dv.cantidad * dv.precio_unitario) as monto_total
            FROM DetalleVenta dv
            JOIN Articulos a ON dv.articulo_id = a.id
            JOIN Ventas v ON dv.venta_id = v.id
            JOIN Subrubros s ON a.subrubro_id = s.id
            JOIN Rubros r ON s.rubro_id = r.id
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ? AND v.estado != 'ANULADA'
            GROUP BY s.id
            ORDER BY monto_total DESC
        """
        cursor.execute(query, (fecha_desde, fecha_hasta))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error en reporte de ventas por subrubro: {e}")
        return []
    finally:
        if conn:
            conn.close()

def reporte_ventas_por_rubro_y_subrubro(fecha_desde, fecha_hasta):
    """
    Genera un reporte de ventas agrupado por rubro y subrubro para un período.
    """
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                r.nombre as rubro_nombre,
                s.nombre as subrubro_nombre,
                SUM(dv.cantidad) as cantidad_total,
                SUM(dv.cantidad * dv.precio_unitario - dv.descuento_monto) as monto_total_neto
            FROM DetalleVenta dv
            JOIN Articulos a ON dv.articulo_id = a.id
            JOIN Ventas v ON dv.venta_id = v.id
            JOIN Subrubros s ON a.subrubro_id = s.id
            JOIN Rubros r ON s.rubro_id = r.id
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ? AND v.estado != 'ANULADA'
            GROUP BY r.nombre, s.nombre
            ORDER BY r.nombre, monto_total_neto DESC
        """
        cursor.execute(query, (fecha_desde, fecha_hasta))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error en reporte de ventas por rubro y subrubro: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_ventas_dia_actual():
    """Calcula la suma total de ventas del día en curso."""
    conn = _crear_conexion()
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

def obtener_top_10_productos_rentables():
    """
    Devuelve un ranking de los 10 productos que más ganancia generaron.
    La ganancia se calcula como (precio_venta - precio_costo) * cantidad.
    """
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT
                a.nombre,
                SUM(dv.cantidad * (dv.precio_unitario - a.precio_costo)) as ganancia_total
            FROM DetalleVenta dv
            JOIN Articulos a ON dv.articulo_id = a.id
            JOIN Ventas v ON dv.venta_id = v.id
            WHERE v.estado != 'ANULADA' AND a.precio_costo > 0
            GROUP BY a.id
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

def obtener_ventas_ultimos_6_meses():
    """Devuelve las ventas totales agrupadas por mes para los últimos 6 meses."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT STRFTIME('%Y-%m', fecha_venta) as mes, SUM(monto_total)
            FROM Ventas
            WHERE estado != 'ANULADA' AND fecha_venta >= DATE('now', '-6 months', 'localtime')
            GROUP BY mes
            ORDER BY mes ASC
        """
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener ventas de los últimos 6 meses: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_ventas_ultimo_mes_por_dia():
    """Devuelve las ventas totales agrupadas por día para el último mes."""
    conn = _crear_conexion()
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
