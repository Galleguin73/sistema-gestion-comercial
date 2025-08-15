import tkinter as tk
from tkinter import ttk, font, messagebox
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
from app.database import config_db, caja_db
from .clientes_abm import ClientesFrame
from .proveedores_abm import ProveedoresFrame
from .articulos_abm import ArticulosFrame
from .configuracion import ConfiguracionFrame
from .compras import ComprasFrame
from .caja import CajaFrame
from .pos_frame import POSFrame
from .reportes_frame import ReportesFrame
from .dashboard_frame import DashboardFrame

class MainWindow(ThemedTk):
    def __init__(self, usuario_logueado):
        super().__init__()
        self.usuario_logueado = usuario_logueado
        self.caja_actual_id = None
        self.restart = False # Atributo para controlar el reinicio

        self.title("Sistema de Gestión Comercial")
        self.state('zoomed') 
        
        # --- NUEVO: Controlar el cierre de la ventana ---
        self.protocol("WM_DELETE_WINDOW", self.salir_aplicacion)
        
        self.set_theme("clam")
        self.style = ttk.Style()
        
        # ... (El resto de la configuración de estilos no cambia) ...
        self.COLOR_SIDEBAR = "#2c3e50"
        self.COLOR_CONTENT = "#ecf0f1"
        self.COLOR_BTN_NORMAL = "#3498db"
        self.COLOR_BTN_HOVER = "#5dade2"
        self.COLOR_BTN_TEXT = "white"
        self.COLOR_TEXT_DARK = "black"
        self.configure(background=self.COLOR_CONTENT)
        self.style.configure("TFrame", background=self.COLOR_CONTENT)
        self.style.configure("Content.TFrame", background=self.COLOR_CONTENT)
        self.style.configure("Sidebar.TFrame", background=self.COLOR_SIDEBAR)
        self.style.map("Nav.TButton", background=[('active', self.COLOR_BTN_HOVER), ('!active', self.COLOR_BTN_NORMAL)], foreground=[('active', self.COLOR_BTN_TEXT), ('!active', self.COLOR_BTN_TEXT)])
        self.style.configure("Nav.TButton", font=("Helvetica", 10, "bold"), padding=(10, 10), borderwidth=0, relief="flat", anchor="w")
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
        self.mostrar_dashboard()

    def verificar_caja_al_inicio(self):
        caja_abierta = caja_db.obtener_estado_caja()
        if caja_abierta:
            self.caja_actual_id = caja_abierta[0]
        else:
            self.caja_actual_id = None

    def crear_botones_navegacion(self):
        app_title = ttk.Label(self.nav_frame, text="Gestión Comercial", 
                              font=("Helvetica", 16, "bold"),
                              background=self.COLOR_SIDEBAR, foreground="white",
                              anchor="center")
        app_title.pack(pady=20, padx=10, fill='x')

        modulos = {
            "Inicio": self.mostrar_dashboard, "Caja": self.mostrar_frame_caja,
            "POS / Venta": self.mostrar_frame_pos, "Artículos": self.mostrar_frame_articulos,
            "Clientes": self.mostrar_frame_clientes, "Proveedores": self.mostrar_frame_proveedores,
            "Compras": self.mostrar_frame_compras, "Reportes": self.mostrar_frame_reportes,
            "Configuración": self.mostrar_frame_configuracion
        }
        
        # Frame para los botones de módulos, para que los de sesión queden abajo
        modulos_frame = ttk.Frame(self.nav_frame, style="Sidebar.TFrame")
        modulos_frame.pack(fill='x', expand=True)

        for texto, comando in modulos.items():
            es_admin = self.usuario_logueado['rol'] == 'admin'
            tiene_permiso = self.usuario_logueado['permisos'].get(texto, False)

            if texto == "Inicio" or es_admin or tiene_permiso:
                btn = ttk.Button(modulos_frame, text=texto, command=comando, style="Nav.TButton")
                btn.pack(pady=2, padx=20, fill='x')
        
        # --- NUEVO: Frame para botones de sesión y logo ---
        sesion_frame = ttk.Frame(self.nav_frame, style="Sidebar.TFrame")
        sesion_frame.pack(side="bottom", fill='x', pady=10)

        ttk.Separator(sesion_frame).pack(fill='x', padx=20, pady=10)

        # Botón para Cerrar Sesión
        btn_logout = ttk.Button(sesion_frame, text="Cerrar Sesión", command=self.cerrar_sesion, style="Nav.TButton")
        btn_logout.pack(pady=2, padx=20, fill='x')

        # Botón para Salir
        btn_exit = ttk.Button(sesion_frame, text="Salir", command=self.salir_aplicacion, style="Nav.TButton")
        btn_exit.pack(pady=2, padx=20, fill='x')

        logo_frame = ttk.Frame(sesion_frame, style="Sidebar.TFrame")
        logo_frame.pack(side="bottom", fill="x", pady=20)
        
        config = config_db.obtener_configuracion()
        if config and config.get("logo_path"):
            # ... (código de logo sin cambios)
            pass

    # --- NUEVAS FUNCIONES PARA CERRAR SESIÓN Y SALIR ---
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

    # ... (El resto de funciones mostrar_frame_... no cambian) ...
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

    def obtener_frame_articulos(self):
        return ArticulosFrame(self.content_frame, self.style)
        
    def mostrar_frame_configuracion(self):
        self.limpiar_content_frame()
        config_frame = ConfiguracionFrame(self.content_frame, self.style)
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