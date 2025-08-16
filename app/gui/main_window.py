import tkinter as tk
from tkinter import ttk, font, messagebox
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
from app.database import config_db, caja_db
from .clientes_abm import ClientesFrame
from .proveedores_abm import ProveedoresFrame
from .articulos_abm import ArticulosFrame
from .empaquetado_frame import EmpaquetadoFrame
from .configuracion import ConfiguracionFrame
from .compras import ComprasFrame
from .caja import CajaFrame
from .pos_frame import POSFrame
from .reportes_frame import ReportesFrame
from .dashboard_frame import DashboardFrame
from .cuentas_corrientes_frame import CuentasCorrientesFrame

class MainWindow(ThemedTk):
    def __init__(self, usuario_logueado):
        super().__init__()
        self.usuario_logueado = usuario_logueado
        self.caja_actual_id = None
        self.restart = False
        
        self.active_button = None
        self.nav_buttons = {}

        self.title("Sistema de Gestión Comercial")
        self.state('zoomed') 
        
        self.protocol("WM_DELETE_WINDOW", self.salir_aplicacion)
        
        self.set_theme("clam")
        self.style = ttk.Style()
        
        self.COLOR_SIDEBAR = "#2c3e50"
        self.COLOR_CONTENT = "#ecf0f1"
        self.COLOR_BTN_NORMAL = "#3498db"
        self.COLOR_BTN_HOVER = "#5dade2"
        self.COLOR_BTN_ACTIVE = "#2ecc71"
        self.COLOR_BTN_TEXT = "white"
        self.COLOR_TEXT_DARK = "black"
        
        self.configure(background=self.COLOR_CONTENT)
        self.style.configure("TFrame", background=self.COLOR_CONTENT)
        self.style.configure("Content.TFrame", background=self.COLOR_CONTENT)
        self.style.configure("Sidebar.TFrame", background=self.COLOR_SIDEBAR)
        
        self.style.map("Nav.TButton", 
                       background=[('active', self.COLOR_BTN_HOVER), ('!active', self.COLOR_BTN_NORMAL)], 
                       foreground=[('!disabled', self.COLOR_BTN_TEXT)])
        
        # --- LÍNEA MODIFICADA ---
        self.style.configure("Nav.TButton", font=("Helvetica", 10, "bold"), padding=(10, 6), borderwidth=0, relief="flat", anchor="w")

        # --- LÍNEA MODIFICADA ---
        self.style.configure("ActiveNav.TButton", font=("Helvetica", 10, "bold"), padding=(10, 6), borderwidth=0, relief="flat", anchor="w",
                             background=self.COLOR_BTN_ACTIVE, foreground=self.COLOR_BTN_TEXT)

        self.style.configure("TLabelframe", font=("Helvetica", 11, "bold"), background=self.COLOR_CONTENT, borderwidth=1, relief="groove")
        self.style.configure("TLabelframe.Label", background=self.COLOR_CONTENT, foreground=self.COLOR_TEXT_DARK)
        self.style.configure("TLabel", background=self.COLOR_CONTENT, foreground=self.COLOR_TEXT_DARK, font=("Helvetica", 9))
        self.style.configure("Action.TButton", font=("Helvetica", 10, "bold"), padding=5)
        self.style.configure("Treeview", background="white", fieldbackground="white", foreground=self.COLOR_TEXT_DARK)
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        self.style.map('Treeview', background=[('selected', self.COLOR_BTN_NORMAL)], foreground=[('selected', self.COLOR_BTN_TEXT)])
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.nav_frame = ttk.Frame(self, width=220, style="Sidebar.TFrame")
        self.nav_frame.grid(row=0, column=0, sticky="nsw")
        self.nav_frame.pack_propagate(False)

        self.content_frame = ttk.Frame(self, style="Content.TFrame")
        self.content_frame.grid(row=0, column=1, sticky="nsew")

        self.verificar_caja_al_inicio()
        self.crear_botones_navegacion()
        
        inicio_btn = self.nav_buttons.get("Inicio")
        if inicio_btn:
             self.on_nav_button_click(inicio_btn, self.mostrar_dashboard)
        else:
             self.mostrar_dashboard()

    def verificar_caja_al_inicio(self):
        caja_abierta = caja_db.obtener_estado_caja()
        if caja_abierta:
            self.caja_actual_id = caja_abierta[0]
        else:
            self.caja_actual_id = None
            
    def on_nav_button_click(self, clicked_button, command_to_run):
        if self.active_button:
            self.active_button.configure(style="Nav.TButton")

        clicked_button.configure(style="ActiveNav.TButton")
        self.active_button = clicked_button
        command_to_run()

    def crear_botones_navegacion(self):
        app_title = ttk.Label(self.nav_frame, text="Gestión Comercial", 
                              font=("Helvetica", 16, "bold"),
                              background=self.COLOR_SIDEBAR, foreground="white",
                              anchor="center")
        app_title.pack(side="top", pady=20, padx=10, fill='x')

        sesion_frame = ttk.Frame(self.nav_frame, style="Sidebar.TFrame")
        sesion_frame.pack(side="bottom", fill='x', pady=10)

        logo_frame = ttk.Frame(self.nav_frame, style="Sidebar.TFrame")
        logo_frame.pack(side="bottom", fill="x", pady=20)

        modulos_frame = ttk.Frame(self.nav_frame, style="Sidebar.TFrame")
        modulos_frame.pack(side="top", fill='x')

        modulos = {
            "Inicio": self.mostrar_dashboard,
            "Caja": self.mostrar_frame_caja,
            "POS / Venta": self.mostrar_frame_pos,
            "Artículos": self.mostrar_frame_articulos,
            "Empaquetado Propio": self.mostrar_frame_empaquetado,
            "Clientes": self.mostrar_frame_clientes,
            "Proveedores": self.mostrar_frame_proveedores,
            "Compras": self.mostrar_frame_compras,
            "Cuentas Corrientes": self.mostrar_frame_cuentas_corrientes,
            "Reportes": self.mostrar_frame_reportes,
            "Configuración": self.mostrar_frame_configuracion
        }
        
        for texto, comando in modulos.items():
            es_admin = self.usuario_logueado['rol'] == 'admin'
            
            permiso_real = texto
            if texto == "Empaquetado Propio":
                permiso_real = "Empaquetado"
            
            tiene_permiso = permiso_real in self.usuario_logueado['permisos']

            if texto in ("Inicio", "Configuración") or es_admin or tiene_permiso:
                btn = ttk.Button(modulos_frame, text=texto, style="Nav.TButton")
                btn.configure(command=lambda b=btn, cmd=comando: self.on_nav_button_click(b, cmd))
                btn.pack(pady=2, padx=20, fill='x')
                self.nav_buttons[texto] = btn

        ttk.Separator(sesion_frame).pack(fill='x', padx=20, pady=10)
        btn_logout = ttk.Button(sesion_frame, text="Cerrar Sesión", command=self.cerrar_sesion, style="Nav.TButton")
        btn_logout.pack(pady=2, padx=20, fill='x')
        btn_exit = ttk.Button(sesion_frame, text="Salir", command=self.salir_aplicacion, style="Nav.TButton")
        btn_exit.pack(pady=2, padx=20, fill='x')

        config = config_db.obtener_configuracion()
        if config and config.get("logo_path"):
            try:
                path = config["logo_path"]
                img = Image.open(path)
                
                ancho_logo = 160
                ancho_original, alto_original = img.size
                ratio = ancho_original / ancho_logo
                nuevo_alto = int(alto_original / ratio)
                img_resized = img.resize((ancho_logo, nuevo_alto), Image.Resampling.LANCZOS)

                self.logo_image = ImageTk.PhotoImage(img_resized)
                logo_label = ttk.Label(logo_frame, image=self.logo_image, background=self.COLOR_SIDEBAR)
                logo_label.pack()
            except Exception as e:
                print(f"No se pudo cargar el logo: {e}")

    def cerrar_sesion(self):
        self.restart = True
        self.destroy()

    def salir_aplicacion(self):
        self.restart = False
        self.destroy()

    def limpiar_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def mostrar_dashboard(self):
        self.limpiar_content_frame()
        dashboard = DashboardFrame(self.content_frame, self.style)
        dashboard.pack(fill='both', expand=True, padx=10, pady=10)

    def mostrar_frame_clientes(self):
        self.limpiar_content_frame()
        clientes_frame = ClientesFrame(self.content_frame, self.style)
        clientes_frame.pack(fill='both', expand=True, padx=10, pady=10)

    def mostrar_frame_proveedores(self):
        self.limpiar_content_frame()
        proveedores_frame = ProveedoresFrame(self.content_frame, self.style)
        proveedores_frame.pack(fill='both', expand=True, padx=10, pady=10)

    def mostrar_frame_articulos(self, oculto=False):
        self.limpiar_content_frame()
        articulos_frame = ArticulosFrame(self.content_frame, self.style)
        if not oculto:
            articulos_frame.pack(fill='both', expand=True, padx=10, pady=10)
        return articulos_frame

    def mostrar_frame_empaquetado(self):
        self.limpiar_content_frame()
        empaquetado_frame = EmpaquetadoFrame(self.content_frame, self.style)
        empaquetado_frame.pack(fill='both', expand=True, padx=10, pady=10)

    def obtener_frame_articulos(self):
        return ArticulosFrame(self.content_frame, self.style)
        
    def mostrar_frame_configuracion(self):
        self.limpiar_content_frame()
        config_frame = ConfiguracionFrame(self.content_frame, self.style, self)
        config_frame.pack(fill='both', expand=True, padx=10, pady=10)

    def mostrar_frame_compras(self):
        self.limpiar_content_frame()
        compras_frame = ComprasFrame(self.content_frame, self.style, self)
        compras_frame.pack(fill='both', expand=True, padx=10, pady=10)

    def mostrar_frame_caja(self):
        self.limpiar_content_frame()
        caja_frame = CajaFrame(self.content_frame, self.style, self.actualizar_estado_caja)
        caja_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    def mostrar_frame_pos(self):
        if not self.caja_actual_id:
            messagebox.showerror("Caja Cerrada", "Debe abrir la caja en el módulo 'Caja' antes de poder registrar una venta.")
            return
            
        self.limpiar_content_frame()
        pos_frame = POSFrame(self.content_frame, self.style, self, self.caja_actual_id)
        pos_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
    def mostrar_frame_reportes(self):
        self.limpiar_content_frame()
        reportes_frame = ReportesFrame(self.content_frame, self.style)
        reportes_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
    def actualizar_estado_caja(self, caja_id):
        self.caja_actual_id = caja_id
    
    def mostrar_frame_cuentas_corrientes(self):
        self.limpiar_content_frame()
        ctas_ctes_frame = CuentasCorrientesFrame(self.content_frame, self.style)
        ctas_ctes_frame.pack(fill='both', expand=True, padx=10, pady=10)