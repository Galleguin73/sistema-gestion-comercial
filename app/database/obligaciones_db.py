# Ubicación: app/database/obligaciones_db.py (Actualizado)

import sqlite3
from datetime import datetime
from app.utils.db_manager import crear_conexion

# --- CRUD PARA TiposDeObligacion (Sin cambios) ---
def obtener_tipos_de_obligacion(criterio=None):
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = "SELECT id, nombre, categoria, descripcion FROM TiposDeObligacion"
        params = []
        if criterio:
            query += " WHERE nombre LIKE ? OR categoria LIKE ?"
            params.extend([f'%{criterio}%', f'%{criterio}%'])
        query += " ORDER BY categoria, nombre"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def obtener_tipo_por_id(tipo_id):
    conn = crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM TiposDeObligacion WHERE id = ?", (tipo_id,))
        return cursor.fetchone()
    finally:
        if conn: conn.close()

def get_tipo_column_names():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(TiposDeObligacion)")
        return [info[1] for info in cursor.fetchall()]
    finally:
        if conn: conn.close()

def agregar_tipo_de_obligacion(datos):
    conn = crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        columnas = ', '.join(datos.keys())
        placeholders = ', '.join(['?'] * len(datos))
        valores = tuple(datos.values())
        query = f"INSERT INTO TiposDeObligacion ({columnas}) VALUES ({placeholders})"
        cursor.execute(query, valores)
        conn.commit()
        return "Tipo de obligación agregado correctamente."
    except sqlite3.IntegrityError:
        return "Error: Ya existe un tipo de obligación con ese nombre."
    finally:
        if conn: conn.close()

def modificar_tipo_de_obligacion(datos):
    conn = crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        tipo_id = datos.pop('id')
        set_clause = ', '.join([f"{col} = ?" for col in datos.keys()])
        valores = tuple(datos.values()) + (tipo_id,)
        query = f"UPDATE TiposDeObligacion SET {set_clause} WHERE id = ?"
        cursor.execute(query, valores)
        conn.commit()
        return "Tipo de obligación modificado correctamente."
    except sqlite3.IntegrityError:
        return "Error: El nombre ya pertenece a otro tipo de obligación."
    finally:
        if conn: conn.close()

def eliminar_tipo_de_obligacion(tipo_id):
    conn = crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM TiposDeObligacion WHERE id = ?", (tipo_id,))
        conn.commit()
        return "Tipo de obligación eliminado correctamente."
    except sqlite3.IntegrityError:
        return "Error: No se puede eliminar porque está siendo utilizado en la agenda."
    finally:
        if conn: conn.close()

# --- FUNCIONES PARA LA AGENDA ---

def obtener_obligaciones(filtros):
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.fecha_vencimiento, a.periodo, t.nombre, t.categoria, a.monto_original, a.estado
            FROM AgendaDeObligaciones a
            JOIN TiposDeObligacion t ON a.tipo_obligacion_id = t.id
        """
        params = []
        where_clauses = ["a.estado != 'ANULADA'"]
        
        if filtros.get("fecha_desde") and filtros.get("fecha_hasta"):
            where_clauses.append("a.fecha_vencimiento BETWEEN ? AND ?")
            params.extend([filtros["fecha_desde"], filtros["fecha_hasta"]])
        
        if filtros.get("estado") and filtros["estado"] != "Todas":
            where_clauses.append("a.estado = ?")
            params.append(filtros["estado"])

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY a.fecha_vencimiento ASC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener obligaciones: {e}")
        return []
    finally:
        if conn: conn.close()

def registrar_obligacion(datos):
    conn = crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO AgendaDeObligaciones 
            (tipo_obligacion_id, fecha_vencimiento, periodo, monto_original, estado, observaciones)
            VALUES (?, ?, ?, ?, 'PENDIENTE', ?)
        """
        cursor.execute(query, (
            datos['tipo_obligacion_id'], datos['fecha_vencimiento'], datos['periodo'],
            datos['monto_original'], datos.get('observaciones')
        ))
        conn.commit()
        return "Obligación registrada exitosamente."
    except sqlite3.Error as e:
        return f"Error de base de datos al registrar obligación: {e}"
    finally:
        if conn: conn.close()
        
def registrar_pago_obligacion(obligacion_id, caja_id, fecha_pago, pagos):
    conn = crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        total_pagado = sum(p['monto'] for p in pagos)
        
        query_update = """
            UPDATE AgendaDeObligaciones 
            SET estado = 'PAGADA', monto_pagado = ?, fecha_pago = ?, caja_id_pago = ?
            WHERE id = ?
        """
        cursor.execute(query_update, (total_pagado, fecha_pago, caja_id, obligacion_id))

        cursor.execute("SELECT t.nombre FROM AgendaDeObligaciones a JOIN TiposDeObligacion t ON a.tipo_obligacion_id = t.id WHERE a.id = ?", (obligacion_id,))
        concepto_base = cursor.fetchone()[0]

        for pago in pagos:
            concepto = f"Pago obligación: {concepto_base}"
            query_caja = "INSERT INTO MovimientosCaja (caja_id, fecha, tipo, concepto, monto, medio_pago_id, obligacion_id) VALUES (?, ?, 'EGRESO', ?, ?, ?, ?)"
            cursor.execute(query_caja, (caja_id, fecha_pago, concepto, pago['monto'], pago['medio_pago_id'], obligacion_id))

        conn.commit()
        return "Pago registrado exitosamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error al registrar el pago: {e}"
    finally:
        if conn: conn.close()

def eliminar_obligacion(obligacion_id):
    conn = crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        cursor.execute("DELETE FROM MovimientosCaja WHERE obligacion_id = ? AND tipo = 'EGRESO'", (obligacion_id,))
        cursor.execute("DELETE FROM AgendaDeObligaciones WHERE id = ?", (obligacion_id,))
        
        conn.commit()
        return "Obligación eliminada exitosamente."
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error al eliminar la obligación: {e}"
    finally:
        if conn: conn.close()

def obtener_obligacion_por_id(obligacion_id):
    conn = crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.fecha_vencimiento, a.periodo, t.nombre, t.categoria, a.monto_original, a.estado
            FROM AgendaDeObligaciones a
            JOIN TiposDeObligacion t ON a.tipo_obligacion_id = t.id
            WHERE a.id = ?
        """
        cursor.execute(query, (obligacion_id,))
        return cursor.fetchone()
    finally:
        if conn: conn.close()

def obtener_obligaciones_proximas(dias=7):
    """
    NUEVO: Obtiene las obligaciones pendientes que vencen en los próximos días.
    """
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.fecha_vencimiento, t.nombre, a.monto_original
            FROM AgendaDeObligaciones a
            JOIN TiposDeObligacion t ON a.tipo_obligacion_id = t.id
            WHERE a.estado = 'PENDIENTE'
              AND a.fecha_vencimiento BETWEEN DATE('now', 'localtime') AND DATE('now', 'localtime', '+' || ? || ' days')
            ORDER BY a.fecha_vencimiento ASC
        """
        cursor.execute(query, (dias,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener próximas obligaciones: {e}")
        return []
    finally:
        if conn: conn.close()