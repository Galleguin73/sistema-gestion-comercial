# Ubicación: app/database/proveedores_db.py (MODIFICADO)
import sqlite3
from datetime import datetime
from app.utils.db_manager import crear_conexion


def agregar_proveedor(datos):
    conn = crear_conexion()
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
    conn = crear_conexion()
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
    finally:
        if conn: conn.close()

def obtener_todos_los_proveedores_para_reporte():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, razon_social FROM Proveedores ORDER BY razon_social")
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def obtener_cuenta_corriente_proveedor(proveedor_id, fecha_desde=None, fecha_hasta=None):
    conn = crear_conexion()
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
    finally:
        if conn: conn.close()

def get_proveedor_column_names():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Proveedores)")
        return [info[1] for info in cursor.fetchall()]
    finally:
        if conn: conn.close()

def obtener_proveedor_por_id(id_proveedor):
    conn = crear_conexion()
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
    conn = crear_conexion()
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
    conn = crear_conexion()
    if conn is None: return
    try:
        cursor = conn.cursor()
        query = "DELETE FROM Proveedores WHERE id = ?"
        cursor.execute(query, (id_proveedor,))
        conn.commit()
    finally:
        if conn: conn.close()

def obtener_compras_impagas(proveedor_id):
    conn = crear_conexion()
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

def registrar_pago_a_facturas(caja_id, proveedor_id, pagos_realizados, ids_facturas, concepto):
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        pago_total = sum(p['monto'] for p in pagos_realizados)
        for pago in pagos_realizados:
            query_caja = "INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id, proveedor_id) VALUES (?, date('now'), 'EGRESO', ?, ?, ?, ?)"
            cursor.execute(query_caja, (caja_id, concepto, pago['monto'], pago['medio_pago_id'], proveedor_id))

        monto_a_aplicar = pago_total
        for compra_id in ids_facturas:
            if monto_a_aplicar <= 0: break
            cursor.execute("SELECT saldo_pendiente FROM Compras WHERE id = ?", (compra_id,))
            saldo_actual = cursor.fetchone()[0]
            monto_aplicado = min(monto_a_aplicar, saldo_actual)
            nuevo_saldo = saldo_actual - monto_aplicado
            estado_nuevo = 'PAGADA' if nuevo_saldo < 0.01 else 'PAGO PARCIAL'
            cursor.execute("UPDATE Compras SET saldo_pendiente = ?, estado = ? WHERE id = ?", (nuevo_saldo, estado_nuevo, compra_id))
            monto_a_aplicar -= monto_aplicado

        cursor.execute("SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1", (proveedor_id,))
        ultimo_saldo = (cursor.fetchone() or [0.0])[0]
        nuevo_saldo_cc = ultimo_saldo - pago_total
        query_cc = "INSERT INTO CuentasCorrientesProveedores (proveedor_id, fecha, tipo_movimiento, monto, saldo_resultante) VALUES (?, date('now'), 'PAGO', ?, ?)"
        cursor.execute(query_cc, (proveedor_id, -pago_total, nuevo_saldo_cc))
        
        conn.commit()
        return "Pago registrado y aplicado exitosamente."
    except Exception as e:
        conn.rollback()
        return f"Error al registrar el pago: {e}"
    finally:
        if conn: conn.close()

def obtener_proveedor_por_nombre(nombre_proveedor):
    conn = crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Proveedores WHERE razon_social = ?", (nombre_proveedor,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    finally:
        if conn: conn.close()

def obtener_proveedores_con_saldo():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT p.id, p.razon_social, cta.saldo_resultante
            FROM (
                SELECT proveedor_id, saldo_resultante
                FROM CuentasCorrientesProveedores
                WHERE id IN (SELECT MAX(id) FROM CuentasCorrientesProveedores GROUP BY proveedor_id)
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

def obtener_facturas_impagas(criterio=None):
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT
                c.id, p.razon_social, c.numero_factura, c.fecha_compra,
                c.fecha_vencimiento, c.monto_total, c.saldo_pendiente
            FROM Compras c
            JOIN Proveedores p ON c.proveedor_id = p.id
            WHERE c.estado IN ('IMPAGA', 'PAGO PARCIAL') AND c.saldo_pendiente > 0.01
        """
        params = []
        if criterio:
            query += " AND (p.razon_social LIKE ? OR c.numero_factura LIKE ?)"
            params.extend([f'%{criterio}%', f'%{criterio}%'])
        query += " ORDER BY c.fecha_vencimiento ASC, c.fecha_compra ASC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def registrar_pago_a_facturas(caja_id, proveedor_id, pagos_realizados, ids_facturas, concepto):
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        pago_total = sum(p['monto'] for p in pagos_realizados)
        for pago in pagos_realizados:
            query_caja = """
                INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id, proveedor_id)
                VALUES (?, date('now'), 'EGRESO', ?, ?, ?, ?)
            """
            cursor.execute(query_caja, (caja_id, concepto, pago['monto'], pago['medio_pago_id'], proveedor_id))

        monto_a_aplicar = pago_total
        for compra_id in ids_facturas:
            if monto_a_aplicar <= 0: break
            cursor.execute("SELECT saldo_pendiente FROM Compras WHERE id = ?", (compra_id,))
            saldo_actual = cursor.fetchone()[0]
            monto_aplicado = min(monto_a_aplicar, saldo_actual)
            nuevo_saldo = saldo_actual - monto_aplicado
            estado_nuevo = 'PAGADA' if nuevo_saldo < 0.01 else 'PAGO PARCIAL'
            cursor.execute("UPDATE Compras SET saldo_pendiente = ?, estado = ? WHERE id = ?", (nuevo_saldo, estado_nuevo, compra_id))
            monto_a_aplicar -= monto_aplicado

        cursor.execute("SELECT saldo_resultante FROM CuentasCorrientesProveedores WHERE proveedor_id = ? ORDER BY id DESC LIMIT 1", (proveedor_id,))
        ultimo_saldo = (cursor.fetchone() or [0.0])[0]
        nuevo_saldo_cc = ultimo_saldo - pago_total
        query_cc = "INSERT INTO CuentasCorrientesProveedores (proveedor_id, fecha, tipo_movimiento, monto, saldo_resultante) VALUES (?, date('now'), 'PAGO', ?, ?)"
        cursor.execute(query_cc, (proveedor_id, -pago_total, nuevo_saldo_cc))
        
        conn.commit()
        return "Pago registrado y aplicado exitosamente."
    except Exception as e:
        conn.rollback()
        return f"Error al registrar el pago: {e}"
        
# --- NUEVA FUNCIÓN AÑADIDA ---
def obtener_proveedor_por_nombre(nombre_proveedor):
    """Obtiene el ID de un proveedor a partir de su razón social."""
    conn = crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # Usamos LIKE para que coincida aunque el combo tenga info extra como el CUIT
        cursor.execute("SELECT id FROM Proveedores WHERE razon_social LIKE ?", (f'{nombre_proveedor}%',))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    except sqlite3.Error as e:
        print(f"Error al obtener proveedor por nombre: {e}")
        return None
    finally:
        if conn: conn.close()