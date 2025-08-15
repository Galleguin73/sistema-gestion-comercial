# Archivo: app/gui/login_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from app.database import usuarios_db

class LoginWindow(tk.Tk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success

        self.title("Inicio de Sesión")
        self.geometry("350x200")
        self.resizable(False, False)

        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="Usuario:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.user_entry = ttk.Entry(main_frame)
        self.user_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(main_frame, text="Contraseña:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.pass_entry = ttk.Entry(main_frame, show="*")
        self.pass_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.pass_entry.bind("<Return>", self.intentar_login)

        login_button = ttk.Button(main_frame, text="Ingresar", command=self.intentar_login)
        login_button.grid(row=2, column=0, columnspan=2, pady=15, sticky="ew")

        self.user_entry.focus_set()

    def intentar_login(self, event=None):
        username = self.user_entry.get()
        password = self.pass_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Por favor, ingrese usuario y contraseña.")
            return

        usuario_data = usuarios_db.validar_usuario(username, password)

        if usuario_data:
            permisos = usuarios_db.obtener_permisos_usuario(usuario_data['id'])
            usuario_data['permisos'] = permisos
            self.destroy() # Cierra la ventana de login
            self.on_login_success(usuario_data) # Llama a la función que abre la ventana principal
        else:
            messagebox.showerror("Login Fallido", "Usuario o contraseña incorrectos.")