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

def abrir_caja(monto_inicial):
    """Abre una nueva sesión de caja."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Caja WHERE estado = 'ABIERTA'")
        if cursor.fetchone():
            return "Error: Ya hay una caja abierta."
        
        query = "INSERT INTO Caja (fecha_apertura, monto_inicial, estado) VALUES (?, ?, ?)"
        cursor.execute(query, (datetime.now(), monto_inicial, 'ABIERTA'))
        conn.commit()
        return "Caja abierta exitosamente."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def cerrar_caja(caja_id, monto_real_efectivo, monto_esperado_efectivo, diferencia_efectivo, detalle_cierre_json):
    """Cierra la sesión de caja actual, guardando el detalle completo del cierre."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        query = """
            UPDATE Caja 
            SET fecha_cierre = ?, 
                monto_final_real = ?, 
                monto_final_esperado = ?, 
                diferencia = ?, 
                estado = 'CERRADA',
                detalle_cierre = ?
            WHERE id = ?
        """
        cursor.execute(query, (
            datetime.now(), 
            monto_real_efectivo, 
            monto_esperado_efectivo, 
            diferencia_efectivo, 
            detalle_cierre_json,
            caja_id
        ))
        conn.commit()
        return "Caja cerrada exitosamente."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def obtener_estado_caja():
    """Devuelve la información de la caja abierta, si existe."""
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, fecha_apertura, monto_inicial FROM Caja WHERE estado = 'ABIERTA' ORDER BY id DESC LIMIT 1")
        return cursor.fetchone()
    finally:
        if conn:
            conn.close()

def obtener_movimientos_consolidados(caja_id):
    """
    Obtiene una lista unificada de todos los movimientos, incluyendo el ID del movimiento.
    """
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
        SELECT
            m.id AS movimiento_id,
            m.fecha,
            m.tipo,
            m.concepto,
            COALESCE(
                (SELECT c.razon_social FROM Clientes c JOIN Ventas v ON v.cliente_id = c.id WHERE v.id = m.venta_id),
                p.razon_social,
                ''
            ) AS entidad,
            m.monto,
            mp.nombre AS medio_pago
        FROM 
            MovimientosCaja m
        LEFT JOIN 
            MediosDePago mp ON m.medio_pago_id = mp.id
        LEFT JOIN
            Proveedores p ON m.proveedor_id = p.id
        WHERE 
            m.caja_id = ?
        ORDER BY 
            m.fecha ASC;
        """
        cursor.execute(query, (caja_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener movimientos consolidados: {e}")
        return []
    finally:
        if conn:
            conn.close()

def anular_movimiento_caja(movimiento_id, caja_id):
    """
    Crea un contraasiento para anular un movimiento de caja.
    Solo anula movimientos simples (no ligados a ventas o proveedores).
    """
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        
        # 1. Obtener el movimiento original
        cursor.execute("SELECT * FROM MovimientosCaja WHERE id = ?", (movimiento_id,))
        mov_original = cursor.fetchone()
        if not mov_original:
            return "Error: No se encontró el movimiento a anular."
            
        # Mapear columnas por nombre para mayor claridad
        columnas = [desc[0] for desc in cursor.description]
        mov_dict = dict(zip(columnas, mov_original))

        # 2. Verificar que es un movimiento simple (no tiene venta_id ni proveedor_id)
        if mov_dict.get('venta_id') or mov_dict.get('proveedor_id'):
            return "Error: Un pago de venta o a proveedor debe anularse desde su respectivo módulo."

        # 3. Crear el contraasiento
        cursor.execute("BEGIN TRANSACTION")

        nuevo_tipo = 'INGRESO' if mov_dict['tipo'] == 'EGRESO' else 'EGRESO'
        nuevo_concepto = f"ANULACIÓN Mov. ID {movimiento_id} - {mov_dict['concepto']}"
        
        query_contraasiento = """
            INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query_contraasiento, (
            caja_id, datetime.now(), nuevo_tipo, nuevo_concepto,
            mov_dict['monto'], mov_dict['medio_pago_id']
        ))

        # 4. Marcar el movimiento original como anulado (opcional pero recomendado)
        query_marcar_anulado = "UPDATE MovimientosCaja SET concepto = ? WHERE id = ?"
        concepto_anulado = f"{mov_dict['concepto']} (ANULADO)"
        cursor.execute(query_marcar_anulado, (concepto_anulado, movimiento_id))

        conn.commit()
        return "Movimiento anulado correctamente con un contraasiento."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error de base de datos al anular: {e}"
    finally:
        if conn:
            conn.close()