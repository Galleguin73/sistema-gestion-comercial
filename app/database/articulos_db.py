from datetime import datetime
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

# --- FUNCIONES DE MARCAS ---
def obtener_marcas():
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM Marcas ORDER BY nombre")
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()

def agregar_marca(nombre):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Marcas (nombre) VALUES (?)", (nombre,))
        conn.commit()
        return "Marca agregada correctamente."
    except sqlite3.IntegrityError:
        return "Error: Esa marca ya existe."
    finally:
        if conn:
            conn.close()

def modificar_marca(marca_id, nuevo_nombre):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Marcas SET nombre = ? WHERE id = ?", (nuevo_nombre, marca_id))
        conn.commit()
        return "Marca modificada correctamente."
    except sqlite3.IntegrityError:
        return "Error: Ese nombre de marca ya existe."
    finally:
        if conn:
            conn.close()

def eliminar_marca(marca_id):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Marcas WHERE id = ?", (marca_id,))
        conn.commit()
        return "Marca eliminada correctamente."
    except sqlite3.IntegrityError:
        return "Error: No se puede eliminar la marca porque está siendo utilizada por uno o más artículos."
    except Exception as e:
        return f"Error inesperado: {e}"
    finally:
        if conn:
            conn.close()

# --- FUNCIONES DE RUBROS Y SUBRUBROS ---
def obtener_rubros():
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM Rubros ORDER BY nombre")
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()
            
def obtener_subrubros_por_rubro(rubro_id):
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM Subrubros WHERE rubro_id = ? ORDER BY nombre", (rubro_id,))
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()

