import tkinter as tk
from app.gui.main_window import MainWindow
from app import db_manager

def main():
    """
    Función principal para inicializar la base de datos y correr la aplicación.
    """
    # 1. Ejecutar las migraciones para asegurar que la BD esté actualizada
    db_manager.ejecutar_migraciones()
    
    # 2. Iniciar la aplicación de Tkinter
    app = MainWindow()
    app.mainloop()

if __name__ == '__main__':
    main()