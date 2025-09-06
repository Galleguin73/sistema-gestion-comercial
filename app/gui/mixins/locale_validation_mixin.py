# Archivo: app/gui/mixins/locale_validation_mixin.py
import tkinter as tk
from tkinter import messagebox

class LocaleValidationMixin:
    """
    Mixin para manejar la validación y el formato de números con separadores
    de miles (.) y decimales (,).
    """

    def _setup_numeric_validation(self, entry_widget):
        """Aplica los bindings para formatear el número al perder el foco."""
        entry_widget.bind("<FocusOut>", self._format_on_focus_out)
        entry_widget.bind("<KeyRelease>", self._on_key_release)

    def _on_key_release(self, event):
        """Permite solo la entrada de dígitos, comas y puntos."""
        widget = event.widget
        texto = widget.get()
        
        # Permite solo un separador decimal (coma)
        if texto.count(',') > 1:
            posicion_cursor = widget.index(tk.INSERT)
            partes = texto.split(',')
            texto_final = partes[0] + ',' + ''.join(partes[1:])
            widget.delete(0, tk.END)
            widget.insert(0, texto_final)
            widget.icursor(posicion_cursor - 1)
            return
        
        # Elimina caracteres no permitidos
        texto_limpio = ''.join(c for c in texto if c in '0123456789.,')
        if texto != texto_limpio:
            posicion_cursor = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto_limpio)
            widget.icursor(posicion_cursor - (len(texto) - len(texto_limpio)))

    def _format_on_focus_out(self, event):
        """Formatea el número cuando el usuario sale del campo."""
        widget = event.widget
        try:
            valor_float = self._parse_local_number(widget.get())
            if valor_float is not None:
                widget.delete(0, tk.END)
                widget.insert(0, self._format_local_number(valor_float))
        except (ValueError, TypeError):
            pass 

    @staticmethod
    def _parse_local_number(s):
        """Convierte un string como '1.250,75' a un float 1250.75."""
        if not isinstance(s, str) or not s:
            return None
        try:
            return float(s.replace('.', '').replace(',', '.'))
        except ValueError:
            return None

    @staticmethod
    def _format_local_number(f):
        """Convierte un float 1250.75 a un string '1.250,75'."""
        if f is None:
            return ""
        return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def get_validated_float(self, entry_widget, campo_nombre):
        """Obtiene de forma segura un float desde un entry validado."""
        valor_str = entry_widget.get()
        if not valor_str.strip():
            return 0.0
        valor_float = self._parse_local_number(valor_str)
        if valor_float is None:
            messagebox.showerror("Error de Validación", f"El valor ingresado en '{campo_nombre}' no es un número válido.", parent=self)
            raise ValueError(f"Validación fallida para el campo {campo_nombre}")
        return valor_float