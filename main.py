# Archivo: main.py (VERSIÓN RESTAURADA)
from app.database import db_manager
from app.gui.login_window import LoginWindow
from app.gui.main_window import MainWindow

def main():
    db_manager.aplicar_migraciones()
    
    while True:
        login_app = LoginWindow()
        login_app.mainloop()
        
        usuario_logueado = login_app.usuario_logueado
        
        if usuario_logueado:
            main_app = MainWindow(usuario_logueado)
            main_app.mainloop()
            
            if not main_app.restart:
                break
        else:
            break

if __name__ == '__main__':
    main()