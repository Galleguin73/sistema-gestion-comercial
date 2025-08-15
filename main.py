from app.gui.main_window import MainWindow
from app.gui.login_window import LoginWindow
from app import db_manager

def main():
    """Función principal que controla el flujo de la aplicación."""
    # Ejecutar migraciones al inicio, solo una vez.
    db_manager.ejecutar_migraciones()
    
    while True:
        usuario_logueado = None
        
        # Función que se pasará a la ventana de login para recibir los datos del usuario
        def on_login_success(usuario_data):
            nonlocal usuario_logueado
            usuario_logueado = usuario_data

        # Iniciar con la ventana de login
        login_app = LoginWindow(on_login_success=on_login_success)
        login_app.mainloop()

        # Si el usuario cierra la ventana de login sin ingresar, salimos del bucle
        if not usuario_logueado:
            break

        # Si el login fue exitoso, abrimos la ventana principal
        app = MainWindow(usuario_logueado)
        app.mainloop()
        
        # Cuando MainWindow se cierra, verificamos si fue para reiniciar o para salir
        if not hasattr(app, 'restart') or not app.restart:
            break # Si no hay orden de reiniciar, salimos del bucle y terminamos

if __name__ == "__main__":
    main()