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

def cerrar_caja(caja_id, monto_real, monto_esperado, diferencia):
    """Cierra la sesión de caja actual."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        query = """
            UPDATE Caja 
            SET fecha_cierre = ?, monto_final_real = ?, monto_final_esperado = ?, diferencia = ?, estado = 'CERRADA'
            WHERE id = ?
        """
        cursor.execute(query, (datetime.now(), monto_real, monto_esperado, diferencia, caja_id))
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

def obtener_movimientos(caja_id):
    """Obtiene todos los movimientos para una sesión de caja dada."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT m.id, m.fecha, m.tipo, m.concepto, m.monto, mp.nombre
            FROM MovimientosCaja m
            LEFT JOIN MediosDePago mp ON m.medio_pago_id = mp.id
            WHERE m.caja_id = ?
            ORDER BY m.fecha
        """
        cursor.execute(query, (caja_id,))
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()

def registrar_movimiento_caja(datos_movimiento):
    """Registra un nuevo movimiento (ingreso o egreso) en la caja actual."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (
            datos_movimiento['caja_id'],
            datetime.now(),
            datos_movimiento['tipo'],
            datos_movimiento['concepto'],
            datos_movimiento['monto'],
            datos_movimiento['medio_pago_id']
        ))
        conn.commit()
        return "Movimiento registrado correctamente."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def eliminar_movimiento_caja(movimiento_id):
    """Elimina un movimiento de caja específico por su ID."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM MovimientosCaja WHERE id = ?", (movimiento_id,))
        conn.commit()
        return "Movimiento eliminado correctamente."
    except sqlite3.Error as e:
        return f"Error al eliminar el movimiento: {e}"
    finally:
        if conn:
            conn.close()