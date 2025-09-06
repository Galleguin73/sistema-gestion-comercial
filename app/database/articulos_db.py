from datetime import datetime
import sqlite3
from app.utils.db_manager import crear_conexion

# --- GESTIÓN DE ARTÍCULOS ---

def agregar_articulo(datos):
    """
    Agrega un nuevo artículo y su primer lote, asegurándose de que cada
    dato se guarde en la tabla correcta.
    """
    conn = crear_conexion()
    if conn is None: return "Error de conexión"
    
    stock_inicial = datos.get('stock', 0.0)
    lote_inicial = datos.pop('lote', None)
    vencimiento_inicial = datos.pop('fecha_vencimiento', None)
    
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        columnas = ', '.join(datos.keys())
        placeholders = ', '.join(['?'] * len(datos))
        valores = tuple(datos.values())
        query_articulo = f"INSERT INTO Articulos ({columnas}) VALUES ({placeholders})"
        cursor.execute(query_articulo, valores)
        articulo_id = cursor.lastrowid
        
        query_lote = """
            INSERT INTO StockLotes (articulo_id, cantidad, lote, fecha_vencimiento, activo)
            VALUES (?, ?, ?, ?, 1)
        """
        cursor.execute(query_lote, (articulo_id, stock_inicial, lote_inicial, vencimiento_inicial))

        conn.commit()
        return "Artículo agregado correctamente."
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return f"Error de integridad: Es posible que el código de barras ya exista.\n\nDetalle: {e}"
    except sqlite3.Error as e:
        conn.rollback()
        return f"Error de base de datos: {e}"
    finally:
        if conn:
            conn.close()

def modificar_articulo(datos):
    """Modifica los datos maestros de un artículo, sin tocar el stock."""
    conn = crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        id_articulo = datos.pop('id')
        
        if 'stock' in datos:
            del datos['stock']
            
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
        if conn: conn.close()

def obtener_articulos(criterio=None, incluir_inactivos=False):
    """
    Obtiene artículos y calcula el stock total sumando los lotes activos.
    """
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                a.id, a.codigo_barras, m.nombre, a.nombre, 
                IFNULL((SELECT SUM(sl.cantidad) FROM StockLotes sl WHERE sl.articulo_id = a.id AND sl.activo = 1), 0) as stock_total,
                a.precio_venta, a.estado, a.unidad_de_medida, a.imagen_path
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
        if conn: conn.close()

def obtener_articulos_para_compra(criterio=None):
    """
    NUEVO: Esta función es la que necesita el módulo de Compras.
    Devuelve una lista simple de artículos para ser seleccionados.
    """
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.codigo_barras, m.nombre, a.nombre 
            FROM Articulos a 
            LEFT JOIN Marcas m ON a.marca_id = m.id
        """
        params = []
        where_clauses = ["a.estado = 'Activo'"]
        
        if criterio:
            where_clauses.append("(a.codigo_barras LIKE ? OR a.nombre LIKE ?)")
            params.extend([f'%{criterio}%', f'%{criterio}%'])
        
        query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY a.nombre"

        cursor.execute(query, params)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener artículos para compra: {e}")
        return []
    finally:
        if conn: conn.close()


def obtener_articulo_por_id(articulo_id):
    """Obtiene los datos maestros de un artículo por su ID."""
    conn = crear_conexion()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM Articulos WHERE id = ?"
        cursor.execute(query, (articulo_id,))
        return cursor.fetchone()
    finally:
        if conn: conn.close()

def buscar_articulos_pos(criterio):
    """
    Busca artículos para el POS.
    """
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.nombre, a.precio_venta, a.unidad_de_medida, m.nombre as marca_nombre, a.imagen_path
            FROM Articulos a
            LEFT JOIN Marcas m ON a.marca_id = m.id
            WHERE (UPPER(a.codigo_barras) LIKE UPPER(?) OR UPPER(a.nombre) LIKE UPPER(?))
            AND a.estado = 'Activo' ORDER BY a.nombre LIMIT 10
        """
        params = (f'%{criterio}%', f'%{criterio}%')
        cursor.execute(query, params)
        resultados = []
        for row in cursor.fetchall():
            descripcion_completa = f"{row[4]} - {row[1]}" if row[4] else row[1]
            resultados.append((row[0], descripcion_completa, row[2], row[3], row[5]))
        return resultados
    except sqlite3.Error as e:
        print(f"Error al buscar artículos para POS: {e}")
        return []
    finally:
        if conn: conn.close()

def desactivar_articulo(articulo_id):
    conn = crear_conexion()
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
    conn = crear_conexion()
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

def get_articulo_column_names():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Articulos)")
        return [info[1] for info in cursor.fetchall()]
    finally:
        if conn: conn.close()

# --- GESTIÓN DE STOCK POR LOTES ---

