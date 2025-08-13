import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from app.database import config_db # Importación actualizada
from .rubros_abm import RubrosFrame
from .marcas_abm import MarcasFrame
from .medios_pago_abm import MediosPagoFrame

class ConfiguracionFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent)
        self.style = style

        # Crear un Notebook (pestañas)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestaña 1: Datos de la Empresa
        self.empresa_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.empresa_tab, text='Datos de la Empresa')
        self.crear_widgets_empresa()
        
        # Pestaña 2: Rubros y Subrubros
        self.rubros_tab = RubrosFrame(self.notebook, self.style)
        self.notebook.add(self.rubros_tab, text='Rubros y Subrubros')

        # Pestaña 3: Marcas
        self.marcas_tab = MarcasFrame(self.notebook, self.style)
        self.notebook.add(self.marcas_tab, text='Marcas')

        # Pestaña 4: Medios de Pago
        self.medios_pago_tab = MediosPagoFrame(self.notebook, self.style)
        self.notebook.add(self.medios_pago_tab, text='Medios de Pago')

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
        config = config_db.obtener_configuracion() # Referencia actualizada
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
        resultado = config_db.guardar_configuracion(datos) # Referencia actualizada
        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado)
        else:
            messagebox.showerror("Error", resultado)