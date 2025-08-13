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

def agregar_proveedor(datos):
    """Agrega un nuevo proveedor a la base de datos."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        columnas = ', '.join(datos.keys())
        placeholders = ', '.join(['?'] * len(datos))
        valores = tuple(datos.values())
        query = f"INSERT INTO Proveedores ({columnas}) VALUES ({placeholders})"
        cursor.execute(query, valores)
        conn.commit()
        return "Proveedor agregado correctamente."
    except sqlite3.IntegrityError:
        return "Error: El CUIT/DNI ingresado ya existe."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def obtener_proveedores():
    """Obtiene una lista de proveedores para el Treeview principal."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, razon_social, cuit_dni, telefono FROM Proveedores ORDER BY razon_social")
        proveedores = cursor.fetchall()
        return proveedores
    except sqlite3.Error as e:
        print(f"Error al obtener proveedores: {e}")
        return []
    finally:
        if conn:
            conn.close()
            
def obtener_todos_los_proveedores_para_reporte():
    """Obtiene id y razón social de todos los proveedores."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, razon_social FROM Proveedores ORDER BY razon_social")
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener todos los proveedores: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_cuenta_corriente_proveedor(proveedor_id, fecha_desde=None, fecha_hasta=None):
    """Obtiene todos los movimientos de la cuenta corriente de un proveedor, opcionalmente filtrado por fecha."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT fecha, tipo_movimiento, monto, saldo_resultante
            FROM CuentasCorrientesProveedores
            WHERE proveedor_id = ?
        """
        params = [proveedor_id]

        if fecha_desde and fecha_hasta:
            query += " AND DATE(fecha) BETWEEN ? AND ?"
            params.extend([fecha_desde, fecha_hasta])

        query += " ORDER BY fecha, id"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener cuenta corriente del proveedor: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_proveedor_column_names():
    """Devuelve los nombres de las columnas de la tabla Proveedores."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Proveedores)")
        return [info[1] for info in cursor.fetchall()]
    finally:
        if conn:
            conn.close()

def obtener_proveedor_por_id(id_proveedor):
    """Obtiene todos los datos de un proveedor específico por su ID."""
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM Proveedores WHERE id = ?"
        cursor.execute(query, (id_proveedor,))
        proveedor = cursor.fetchone()
        return proveedor
    except sqlite3.Error as e:
        print(f"Error al obtener proveedor por ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

def modificar_proveedor(datos):
    """Modifica los datos de un proveedor existente."""
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        id_proveedor = datos.pop('id')
        set_clause = ', '.join([f"{col} = ?" for col in datos.keys()])
        valores = tuple(datos.values()) + (id_proveedor,)
        query = f"UPDATE Proveedores SET {set_clause} WHERE id = ?"
        cursor.execute(query, valores)
        conn.commit()
        return "Proveedor modificado correctamente."
    except sqlite3.IntegrityError:
        return "Error: El CUIT/DNI ingresado ya pertenece a otro proveedor."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def eliminar_proveedor(id_proveedor):
    """Elimina un proveedor de la base de datos por su ID."""
    conn = _crear_conexion()
    if conn is None: return
    try:
        cursor = conn.cursor()
        query = "DELETE FROM Proveedores WHERE id = ?"
        cursor.execute(query, (id_proveedor,))
        conn.commit()
    finally:
        if conn:
            conn.close()

def obtener_compras_impagas(proveedor_id):
    """Obtiene todas las facturas de compra impagas de un proveedor."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT id, fecha_compra, numero_factura, monto_total
            FROM Compras
            WHERE proveedor_id = ? AND (estado IS NULL OR estado = 'IMPAGA')
            ORDER BY fecha_compra ASC
        """
        cursor.execute(query, (proveedor_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener compras impagas: {e}")
        return []
    finally:
        if conn:
            conn.close()

def registrar_pago_a_proveedor(caja_id, proveedor_id, compra_ids, pagos, nro_comprobante, detalle):
    """
    Registra un pago a un proveedor con múltiples medios de pago.
    """
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    
    monto_total_pagado = sum(p['monto'] for p in pagos)

    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        cursor.execute(
            "SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1",
            (proveedor_id,)
        )
        ultimo_saldo_res = cursor.fetchone()
        ultimo_saldo = ultimo_saldo_res[0] if ultimo_saldo_res else 0.0
        nuevo_saldo = ultimo_saldo - monto_total_pagado

        query_cc = """
            INSERT INTO CuentasCorrientesProveedores 
            (proveedor_id, fecha, tipo_movimiento, monto, saldo_resultante)
            VALUES (?, date('now'), 'PAGO', ?, ?)
        """
        cursor.execute(query_cc, (proveedor_id, -monto_total_pagado, nuevo_saldo))

        for compra_id in compra_ids:
            cursor.execute("UPDATE Compras SET estado = 'PAGADA' WHERE id = ?", (compra_id,))
        
        for pago in pagos:
            query_mov_caja = """
                INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id)
                VALUES (?, ?, 'EGRESO', ?, ?, ?)
            """
            concepto = f"Pago a Proveedor - Comp: {nro_comprobante} - Det: {detalle}"
            cursor.execute(query_mov_caja, (
                caja_id, datetime.now(), concepto, pago['monto'], pago['medio_pago_id']
            ))

        conn.commit()
        return "Pago a proveedor registrado exitosamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()