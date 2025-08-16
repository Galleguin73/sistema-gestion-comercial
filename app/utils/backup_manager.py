# Archivo: app/utils/backup_manager.py
import os
import shutil
from tkinter import filedialog, messagebox
from datetime import datetime

# Obtenemos la ruta del archivo de la base de datos de forma dinámica
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DB_DIR, 'gestion.db')

def crear_copia_seguridad():
    """
    Abre un diálogo para que el usuario elija dónde guardar una copia
    del archivo de la base de datos.
    """
    if not os.path.exists(DB_PATH):
        messagebox.showerror("Error", "No se encontró el archivo de la base de datos.")
        return

    # Generar un nombre de archivo por defecto con la fecha y hora
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_archivo_sugerido = f"backup_gestion_{timestamp}.db"

    # Abrir el diálogo "Guardar como"
    ruta_destino = filedialog.asksaveasfilename(
        title="Guardar Copia de Seguridad como...",
        initialfile=nombre_archivo_sugerido,
        defaultextension=".db",
        filetypes=[("Archivos de Base de Datos", "*.db"), ("Todos los archivos", "*.*")]
    )

    if ruta_destino:
        try:
            # shutil.copy2 preserva los metadatos del archivo
            shutil.copy2(DB_PATH, ruta_destino)
            messagebox.showinfo("Éxito", f"Copia de seguridad creada exitosamente en:\n{ruta_destino}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la copia de seguridad.\nError: {e}")

def restaurar_copia_seguridad(app):
    """
    Abre un diálogo para que el usuario elija un archivo de backup
    para restaurar la base de datos.
    """
    ruta_backup = filedialog.askopenfilename(
        title="Seleccionar Copia de Seguridad para Restaurar",
        filetypes=[("Archivos de Base de Datos", "*.db"), ("Todos los archivos", "*.*")]
    )

    if ruta_backup:
        confirmacion = messagebox.askyesno(
            "Confirmación Crítica",
            "¿Está ABSOLUTAMENTE SEGURO de que desea restaurar la base de datos?\n\n"
            "ESTA ACCIÓN SOBREESCRIBIRÁ TODOS SUS DATOS ACTUALES.\n\n"
            "Esta operación no se puede deshacer.",
            icon='warning'
        )
        
        if confirmacion:
            try:
                # La aplicación debe cerrarse para liberar el archivo de la base de datos
                app.destroy() 
                
                # Realizar la restauración
                shutil.copy2(ruta_backup, DB_PATH)
                
                # Usamos un messagebox de bajo nivel porque la app principal ya no existe
                tk.Tk().withdraw() # Oculta la ventana raíz extra de Tk
                messagebox.showinfo("Restauración Completa", 
                                    "La base de datos ha sido restaurada exitosamente.\n"
                                    "Por favor, vuelva a abrir la aplicación.")

            except Exception as e:
                tk.Tk().withdraw()
                messagebox.showerror("Error", f"No se pudo restaurar la base de datos.\nError: {e}")