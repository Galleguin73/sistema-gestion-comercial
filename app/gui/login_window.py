# Archivo: app/gui/login_window.py (VERSIÓN RESTAURADA)
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from app.database import usuarios_db, config_db

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw() 
        self.title("Inicio de Sesión")
        
        self.usuario_logueado = None

        window_width = 380
        window_height = 520
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        self.resizable(False, False)
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)

        self.logo_image = None
        logo_label = self._crear_logo_label(main_frame)
        if logo_label:
            logo_label.pack(pady=(10, 30))

        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="x", pady=10)

        ttk.Label(form_frame, text="Usuario:", font=("Helvetica", 11)).pack(anchor="w")
        self.user_entry = ttk.Entry(form_frame, font=("Helvetica", 11))
        self.user_entry.pack(fill="x", pady=5)

        ttk.Label(form_frame, text="Contraseña:", font=("Helvetica", 11)).pack(anchor="w", pady=(10, 0))
        self.pass_entry = ttk.Entry(form_frame, show="*", font=("Helvetica", 11))
        self.pass_entry.pack(fill="x", pady=5)
        
        self.user_entry.bind("<Return>", lambda event: self.pass_entry.focus())
        self.pass_entry.bind("<Return>", self.intentar_login)

        s = ttk.Style()
        s.configure('Action.TButton', font=('Helvetica', 10, 'bold'))
        login_button = ttk.Button(main_frame, text="Ingresar", command=self.intentar_login, style="Action.TButton")
        login_button.pack(fill="x", pady=20, ipady=8)

        self.user_entry.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.deiconify()

    def _crear_logo_label(self, parent):
        config = config_db.obtener_configuracion()
        if config and config.get("logo_path"):
            try:
                path = config["logo_path"]
                img = Image.open(path)
                ancho_logo = 180
                ancho_original, alto_original = img.size
                ratio = ancho_original / ancho_logo
                nuevo_alto = int(alto_original / ratio)
                img_resized = img.resize((ancho_logo, nuevo_alto), Image.Resampling.LANCZOS)

                self.logo_image = ImageTk.PhotoImage(img_resized)
                return ttk.Label(parent, image=self.logo_image)
            except Exception as e:
                print(f"No se pudo cargar el logo en el login: {e}")
        return None

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
            self.usuario_logueado = usuario_data
            self.destroy()
        else:
            messagebox.showerror("Login Fallido", "Usuario o contraseña incorrectos.")

    def on_closing(self):
        self.usuario_logueado = None
        self.destroy()