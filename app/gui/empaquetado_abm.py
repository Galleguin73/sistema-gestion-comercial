import tkinter as tk
from tkinter import ttk, messagebox, TclError
from app.database import articulos_db
from .mixins.pricing_mixin import PricingLogicMixin

class VentanaArticuloEmpaquetado(tk.Toplevel, PricingLogicMixin):
    def __init__(self, parent, articulo_id=None):
        super().__init__(parent)
        PricingLogicMixin.__init__(self)
        self.parent = parent
        self.articulo_id = articulo_id
        
        titulo = "Editar Artículo de Empaquetado" if self.articulo_id else "Nuevo Artículo de Empaquetado"
        self.title(titulo)
        self.geometry("800x700")
        self.transient(parent)
        self.grab_set()

        self.componentes_seleccionados = []

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        form_frame = ttk.Labelframe(main_frame, text="Datos del Producto Final", padding="10")
        form_frame.pack(fill="x", expand=False, padx=5, pady=5)
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)

        comp_frame = ttk.Labelframe(main_frame, text="Componentes (Artículos del Rubro 'GRANEL')", padding="10")
        comp_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.entries = {}
        row_num = 0

        ttk.Label(form_frame, text="Detalle:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['nombre'] = ttk.Entry(form_frame)
        self.entries['nombre'].grid(row=row_num, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        row_num += 1

        ttk.Label(form_frame, text="Código:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['codigo_barras'] = ttk.Entry(form_frame)
        self.entries['codigo_barras'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Marca:").grid(row=row_num, column=2, padx=5, pady=5, sticky="w")
        self.combo_marca = ttk.Combobox(form_frame, state="readonly")
        self.combo_marca.grid(row=row_num, column=3, padx=5, pady=5, sticky="ew")
        self.cargar_marcas()
        row_num += 1
        
        ttk.Label(form_frame, text="Subrubro:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.combo_subrubro = ttk.Combobox(form_frame, state="readonly")
        self.combo_subrubro.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        self.cargar_subrubros()
        row_num += 1
        
        ttk.Separator(form_frame, orient='horizontal').grid(row=row_num, column=0, columnspan=4, sticky='ew', pady=10)
        row_num += 1

        ttk.Label(form_frame, text="Precio de Costo:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.costo_entry = ttk.Entry(form_frame)
        self.entries['precio_costo'] = self.costo_entry
        self.costo_entry.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="IVA (%):").grid(row=row_num, column=2, padx=5, pady=5, sticky="w")
        self.iva_combo = ttk.Combobox(form_frame, values=["0", "10.5", "21"], state="readonly")
        self.entries['iva'] = self.iva_combo
        self.iva_combo.grid(row=row_num, column=3, padx=5, pady=5, sticky="ew")
        row_num += 1

        ttk.Label(form_frame, text="Utilidad (%):").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.utilidad_entry = ttk.Entry(form_frame)
        self.entries['utilidad'] = self.utilidad_entry
        self.utilidad_entry.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(form_frame, text="Precio de Venta:").grid(row=row_num, column=2, padx=5, pady=5, sticky="w")
        self.venta_entry = ttk.Entry(form_frame)
        self.entries['precio_venta'] = self.venta_entry
        self.venta_entry.grid(row=row_num, column=3, padx=5, pady=5, sticky="ew")
        
        self.bind_pricing_events()

        # --- INTERFAZ DE COMPONENTES RESTAURADA ---
        selector_frame = ttk.Frame(comp_frame)
        selector_frame.pack(fill='x', pady=5)
        selector_frame.columnconfigure(1, weight=1)

        ttk.Label(selector_frame, text="Artículo Granel:").grid(row=0, column=0, padx=5)
        self.combo_granel = ttk.Combobox(selector_frame, state="readonly")
        self.combo_granel.grid(row=0, column=1, padx=5, sticky="ew")
        self.cargar_articulos_granel()

        ttk.Label(selector_frame, text="Cantidad:").grid(row=0, column=2, padx=5)
        self.cantidad_comp_entry = ttk.Entry(selector_frame, width=10)
        self.cantidad_comp_entry.grid(row=0, column=3, padx=5)

        btn_agregar_comp = ttk.Button(selector_frame, text="Agregar Componente", command=self.agregar_componente)
        btn_agregar_comp.grid(row=0, column=4, padx=10)

        tree_comp_frame = ttk.Frame(comp_frame)
        tree_comp_frame.pack(fill="both", expand=True, pady=10)
        
        self.tree_componentes = ttk.Treeview(tree_comp_frame, 
                                             columns=("id", "nombre", "cantidad"), 
                                             show="headings",
                                             displaycolumns=("nombre", "cantidad"))
        self.tree_componentes.heading("nombre", text="Componente")
        self.tree_componentes.heading("cantidad", text="Cantidad Usada")
        self.tree_componentes.pack(side="left", fill="both", expand=True)
        # --- FIN DE LA SECCIÓN RESTAURADA ---

        btn_guardar = ttk.Button(main_frame, text="Guardar Cambios", command=self.guardar, style="Action.TButton")
        btn_guardar.pack(pady=10, fill='x', padx=5)

        if self.articulo_id:
            self.cargar_datos_para_edicion()
        else:
            self.iva_combo.set("21")

    def cargar_marcas(self):
        self.marcas_data = articulos_db.obtener_marcas()
        self.combo_marca['values'] = [m[1] for m in self.marcas_data]

    def cargar_subrubros(self):
        self.subrubros_data = articulos_db.obtener_subrubros_empaquetado()
        self.combo_subrubro['values'] = [s[1] for s in self.subrubros_data]

    def cargar_articulos_granel(self):
        self.articulos_granel_data = articulos_db.obtener_articulos_granel()
        self.combo_granel['values'] = [item[1] for item in self.articulos_granel_data]

    def agregar_componente(self):
        nombre_seleccionado = self.combo_granel.get()
        if not nombre_seleccionado: return
        try:
            cantidad = float(self.cantidad_comp_entry.get())
            if cantidad <= 0: raise ValueError()
        except ValueError:
            messagebox.showwarning("Dato inválido", "La cantidad debe ser un número positivo.", parent=self)
            return

        id_seleccionado = next(item[0] for item in self.articulos_granel_data if item[1] == nombre_seleccionado)
        self.componentes_seleccionados.append((id_seleccionado, cantidad))
        self.tree_componentes.insert("", "end", values=(id_seleccionado, nombre_seleccionado, cantidad))
        self.combo_granel.set('')
        self.cantidad_comp_entry.delete(0, tk.END)

    def cargar_datos_para_edicion(self):
        columnas = articulos_db.get_articulo_column_names()
        datos_crudos = articulos_db.obtener_articulo_por_id(self.articulo_id)
        articulo = dict(zip(columnas, datos_crudos))

        for clave, entry in self.entries.items():
            valor = articulo.get(clave)
            if valor is not None:
                if isinstance(entry, ttk.Combobox):
                    pass
                else:
                    entry.delete(0, tk.END)
                    entry.insert(0, str(valor))
        
        self.entries['iva'].set(articulo.get('iva', '21'))
        
        marca_nombre = next((m[1] for m in self.marcas_data if m[0] == articulo.get('marca_id')), "")
        self.combo_marca.set(marca_nombre)

        subrubro_id = articulo.get('subrubro_id')
        subrubro_nombre = next((s[1] for s in self.subrubros_data if s[0] == subrubro_id), "")
        self.combo_subrubro.set(subrubro_nombre)

        componentes = articulos_db.obtener_composicion_articulo(self.articulo_id)
        for comp_id, comp_nombre, comp_cantidad in componentes:
            self.componentes_seleccionados.append((comp_id, comp_cantidad))
            self.tree_componentes.insert("", "end", values=(comp_id, comp_nombre, comp_cantidad))
    
    def guardar(self):
        datos_principales = {key: entry.get() for key, entry in self.entries.items() if entry.get()}
        
        subrubro_nombre = self.combo_subrubro.get()
        if not datos_principales.get("nombre") or not subrubro_nombre or not self.componentes_seleccionados:
            messagebox.showwarning("Datos incompletos", "Debe completar el nombre, seleccionar un subrubro y agregar al menos un componente.", parent=self)
            return

        marca_nombre = self.combo_marca.get()
        datos_principales['marca_id'] = next((mid for mid, nombre in self.marcas_data if nombre == marca_nombre), None)
        
        datos_principales['subrubro_id'] = next((sid for sid, nombre in self.subrubros_data if nombre == subrubro_nombre), None)
        
        if self.articulo_id:
            resultado = articulos_db.modificar_articulo_compuesto(self.articulo_id, datos_principales, self.componentes_seleccionados)
        else:
            datos_principales['stock'] = 0.0
            datos_principales['estado'] = 'Activo'
            resultado = articulos_db.agregar_articulo_compuesto(datos_principales, self.componentes_seleccionados)

        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self.parent)
            self.parent.actualizar_lista()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)


class ABMEmpaquetadoWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("ABM de Artículos de Empaquetado")
        self.geometry("900x600")
        self.transient(parent)
        self.grab_set()

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        columnas = ("id", "codigo", "marca", "nombre", "stock")
        self.tree = ttk.Treeview(tree_frame, columns=columnas, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("codigo", text="Código")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("stock", text="Stock")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nombre", width=350)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=1, sticky="ns")

        btn_agregar = ttk.Button(button_frame, text="Agregar", command=self.abrir_ventana_creacion, style="Action.TButton")
        btn_agregar.pack(pady=5, fill="x")

        btn_modificar = ttk.Button(button_frame, text="Modificar", command=self.abrir_ventana_modificacion, style="Action.TButton")
        btn_modificar.pack(pady=5, fill="x")

        btn_cerrar = ttk.Button(button_frame, text="Cerrar", command=self.destroy, style="Action.TButton")
        btn_cerrar.pack(pady=5, fill="x")

        self.actualizar_lista()

    def actualizar_lista(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        articulos = articulos_db.obtener_articulos_empaquetado()
        for art in articulos:
            self.tree.insert("", "end", values=art[:5])

    def abrir_ventana_creacion(self):
        VentanaArticuloEmpaquetado(self)

    def abrir_ventana_modificacion(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un artículo de la lista para modificar.")
            return
        
        articulo_id = self.tree.item(selected_item, "values")[0]
        VentanaArticuloEmpaquetado(self, articulo_id=articulo_id)