def obtener_lotes_disponibles_para_venta(articulo_id):
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT id, cantidad, lote, fecha_vencimiento, fecha_ingreso
            FROM StockLotes
            WHERE articulo_id = ? AND cantidad > 0 AND activo = 1
            ORDER BY 
                CASE WHEN fecha_vencimiento IS NULL THEN 1 ELSE 0 END, 
                fecha_vencimiento ASC, 
                fecha_ingreso ASC
        """
        cursor.execute(query, (articulo_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener lotes disponibles: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_articulos_stock_bajo():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.nombre, 
                   IFNULL((SELECT SUM(sl.cantidad) FROM StockLotes sl WHERE sl.articulo_id = a.id AND sl.activo = 1), 0) as stock_actual,
                   a.stock_minimo
            FROM Articulos a
            WHERE a.estado = 'Activo' 
              AND a.stock_minimo > 0 
              AND stock_actual <= a.stock_minimo
            ORDER BY a.nombre
        """
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener artículos con stock bajo: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_articulos_proximos_a_vencer(dias=10):
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.nombre, sl.lote, sl.fecha_vencimiento, sl.cantidad
            FROM StockLotes sl
            JOIN Articulos a ON sl.articulo_id = a.id
            WHERE sl.fecha_vencimiento IS NOT NULL
              AND sl.cantidad > 0
              AND DATE(sl.fecha_vencimiento) >= DATE('now', 'localtime')
              AND DATE(sl.fecha_vencimiento) <= DATE('now', 'localtime', '+' || ? || ' days')
            ORDER BY DATE(sl.fecha_vencimiento) ASC
        """
        cursor.execute(query, (dias,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener artículos próximos a vencer: {e}")
        return []
    finally:
        if conn:
            conn.close()

def obtener_lotes_por_articulo(articulo_id):
    """
    Obtiene una lista de todos los lotes para un artículo específico,
    para ser mostrados en la interfaz.
    """
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT id, lote, cantidad, fecha_vencimiento, fecha_ingreso, activo
            FROM StockLotes
            WHERE articulo_id = ?
            ORDER BY fecha_ingreso DESC
        """
        cursor.execute(query, (articulo_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener los lotes del artículo: {e}")
        return []
    finally:
        if conn:
            conn.close()


# --- GESTIÓN DE MARCAS Y RUBROS ---

def obtener_marcas():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM Marcas ORDER BY nombre")
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def agregar_marca(nombre):
    conn = crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Marcas (nombre) VALUES (?)", (nombre,))
        conn.commit()
        return "Marca agregada correctamente."
    except sqlite3.IntegrityError:
        return "Error: Esa marca ya existe."
    finally:
        if conn: conn.close()

def modificar_marca(marca_id, nuevo_nombre):
    conn = crear_conexion()
    if conn is None: return "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Marcas SET nombre = ? WHERE id = ?", (nuevo_nombre, marca_id))
        conn.commit()
        return "Marca modificada correctamente."
    except sqlite3.IntegrityError:
        return "Error: Ese nombre de marca ya existe."
    finally:
        if conn: conn.close()

def eliminar_marca(marca_id):
    conn = crear_conexion()
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
        if conn: conn.close()

def obtener_rubros():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM Rubros ORDER BY nombre")
        return cursor.fetchall()
    finally:
        if conn: conn.close()
            
def obtener_subrubros_por_rubro(rubro_id):
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM Subrubros WHERE rubro_id = ? ORDER BY nombre", (rubro_id,))
        return cursor.fetchall()
    finally:
        if conn: conn.close()

def obtener_rubro_de_subrubro(subrubro_id):
    conn = crear_conexion()
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
        if conn: conn.close()


# --- MÓDULO DE EMPAQUETADO ---

def obtener_articulos_empaquetado():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.codigo_barras, m.nombre, a.nombre, 
                   IFNULL((SELECT SUM(sl.cantidad) FROM StockLotes sl WHERE sl.articulo_id = a.id AND sl.activo = 1), 0) as stock_total,
                   a.precio_venta, a.estado
            FROM Articulos a
            LEFT JOIN Marcas m ON a.marca_id = m.id
            JOIN Subrubros sr ON a.subrubro_id = sr.id
            JOIN Rubros r ON sr.rubro_id = r.id
            WHERE r.nombre = 'EMPAQUETADO PROPIO' AND a.estado = 'Activo'
            ORDER BY a.nombre
        """
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener artículos de empaquetado: {e}")
        return []
    finally:
        if conn: conn.close()

def realizar_produccion_empaquetado(articulo_final_id, cantidad_a_producir):
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        composicion = obtener_composicion_articulo(articulo_final_id)
        if not composicion:
            raise ValueError("El producto no tiene componentes definidos en su receta.")

        for comp_id, _, cantidad_necesaria_por_unidad in composicion:
            stock_requerido = cantidad_necesaria_por_unidad * cantidad_a_producir
            
            lotes_componente = obtener_lotes_disponibles_para_venta(comp_id)
            stock_disponible_componente = sum(lote[1] for lote in lotes_componente)

            if stock_disponible_componente < stock_requerido:
                cursor.execute("SELECT nombre FROM Articulos WHERE id = ?", (comp_id,))
                nombre_comp = cursor.fetchone()[0]
                raise ValueError(f"Stock insuficiente para '{nombre_comp}'. Se necesitan {stock_requerido} y hay {stock_disponible_componente}.")

            cantidad_restante_a_descontar = stock_requerido
            for lote_id, cantidad_en_lote, _, _, _ in lotes_componente:
                if cantidad_restante_a_descontar <= 0: break
                
                cantidad_a_tomar_de_lote = min(cantidad_restante_a_descontar, cantidad_en_lote)
                cursor.execute("UPDATE StockLotes SET cantidad = cantidad - ? WHERE id = ?", 
                               (cantidad_a_tomar_de_lote, lote_id))
                cantidad_restante_a_descontar -= cantidad_a_tomar_de_lote
        
        lote_nombre = f"PROD-{datetime.now().strftime('%Y%m%d-%H%M')}"
        query_nuevo_lote = """
            INSERT INTO StockLotes (articulo_id, cantidad, lote, activo)
            VALUES (?, ?, ?, 1)
        """
        cursor.execute(query_nuevo_lote, (articulo_final_id, cantidad_a_producir, lote_nombre))

        conn.commit()
        return f"Producción de {cantidad_a_producir} unidades completada exitosamente."
    except Exception as e:
        conn.rollback()
        return f"Error durante la producción: {e}"
    finally:
        if conn:
            conn.close()

def obtener_articulos_granel():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT a.id, a.nombre, m.nombre
            FROM Articulos a
            LEFT JOIN Marcas m ON a.marca_id = m.id
            JOIN Subrubros sr ON a.subrubro_id = sr.id
            JOIN Rubros r ON sr.rubro_id = r.id
            WHERE r.nombre = 'GRANEL' AND a.estado = 'Activo'
            ORDER BY a.nombre
        """
        cursor.execute(query)
        return [(row[0], f"{row[2]} - {row[1]}") for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Error al obtener artículos del rubro Granel: {e}")
        return []
    finally:
        if conn:
            conn.close()

def agregar_articulo_compuesto(datos_articulo, componentes):
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        columnas = ', '.join(datos_articulo.keys())
        placeholders = ', '.join(['?'] * len(datos_articulo))
        valores = tuple(datos_articulo.values())
        query = f"INSERT INTO Articulos ({columnas}) VALUES ({placeholders})"
        cursor.execute(query, valores)
        articulo_final_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO StockLotes (articulo_id, cantidad, activo) VALUES (?, 0, 1)", (articulo_final_id,))
        
        if not componentes:
            raise ValueError("El artículo debe tener al menos un componente.")
        for id_componente, cantidad in componentes:
            query_comp = "INSERT INTO ComposicionArticulos (articulo_final_id, articulo_componente_id, cantidad_componente) VALUES (?, ?, ?)"
            cursor.execute(query_comp, (articulo_final_id, id_componente, cantidad))
        conn.commit()
        return "Artículo de empaquetado creado correctamente."
    except Exception as e:
        conn.rollback()
        return f"Error al crear el artículo compuesto: {e}"
    finally:
        if conn:
            conn.close()

def obtener_composicion_articulo(articulo_id):
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                c.articulo_componente_id,
                a.nombre,
                m.nombre,
                c.cantidad_componente
            FROM ComposicionArticulos c
            JOIN Articulos a ON c.articulo_componente_id = a.id
            LEFT JOIN Marcas m ON a.marca_id = m.id
            WHERE c.articulo_final_id = ?
        """
        cursor.execute(query, (articulo_id,))
        return [(row[0], f"{row[2]} - {row[1]}", row[3]) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Error al obtener la composición: {e}")
        return []
    finally:
        if conn:
            conn.close()

def modificar_articulo_compuesto(articulo_id, datos_articulo, componentes):
    conn = crear_conexion()
    if conn is None: return "Error de conexión."
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        set_clause = ', '.join([f"{col} = ?" for col in datos_articulo.keys()])
        valores = tuple(datos_articulo.values()) + (articulo_id,)
        query_update = f"UPDATE Articulos SET {set_clause} WHERE id = ?"
        cursor.execute(query_update, valores)
        cursor.execute("DELETE FROM ComposicionArticulos WHERE articulo_final_id = ?", (articulo_id,))
        if not componentes:
            raise ValueError("El artículo debe tener al menos un componente.")
        for id_componente, cantidad in componentes:
            query_comp = "INSERT INTO ComposicionArticulos (articulo_final_id, articulo_componente_id, cantidad_componente) VALUES (?, ?, ?)"
            cursor.execute(query_comp, (articulo_final_id, id_componente, cantidad))
        conn.commit()
        return "Artículo de empaquetado modificado correctamente."
    except Exception as e:
        conn.rollback()
        return f"Error al modificar el artículo compuesto: {e}"
    finally:
        if conn:
            conn.close()

def obtener_subrubros_empaquetado():
    conn = crear_conexion()
    if conn is None: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Rubros WHERE nombre = 'EMPAQUETADO PROPIO'")
        rubro = cursor.fetchone()
        if not rubro:
            return []
        rubro_id = rubro[0]
        cursor.execute("SELECT id, nombre FROM Subrubros WHERE rubro_id = ? ORDER BY nombre", (rubro_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error al obtener subrubros de empaquetado: {e}")
        return []
    finally:
        if conn:
            conn.close()