def obtener_rubro_de_subrubro(subrubro_id):
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT r.id, r.nombre FROM Rubros r JOIN Subrubros s ON r.id = s.rubro_id WHERE s.id = ?"
        cursor.execute(query, (subrubro_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Error al obtener rubro de subrubro: {e}")
        return None
    finally:
        if conn:
            conn.close()

def agregar_rubro(nombre):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Rubros (nombre) VALUES (?)", (nombre,))
        conn.commit()
        return "Rubro agregado correctamente."
    except sqlite3.IntegrityError:
        return "Error: Ese rubro ya existe."
    finally:
        if conn:
            conn.close()

def eliminar_rubro(rubro_id):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Subrubros WHERE rubro_id = ?", (rubro_id,))
        cursor.execute("DELETE FROM Rubros WHERE id = ?", (rubro_id,))
        conn.commit()
        return "Rubro eliminado correctamente."
    finally:
        if conn:
            conn.close()

def agregar_subrubro(nombre, rubro_id):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Subrubros (nombre, rubro_id) VALUES (?, ?)", (nombre, rubro_id))
        conn.commit()
        return "Subrubro agregado correctamente."
    except sqlite3.Error as e:
        return f"Error: {e}"
    finally:
        if conn:
            conn.close()

def eliminar_subrubro(subrubro_id):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Subrubros WHERE id = ?", (subrubro_id,))
        conn.commit()
        return "Subrubro eliminado correctamente."
    finally:
        if conn:
            conn.close()

# --- FUNCIONES DE ARTÍCULOS ---
def get_articulo_column_names():
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Articulos)")
        return [info[1] for info in cursor.fetchall()]
    finally:
        if conn:
            conn.close()

def obtener_ultimo_id_articulo():
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM Articulos")
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        if conn:
            conn.close()

def agregar_articulo(datos):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        columnas = ', '.join(datos.keys())
        placeholders = ', '.join(['?']*len(datos))
        valores = tuple(datos.values())
        query = f"INSERT INTO Articulos ({columnas}) VALUES ({placeholders})"
        cursor.execute(query, valores)
        conn.commit()
        return "Artículo agregado correctamente."
    except sqlite3.IntegrityError:
        return "Error: El código de barras ingresado ya existe."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def obtener_articulos(criterio=None, incluir_inactivos=False):
    """
    Obtiene una lista de artículos, opcionalmente filtrada por un criterio
    de búsqueda en código o nombre.
    """
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.codigo_barras, m.nombre, a.nombre, a.stock, a.precio_venta, a.estado
            FROM Articulos a
            LEFT JOIN Marcas m ON a.marca_id = m.id
        """
        params = []
        
        where_clauses = []
        if not incluir_inactivos:
            where_clauses.append("a.estado = 'Activo'")
        
        if criterio:
            where_clauses.append("(a.codigo_barras LIKE ? OR a.nombre LIKE ?)")
            params.extend([f'%{criterio}%', f'%{criterio}%'])
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY a.nombre"
        
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()

def obtener_articulos_para_compra(criterio=None):
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.codigo_barras, m.nombre, a.nombre, a.stock
            FROM Articulos a
            LEFT JOIN Marcas m ON a.marca_id = m.id
        """
        params = []
        if criterio:
            query += " WHERE (a.codigo_barras LIKE ? OR a.nombre LIKE ?) AND a.estado = 'Activo'"
            params.extend([f'%{criterio}%', f'%{criterio}%'])
        else:
            query += " WHERE a.estado = 'Activo'"
        query += " ORDER BY a.nombre"
        cursor.execute(query, params)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener artículos para compra: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_articulo_por_id(articulo_id):
    conn = _crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM Articulos WHERE id = ?"
        cursor.execute(query, (articulo_id,))
        return cursor.fetchone()
    finally:
        if conn:
            conn.close()

def modificar_articulo(datos):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        id_articulo = datos.pop('id')
        set_clause = ', '.join([f"{col} = ?" for col in datos.keys()])
        valores = tuple(datos.values()) + (id_articulo,)
        query = f"UPDATE Articulos SET {set_clause} WHERE id = ?"
        cursor.execute(query, valores)
        conn.commit()
        return "Artículo modificado correctamente."
    except sqlite3.IntegrityError:
        return "Error: El código de barras ya pertenece a otro artículo."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def buscar_articulos_pos(criterio):
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.nombre, a.precio_venta, a.unidad_de_medida, m.nombre
            FROM Articulos a
            LEFT JOIN Marcas m ON a.marca_id = m.id
            WHERE (UPPER(a.codigo_barras) LIKE UPPER(?) OR UPPER(a.nombre) LIKE UPPER(?))
            AND a.estado = 'Activo'
            ORDER BY a.nombre
            LIMIT 10
        """
        params = (f'%{criterio}%', f'%{criterio}%')
        cursor.execute(query, params)
        resultados = []
        for row in cursor.fetchall():
            descripcion_completa = f"{row[4]} - {row[1]}" if row[4] else row[1]
            resultados.append((row[0], descripcion_completa, row[2], row[3]))
        return resultados
    except sqlite3.Error as e:
        print(f"Error al buscar artículos para POS: {e}")
        return []
    finally:
        if conn:
            conn.close()

def desactivar_articulo(articulo_id):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Articulos SET estado = 'Inactivo' WHERE id = ?", (articulo_id,))
        conn.commit()
        return "Artículo desactivado correctamente."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def reactivar_articulo(articulo_id):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Articulos SET estado = 'Activo' WHERE id = ?", (articulo_id,))
        conn.commit()
        return "Artículo reactivado correctamente."
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def realizar_ajuste_stock(articulo_id, tipo_ajuste, cantidad, concepto):
    conn = _crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("SELECT stock FROM Articulos WHERE id = ?", (articulo_id,))
        stock_anterior = cursor.fetchone()[0]

        if tipo_ajuste == 'INGRESO':
            stock_nuevo = stock_anterior + cantidad
        elif tipo_ajuste == 'EGRESO':
            stock_nuevo = stock_anterior - cantidad
        else:
            raise ValueError("Tipo de ajuste no válido")

        if stock_nuevo < 0:
            raise ValueError("El ajuste no puede resultar en stock negativo.")

        cursor.execute("UPDATE Articulos SET stock = ? WHERE id = ?", (stock_nuevo, articulo_id))

        query_log = """
            INSERT INTO AjustesStock 
            (articulo_id, fecha, tipo_ajuste, cantidad, concepto, stock_anterior, stock_nuevo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query_log, (
            articulo_id, datetime.now(), tipo_ajuste, cantidad, concepto, stock_anterior, stock_nuevo
        ))
        conn.commit()
        return "Ajuste de stock realizado exitosamente."
    except Exception as e:
        conn.rollback()
        return f"Error al realizar el ajuste: {e}"
    finally:
        if conn:
            conn.close()

def obtener_articulos_stock_bajo():
    conn = _crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT nombre, stock, stock_minimo
            FROM Articulos
            WHERE estado = 'Activo' AND stock_minimo > 0 AND stock <= stock_minimo
            ORDER BY nombre
        """
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener artículos con stock bajo: {e}")
        return []
    finally:
        if conn:
            conn.close()