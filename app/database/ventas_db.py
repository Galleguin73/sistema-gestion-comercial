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

def registrar_venta(datos_venta, items_carrito, pagos):
    """
    Registra una venta completa y genera los movimientos de caja correspondientes.
    """
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        # 1. Crear la Venta
        query_venta = "INSERT INTO Ventas (cliente_id, caja_id, fecha_venta, monto_total, tipo_comprobante) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(query_venta, (
            datos_venta['cliente_id'], datos_venta['caja_id'], datetime.now(), 
            datos_venta['total'], datos_venta['tipo_comprobante']
        ))
        venta_id = cursor.lastrowid

        # 2. Actualizar número de comprobante
        numero_comprobante = str(venta_id).zfill(8)
        cursor.execute("UPDATE Ventas SET numero_comprobante = ? WHERE id = ?", (numero_comprobante, venta_id))

        # 3. Registrar detalles y descontar stock
        for item_id, item_data in items_carrito.items():
            cantidad = item_data['cantidad']
            query_detalle = "INSERT INTO DetalleVenta (venta_id, articulo_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)"
            cursor.execute(query_detalle, (venta_id, item_id, cantidad, item_data['precio_unit']))
            
            query_stock = "UPDATE Articulos SET stock = stock - ? WHERE id = ?"
            cursor.execute(query_stock, (cantidad, item_id))

        # 4. Registrar los pagos Y los movimientos de caja
        for pago in pagos:
            # 4a. Registrar en VentasPagos
            query_pago = "INSERT INTO VentasPagos (venta_id, medio_pago_id, monto) VALUES (?, ?, ?)"
            cursor.execute(query_pago, (venta_id, pago['medio_pago_id'], pago['monto']))

            # 4b. Registrar en MovimientosCaja
            query_mov_caja = """
                INSERT INTO MovimientosCaja (caja_id, venta_id, fecha, tipo, concepto, monto, medio_pago_id)
                VALUES (?, ?, ?, 'INGRESO', ?, ?, ?)
            """
            concepto = f"Venta - Comprobante N°{numero_comprobante}"
            cursor.execute(query_mov_caja, (
                datos_venta['caja_id'], venta_id, datetime.now(), 
                concepto, pago['monto'], pago['medio_pago_id']
            ))

        conn.commit()
        return "Venta registrada exitosamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()
            
def obtener_ventas_por_periodo(fecha_desde, fecha_hasta):
    """Obtiene un listado de ventas realizadas en un período de fechas."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT v.id, v.fecha_venta, c.razon_social, v.tipo_comprobante, v.monto_total
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
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
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
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
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
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
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
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
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