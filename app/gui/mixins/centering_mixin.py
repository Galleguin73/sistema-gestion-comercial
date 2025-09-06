import tkinter as tk

class CenteringMixin:
    def center_window(self):
        """
        Centra la ventana (Toplevel o Tk) en la pantalla.
        """
        # Asegura que el tamaño de la ventana esté actualizado
        self.update_idletasks()

        # Obtiene el tamaño de la ventana
        width = self.winfo_width()
        height = self.winfo_height()

        # Obtiene el tamaño de la pantalla
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calcula la posición x, y para centrar la ventana
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # Establece la nueva geometría de la ventana
        self.geometry(f'{width}x{height}+{x}+{y}')