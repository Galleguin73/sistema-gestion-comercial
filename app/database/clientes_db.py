import sqlite3
import os

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

def get_cliente_column_names():
    """Devuelve los nombres de las columnas de la tabla Clientes."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Clientes)")
        return [info[1] for info in cursor.fetchall()]
    finally:
        if conn:
            conn.close()

def agregar_cliente(datos):
    """Agrega un nuevo cliente a la base de datos."""
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
        if conn:
            conn.close()

def obtener_clientes():
    """Obtiene una lista de clientes para el Treeview principal."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, razon_social, nombre_fantasia, tipo_cuenta, fecha_alta, estado FROM Clientes ORDER BY razon_social")
        clientes = cursor.fetchall()
        return clientes
    except sqlite3.Error as e:
        print(f"Error al obtener clientes: {e}")
        return []
    finally:
        if conn:
            conn.close()
            
def obtener_todos_los_clientes_para_reporte():
    """Obtiene id y razón social de todos los clientes."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, razon_social FROM Clientes WHERE cuenta_corriente_habilitada = 1 ORDER BY razon_social")
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener todos los clientes: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_cuenta_corriente_cliente(cliente_id, fecha_desde=None, fecha_hasta=None):
    """Obtiene todos los movimientos de la cuenta corriente de un cliente, opcionalmente filtrado por fecha."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT fecha, tipo_movimiento, monto, saldo_resultante
            FROM CuentasCorrientesClientes
            WHERE cliente_id = ?
        """
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
        if conn:
            conn.close()

def obtener_cliente_por_id(id_cliente):
    """Obtiene todos los datos de un cliente específico por su ID."""
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM Clientes WHERE id = ?"
        cursor.execute(query, (id_cliente,))
        cliente = cursor.fetchone()
        return cliente
    except sqlite3.Error as e:
        print(f"Error al obtener cliente por ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

def modificar_cliente(datos):
    """Modifica los datos de un cliente existente."""
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
        if conn:
            conn.close()

def eliminar_cliente(id_cliente):
    """Elimina un cliente de la base de datos por su ID."""
    conn = _crear_conexion()
    if conn is None: return
    try:
        cursor = conn.cursor()
        query = "DELETE FROM Clientes WHERE id = ?"
        cursor.execute(query, (id_cliente,))
        conn.commit()
    finally:
        if conn:
            conn.close()
            
def buscar_clientes_pos(criterio):
    """Busca clientes por razón social o CUIT/DNI para el POS."""
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT id, razon_social, cuit_dni FROM Clientes
            WHERE UPPER(razon_social) LIKE UPPER(?) OR UPPER(cuit_dni) LIKE UPPER(?)
            ORDER BY razon_social
            LIMIT 10
        """
        params = (f'%{criterio}%', f'%{criterio}%')
        cursor.execute(query, params)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al buscar clientes para POS: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_ultimo_id_cliente():
    """Obtiene el ID del último cliente insertado."""
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM Clientes")
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        if conn:
            conn.close()