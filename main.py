from app.database import db_manager
from app.gui.login_window import LoginWindow
from app.gui.main_window import MainWindow

def main():
    # db_manager.aplicar_migraciones()
    
    while True:
        # 1. Muestra la ventana de login y espera a que se cierre
        login_app = LoginWindow()
        login_app.mainloop()
        
        # 2. Verifica si el login fue exitoso
        usuario_logueado = login_app.usuario_logueado
        
        if usuario_logueado:
            # 3. Si fue exitoso, abre la ventana principal
            main_app = MainWindow(usuario_logueado)
            main_app.mainloop()
            
            # 4. Si el usuario cerró sesión, el bucle reinicia. Si salió, se rompe.
            if not main_app.restart:
                break
        else:
            # Si el login no fue exitoso (el usuario cerró la ventana), termina el programa
            break

if __name__ == '__main__':
    main()