import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from app.database import config_db
from .rubros_abm import RubrosFrame
from .marcas_abm import MarcasFrame
from .medios_pago_abm import MediosPagoFrame
from .usuarios_abm import UsuariosFrame
from app.utils import backup_manager

class ConfiguracionImpresionFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        
        main_frame = ttk.Frame(self, style="Content.TFrame")
        main_frame.pack(padx=20, pady=20, fill='x')
        
        data_frame = ttk.LabelFrame(main_frame, text="Configuración de Impresión", style="TLabelframe")
        data_frame.pack(fill='x')
        data_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(data_frame, text="Formato de Ticket/Comprobante:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.tipo_impresion_combo = ttk.Combobox(data_frame, values=["Ticket 80mm", "Ticket 58mm", "Hoja A4"], state="readonly")
        self.tipo_impresion_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        btn_guardar = ttk.Button(main_frame, text="Guardar Configuración de Impresión", 
                                 command=self.guardar_configuracion, style="Action.TButton")
        btn_guardar.pack(pady=10, anchor="e")

        self.cargar_datos()

    def cargar_datos(self):
        config = config_db.obtener_configuracion()
        if config:
            self.tipo_impresion_combo.set(config.get("tipo_impresion", "Ticket 80mm"))

    def guardar_configuracion(self):
        datos = {
            "tipo_impresion": self.tipo_impresion_combo.get()
        }
        resultado = config_db.guardar_configuracion_impresion(datos)
        if "guardada" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
        else:
            messagebox.showerror("Error", resultado, parent=self)

class BackupFrame(ttk.Frame):
    def __init__(self, parent, style, app_instance):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.app = app_instance

        main_frame = ttk.Frame(self, style="Content.TFrame")
        main_frame.pack(padx=20, pady=20, fill='x')

        data_frame = ttk.LabelFrame(main_frame, text="Copias de Seguridad", style="TLabelframe")
        data_frame.pack(fill='x')

        info_text = ("Realizar copias de seguridad de forma regular es crucial para proteger la información de su negocio. "
                     "Guarde sus copias en un lugar seguro (ej: un pendrive o en la nube).")
        ttk.Label(data_frame, text=info_text, wraplength=500, justify="left").pack(padx=10, pady=10)

        btn_crear = ttk.Button(data_frame, text="1. Crear Copia de Seguridad Ahora", 
                               command=backup_manager.crear_copia_seguridad, style="Action.TButton")
        btn_crear.pack(pady=(10, 5), padx=10, fill='x')
        
        ttk.Separator(data_frame, orient='horizontal').pack(fill='x', pady=15, padx=10)

        warning_text = ("¡ATENCIÓN! Restaurar una copia de seguridad reemplazará TODOS los datos actuales. "
                        "Esta acción es irreversible. Úsela únicamente si está seguro.")
        ttk.Label(data_frame, text=warning_text, wraplength=500, justify="left", foreground="red").pack(padx=10, pady=5)
        
        btn_restaurar = ttk.Button(data_frame, text="2. Restaurar desde una Copia de Seguridad", 
                                   command=lambda: backup_manager.restaurar_copia_seguridad(self.app), 
                                   style="Action.TButton")
        btn_restaurar.pack(pady=(5, 10), padx=10, fill='x')

class ConfiguracionFrame(ttk.Frame):
    def __init__(self, parent, style, main_window):
        super().__init__(parent)
        self.style = style

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- PESTAÑA 1: Datos de la Empresa ---
        self.empresa_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.empresa_tab, text='Datos de la Empresa')
        self.crear_widgets_empresa()
        
        # --- PESTAÑA 2: Rubros y Subrubros (con contenedor) ---
        rubros_container = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(rubros_container, text='Rubros y Subrubros')
        # El frame del ABM se empaqueta dentro del contenedor para que no se expanda
        rubros_frame = RubrosFrame(rubros_container, self.style)
        rubros_frame.pack(padx=20, pady=20, anchor='n')

        # --- PESTAÑA 3: Marcas (con contenedor) ---
        marcas_container = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(marcas_container, text='Marcas')
        marcas_frame = MarcasFrame(marcas_container, self.style)
        marcas_frame.pack(padx=20, pady=20, anchor='n')

        # --- PESTAÑA 4: Medios de Pago (con contenedor) ---
        medios_pago_container = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(medios_pago_container, text='Medios de Pago')
        medios_pago_frame = MediosPagoFrame(medios_pago_container, self.style)
        medios_pago_frame.pack(padx=20, pady=20, anchor='n')

        # --- PESTAÑA 5: Impresión ---
        self.impresion_tab = ConfiguracionImpresionFrame(self.notebook, self.style)
        self.notebook.add(self.impresion_tab, text='Impresión')
        
        # --- PESTAÑA 6: Usuarios ---
        self.usuarios_tab = UsuariosFrame(self.notebook, self.style)
        self.notebook.add(self.usuarios_tab, text='Usuarios y Permisos')
        
        # --- PESTAÑA 7: Copias de Seguridad ---
        self.backup_tab = BackupFrame(self.notebook, self.style, main_window)
        self.notebook.add(self.backup_tab, text='Copias de Seguridad')

    def crear_widgets_empresa(self):
        data_frame = ttk.LabelFrame(self.empresa_tab, text="Datos de la Empresa", style="TLabelframe")
        data_frame.pack(padx=20, pady=20, fill='x')
        data_frame.grid_columnconfigure(1, weight=1)
        
        self.entries = {}
        campos = [
            ("Razón Social:", 'razon_social'), ("Nombre Fantasía:", 'nombre_fantasia'),
            ("CUIT:", 'cuit'), ("Condición IVA:", 'condicion_iva', ["Monotributo", "Responsable Inscripto"]),
            ("Ingresos Brutos:", 'iibb'), ("Domicilio:", 'domicilio'),
            ("Ciudad:", 'ciudad'), ("Provincia:", 'provincia')
        ]
        for i, item in enumerate(campos):
            texto, clave, *valores = item
            label = ttk.Label(data_frame, text=texto)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            if valores:
                entry = ttk.Combobox(data_frame, values=valores[0])
            else:
                entry = ttk.Entry(data_frame)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            self.entries[clave] = entry
        
        ttk.Label(data_frame, text="Logo:").grid(row=len(campos), column=0, padx=10, pady=5, sticky="w")
        self.logo_path_var = tk.StringVar()
        logo_entry = ttk.Entry(data_frame, textvariable=self.logo_path_var, state="readonly")
        logo_entry.grid(row=len(campos), column=1, padx=10, pady=5, sticky="ew")
        self.entries['logo_path'] = self.logo_path_var
        
        logo_btn = ttk.Button(data_frame, text="Seleccionar Archivo...", command=self.seleccionar_logo)
        logo_btn.grid(row=len(campos), column=2, padx=10, pady=5)
        
        save_btn = ttk.Button(self.empresa_tab, text="Guardar Configuración", command=self.guardar, style="Action.TButton")
        save_btn.pack(padx=20, pady=10, fill='x')

        self.cargar_datos()

    def seleccionar_logo(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar Logo",
            filetypes=(("Archivos de imagen", "*.png *.jpg *.jpeg *.gif"), ("Todos los archivos", "*.*"))
        )
        if filepath:
            self.logo_path_var.set(filepath)

    def cargar_datos(self):
        config = config_db.obtener_configuracion()
        if config:
            for clave, entry in self.entries.items():
                valor = config.get(clave, "")
                if isinstance(entry, tk.StringVar):
                    entry.set(valor or "")
                else:
                    entry.delete(0, tk.END)
                    entry.insert(0, valor or "")

    def guardar(self):
        datos = {}
        for clave, entry in self.entries.items():
            if isinstance(entry, tk.StringVar):
                datos[clave] = entry.get()
            else:
                datos[clave] = entry.get()
        resultado = config_db.guardar_configuracion(datos)
        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado)
        else:
            messagebox.showerror("Error", resultado)