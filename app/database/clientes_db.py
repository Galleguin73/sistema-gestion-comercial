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

def agregar_cliente(datos):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        columnas = ', '.join(datos.keys())
        placeholders = ', '.join(['?'] * len(datos))
        valores = tuple(datos.values())
        query = f"INSERT INTO Clientes ({columnas}) VALUES ({placeholders})"
        cursor.execute(query, valores)
        conn.commit()
        return "Cliente agregado correctamente."
    except sqlite3.IntegrityError:
        return "Error: El CUIT/DNI ingresado ya existe."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn: conn.close()

def obtener_clientes(criterio=None):
    """Obtiene una lista de clientes para el Treeview, opcionalmente filtrada."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = "SELECT id, razon_social, nombre_fantasia, tipo_cuenta, fecha_alta, estado FROM Clientes"
        params = []
        if criterio:
            query += " WHERE razon_social LIKE ? OR nombre_fantasia LIKE ? OR cuit_dni LIKE ?"
            params.extend([f'%{criterio}%', f'%{criterio}%', f'%{criterio}%'])
        query += " ORDER BY razon_social"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener clientes: {e}")
        return []
    finally:
        if conn: conn.close()

def obtener_todos_los_clientes_para_reporte():
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, razon_social FROM Clientes ORDER BY razon_social")
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener todos los clientes: {e}")
        return []
    finally:
        if conn: conn.close()

def obtener_cuenta_corriente_cliente(cliente_id, fecha_desde=None, fecha_hasta=None):
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = "SELECT fecha, tipo_movimiento, monto, saldo_resultante FROM CuentasCorrientesClientes WHERE cliente_id = ?"
        params = [cliente_id]
        if fecha_desde and fecha_hasta:
            query += " AND DATE(fecha) BETWEEN ? AND ?"
            params.extend([fecha_desde, fecha_hasta])
        query += " ORDER BY fecha, id"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener cuenta corriente del cliente: {e}")
        return []
    finally:
        if conn: conn.close()

def get_cliente_column_names():
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Clientes)")
        return [info[1] for info in cursor.fetchall()]
    finally:
        if conn: conn.close()

def obtener_cliente_por_id(id_cliente):
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM Clientes WHERE id = ?"
        cursor.execute(query, (id_cliente,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Error al obtener cliente por ID: {e}")
        return None
    finally:
        if conn: conn.close()

def modificar_cliente(datos):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        id_cliente = datos.pop('id')
        set_clause = ', '.join([f"{col} = ?" for col in datos.keys()])
        valores = tuple(datos.values()) + (id_cliente,)
        query = f"UPDATE Clientes SET {set_clause} WHERE id = ?"
        cursor.execute(query, valores)
        conn.commit()
        return "Cliente modificado correctamente."
    except sqlite3.IntegrityError:
        return "Error: El CUIT/DNI ingresado ya pertenece a otro cliente."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn: conn.close()

def eliminar_cliente(id_cliente):
    conn = _crear_conexion()
    if conn is None: return
    try:
        cursor = conn.cursor()
        query = "DELETE FROM Clientes WHERE id = ?"
        cursor.execute(query, (id_cliente,))
        conn.commit()
    finally:
        if conn: conn.close()

def buscar_clientes_pos(criterio):
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = "SELECT id, razon_social, cuit_dni FROM Clientes WHERE razon_social LIKE ? OR cuit_dni LIKE ? ORDER BY razon_social LIMIT 10"
        params = (f'%{criterio}%', f'%{criterio}%')
        cursor.execute(query, params)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al buscar clientes para POS: {e}")
        return []
    finally:
        if conn: conn.close()

def registrar_cobro_cuenta_corriente(caja_id, cliente_id, pagos, concepto):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    
    monto_total_cobrado = sum(p['monto'] for p in pagos)

    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("SELECT saldo_resultante FROM CuentasCorrientesClientes WHERE cliente_id = ? ORDER BY id DESC LIMIT 1", (cliente_id,))
        ultimo_saldo_res = cursor.fetchone()
        ultimo_saldo = ultimo_saldo_res[0] if ultimo_saldo_res else 0.0
        nuevo_saldo = ultimo_saldo - monto_total_cobrado
        query_cc = "INSERT INTO CuentasCorrientesClientes (cliente_id, fecha, tipo_movimiento, monto, saldo_resultante) VALUES (?, date('now'), 'COBRO', ?, ?)"
        cursor.execute(query_cc, (cliente_id, -monto_total_cobrado, nuevo_saldo))
        for pago in pagos:
            query_mov_caja = "INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id, cliente_id) VALUES (?, ?, 'INGRESO', ?, ?, ?, ?)"
            cursor.execute(query_mov_caja, (caja_id, datetime.now(), concepto, pago['monto'], pago['medio_pago_id'], cliente_id))
        conn.commit()
        return "Cobro registrado exitosamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error de base de datos: {e}"
    finally:
        if conn: conn.close()

def obtener_clientes_con_saldo():
    """
    Devuelve una lista de clientes con saldo en su cuenta corriente.
    """
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        # Consulta corregida para ser compatible con SQLite
        query = """
            SELECT c.id, c.razon_social, cta.saldo_resultante
            FROM (
                SELECT cliente_id, saldo_resultante, MAX(fecha)
                FROM CuentasCorrientesClientes
                GROUP BY cliente_id
            ) AS cta
            JOIN Clientes c ON c.id = cta.cliente_id
            WHERE cta.saldo_resultante != 0
            ORDER BY c.razon_social
        """
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener clientes con saldo: {e}")
        return []
    finally:
        if conn: conn.close()