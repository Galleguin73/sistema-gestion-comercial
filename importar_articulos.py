# Nombre de archivo recomendado: importar_articulos.py
# Ubicación: En la carpeta raíz de tu proyecto (al mismo nivel que main.py)

import pandas as pd
import sqlite3
import os

# --- CONFIGURACIÓN ---
# 1. Asegúrate de que esta ruta apunte a tu archivo Excel.
#    Como el script está en la raíz, solo necesitas poner el nombre del archivo
#    si está en la misma carpeta.
RUTA_EXCEL = 'Lista de Articulos.xlsx'

# 2. Ruta a la base de datos (debería ser correcta si el script está en la raíz)
DB_PATH = os.path.join('database', 'gestion.db')

# 3. Mapeo de columnas del Excel a la base de datos (puedes ajustar si es necesario)
MAPEO_COLUMNAS = {
    'Código de barras': 'codigo_barras',
    'MARCA': 'marca_nombre',
    'Descripcion': 'nombre',
    'Precio Neto': 'precio_costo'
}

def importar_articulos():
    """
    Script para importar artículos desde un archivo Excel a la base de datos SQLite.
    """
    # --- PASO 1: LEER EL ARCHIVO EXCEL ---
    print(f"🔄 Leyendo el archivo Excel: {RUTA_EXCEL}...")
    try:
        # Usamos pandas para leer el archivo. openpyxl es el motor para archivos .xlsx
        df = pd.read_excel(RUTA_EXCEL, engine='openpyxl')
        # --- AÑADE ESTA LÍNEA AQUÍ ---
        print(f"💡 COLUMNAS ENCONTRADAS: {df.columns.tolist()}")
        # ---------------------------
    except FileNotFoundError:
        print(f"❌ ERROR: No se encontró el archivo '{RUTA_EXCEL}'. Asegúrate de que el nombre y la ubicación sean correctos.")
        return

    # Renombramos las columnas del DataFrame de pandas para que sea más fácil trabajar
    df.rename(columns=MAPEO_COLUMNAS, inplace=True)

    # --- PASO 2: CONECTAR A LA BASE DE DATOS Y PREPARAR ---
    print(f"🔗 Conectando a la base de datos: {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtenemos todos los códigos de barras existentes para una verificación rápida
    cursor.execute("SELECT codigo_barras FROM Articulos WHERE codigo_barras IS NOT NULL")
    codigos_existentes = {row[0] for row in cursor.fetchall()}
    print(f"✅ Se encontraron {len(codigos_existentes)} códigos de barras existentes en la base de datos.")

    # --- PASO 3: PROCESAR E INSERTAR ARTÍCULOS ---
    articulos_importados = 0
    articulos_omitidos = 0

    print("\n🚀 Iniciando la importación de artículos...")
    # Iteramos sobre cada fila del archivo Excel
    for index, row in df.iterrows():
        codigo_barras = str(row['codigo_barras']).strip() if pd.notna(row['codigo_barras']) else None

        # Condición: Si no hay código de barras o si ya existe, lo saltamos
        if not codigo_barras or codigo_barras in codigos_existentes:
            articulos_omitidos += 1
            continue

        # --- Manejo inteligente de Marcas ---
        marca_nombre = str(row['marca_nombre']).strip().upper() if pd.notna(row['marca_nombre']) else "SIN MARCA"
        marca_id = None
        
        # Buscamos si la marca ya existe
        cursor.execute("SELECT id FROM Marcas WHERE UPPER(nombre) = ?", (marca_nombre,))
        resultado = cursor.fetchone()
        
        if resultado:
            marca_id = resultado[0]
        else:
            # Si la marca no existe, la creamos
            try:
                cursor.execute("INSERT INTO Marcas (nombre) VALUES (?)", (marca_nombre,))
                marca_id = cursor.lastrowid
                print(f"  -> Nueva marca creada: '{marca_nombre}'")
            except sqlite3.Error as e:
                print(f"  -> Error al crear marca '{marca_nombre}': {e}")
                articulos_omitidos += 1
                continue

        # --- Preparación de datos del artículo ---
        nombre_articulo = str(row['nombre']).strip() if pd.notna(row['nombre']) else "Artículo sin nombre"
        precio_costo = float(row['precio_costo']) if pd.notna(row['precio_costo']) else 0.0

        # El resto de los campos quedan como NULL por defecto
        datos_articulo = {
            'codigo_barras': codigo_barras,
            'nombre': nombre_articulo,
            'marca_id': marca_id,
            'precio_costo': precio_costo,
            'stock': 0 # Asumimos stock inicial 0
        }

        # --- Inserción en la base de datos ---
        try:
            columnas = ', '.join(datos_articulo.keys())
            placeholders = ', '.join(['?'] * len(datos_articulo))
            valores = tuple(datos_articulo.values())
            
            cursor.execute(f"INSERT INTO Articulos ({columnas}) VALUES ({placeholders})", valores)
            articulos_importados += 1
            # Agregamos el nuevo código a nuestra lista para no volver a insertarlo si está duplicado en el mismo Excel
            codigos_existentes.add(codigo_barras)

        except sqlite3.Error as e:
            print(f"  -> ERROR al insertar artículo con código '{codigo_barras}': {e}")
            articulos_omitidos += 1

    # --- PASO 4: FINALIZAR Y MOSTRAR RESUMEN ---
    conn.commit()
    conn.close()

    print("\n--- RESUMEN DE LA IMPORTACIÓN ---")
    print(f"📄 Artículos procesados en el Excel: {len(df)}")
    print(f"✅ Artículos nuevos importados: {articulos_importados}")
    print(f"⏭️ Artículos omitidos (duplicados o con error): {articulos_omitidos}")
    print("-----------------------------------")
    print("🎉 ¡Proceso finalizado! 🎉")


if __name__ == '__main__':
    importar_articulos()