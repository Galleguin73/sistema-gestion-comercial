import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'database')
DB_PATH = os.path.join(DB_DIR, 'gestion.db')

def _crear_conexion():
    try:
        return sqlite3.connect(DB_PATH, timeout=10)
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def agregar_proveedor(datos):
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
        if conn: conn.close()

def obtener_proveedores(criterio=None):
    """Obtiene una lista de proveedores para el Treeview principal, opcionalmente filtrada."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = "SELECT id, razon_social, cuit_dni, telefono FROM Proveedores"
        params = []
        if criterio:
            query += " WHERE razon_social LIKE ? OR cuit_dni LIKE ?"
            params.extend([f'%{criterio}%', f'%{criterio}%'])
        query += " ORDER BY razon_social"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener proveedores: {e}")
        return []
    finally:
        if conn: conn.close()

def obtener_todos_los_proveedores_para_reporte():
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
        if conn: conn.close()

def obtener_cuenta_corriente_proveedor(proveedor_id, fecha_desde=None, fecha_hasta=None):
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = "SELECT fecha, tipo_movimiento, monto, saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ?"
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
        if conn: conn.close()

def get_proveedor_column_names():
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Proveedores)")
        return [info[1] for info in cursor.fetchall()]
    finally:
        if conn: conn.close()

def obtener_proveedor_por_id(id_proveedor):
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM Proveedores WHERE id = ?"
        cursor.execute(query, (id_proveedor,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Error al obtener proveedor por ID: {e}")
        return None
    finally:
        if conn: conn.close()

def modificar_proveedor(datos):
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
        if conn: conn.close()

def eliminar_proveedor(id_proveedor):
    conn = _crear_conexion()
    if conn is None: return
    try:
        cursor = conn.cursor()
        query = "DELETE FROM Proveedores WHERE id = ?"
        cursor.execute(query, (id_proveedor,))
        conn.commit()
    finally:
        if conn: conn.close()

def obtener_compras_impagas(proveedor_id):
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = "SELECT id, fecha_compra, numero_factura, monto_total FROM Compras WHERE proveedor_id = ? AND (estado IS NULL OR estado = 'IMPAGA') ORDER BY fecha_compra ASC"
        cursor.execute(query, (proveedor_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener compras impagas: {e}")
        return []
    finally:
        if conn: conn.close()

def registrar_pago_a_proveedor(caja_id, proveedor_id, compra_ids, pagos, nro_comprobante, detalle):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    
    monto_total_pagado = sum(p['monto'] for p in pagos)
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1", (proveedor_id,))
        ultimo_saldo_res = cursor.fetchone()
        ultimo_saldo = ultimo_saldo_res[0] if ultimo_saldo_res else 0.0
        nuevo_saldo = ultimo_saldo - monto_total_pagado
        query_cc = "INSERT INTO CuentasCorrientesProveedores (proveedor_id, fecha, tipo_movimiento, monto, saldo_resultante, compra_id) VALUES (?, date('now'), 'PAGO', ?, ?, ?)"
        cursor.execute(query_cc, (proveedor_id, -monto_total_pagado, nuevo_saldo, compra_ids[0] if compra_ids else None))
        for compra_id in compra_ids:
            cursor.execute("UPDATE Compras SET estado = 'PAGADA' WHERE id = ?", (compra_id,))
        compra_id_referencia = compra_ids[0] if compra_ids else None
        for pago in pagos:
            query_mov_caja = "INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id, proveedor_id, compra_id) VALUES (?, ?, 'EGRESO', ?, ?, ?, ?, ?)"
            concepto = f"Pago a Proveedor - Comp: {nro_comprobante} - Det: {detalle}"
            cursor.execute(query_mov_caja, (caja_id, datetime.now(), concepto, pago['monto'], pago['medio_pago_id'], proveedor_id, compra_id_referencia))
        conn.commit()
        return "Pago a proveedor registrado exitosamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error de base de datos: {e}"
    finally:
        if conn: conn.close()

def registrar_pago_cuenta_corriente(caja_id, proveedor_id, pagos, concepto):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    monto_total_pagado = sum(p['monto'] for p in pagos)
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1", (proveedor_id,))
        ultimo_saldo_res = cursor.fetchone()
        ultimo_saldo = ultimo_saldo_res[0] if ultimo_saldo_res else 0.0
        nuevo_saldo = ultimo_saldo - monto_total_pagado
        query_cc = "INSERT INTO CuentasCorrientesProveedores (proveedor_id, fecha, tipo_movimiento, monto, saldo_resultante) VALUES (?, date('now'), 'PAGO', ?, ?)"
        cursor.execute(query_cc, (proveedor_id, -monto_total_pagado, nuevo_saldo))
        for pago in pagos:
            query_mov_caja = "INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id, proveedor_id) VALUES (?, ?, 'EGRESO', ?, ?, ?, ?)"
            cursor.execute(query_mov_caja, (caja_id, datetime.now(), concepto, pago['monto'], pago['medio_pago_id'], proveedor_id))
        conn.commit()
        return "Pago registrado exitosamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error de base de datos: {e}"
    finally:
        if conn: conn.close()

def obtener_proveedores_con_saldo():
    """
    Devuelve una lista de proveedores con saldo en su cuenta corriente.
    """
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # Consulta corregida para ser compatible con SQLite
        query = """
            SELECT p.id, p.razon_social, cta.saldo_resultante
            FROM (
                SELECT proveedor_id, saldo_resultante, MAX(fecha)
                FROM CuentasCorrientesProveedores
                GROUP BY proveedor_id
            ) AS cta
            JOIN Proveedores p ON p.id = cta.proveedor_id
            WHERE cta.saldo_resultante != 0
            ORDER BY p.razon_social
        """
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener proveedores con saldo: {e}")
        return []
    finally:
        if conn: conn.close()