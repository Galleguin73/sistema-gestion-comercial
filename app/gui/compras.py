import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import compras_db, articulos_db, proveedores_db
from .articulos_abm import VentanaArticulo
from tkcalendar import DateEntry

class VentanaBuscarArticulo(tk.Toplevel):
    def __init__(self, parent, callback, main_window):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.main_window = main_window
        self.title("Buscar o Agregar Artículo")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()

        search_frame = ttk.Frame(self, padding="10")
        search_frame.pack(fill='x')
        ttk.Label(search_frame, text="Buscar por Código o Nombre:").pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.buscar_articulos)
        self.search_entry = ttk.Entry(search_frame, width=40, textvariable=self.search_var)
        self.search_entry.pack(side='left', fill='x', expand=True)
        self.search_entry.focus_set()

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        columnas = ("ID", "Codigo", "Marca", "Nombre", "Stock")
        self.tree = ttk.Treeview(tree_frame, columns=columnas, show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Codigo", text="Código")
        self.tree.heading("Marca", text="Marca")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Stock", text="Stock Actual")
        self.tree.column("ID", width=40, anchor="center")
        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind("<Double-1>", lambda e: self.seleccionar())

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        action_frame = ttk.Frame(self, padding="10")
        action_frame.pack(fill='x')
        ttk.Button(action_frame, text="Crear Artículo Nuevo", command=self.crear_nuevo).pack(side='left')
        ttk.Button(action_frame, text="Seleccionar Artículo", command=self.seleccionar).pack(side='right')
        self.buscar_articulos()

    def buscar_articulos(self, *args):
        criterio = self.search_var.get()
        for row in self.tree.get_children():
            self.tree.delete(row)
        articulos = articulos_db.obtener_articulos_para_compra(criterio)
        for articulo in articulos:
            self.tree.insert("", "end", values=articulo)

    def crear_nuevo(self):
        temp_articulos_frame = self.main_window.obtener_frame_articulos()
        ventana_nuevo_articulo = VentanaArticulo(temp_articulos_frame)
        ventana_nuevo_articulo.guardar = self.crear_y_seleccionar_wrapper(ventana_nuevo_articulo)

    def crear_y_seleccionar_wrapper(self, ventana_abm):
        guardar_original = ventana_abm.guardar
        def guardar_y_seleccionar():
            articulo_guardado_datos = guardar_original()
            if articulo_guardado_datos:
                self.proceso_de_seleccion_final({
                    'id': articulo_guardado_datos['id'], 'codigo': articulo_guardado_datos['codigo_barras'],
                    'marca_id': articulo_guardado_datos.get('marca_id'), 'nombre': articulo_guardado_datos['nombre'],
                    'costo_sugerido': float(articulo_guardado_datos.get('precio_costo', 0.0) or 0.0),
                    'iva_sugerido': float(articulo_guardado_datos.get('iva', 0.0) or 0.0)
                })
        return guardar_y_seleccionar

    def seleccionar(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un artículo.", parent=self)
            return
        articulo_id = self.tree.item(selected_item, "values")[0]
        articulo_completo = articulos_db.obtener_articulo_por_id(articulo_id)
        articulo_info = {
            'id': articulo_id, 'codigo': articulo_completo[1], 'marca_id': articulo_completo[3],
            'nombre': articulo_completo[2], 'costo_sugerido': articulo_completo[6] or 0.0,
            'iva_sugerido': articulo_completo[7] or 0.0
        }
        self.proceso_de_seleccion_final(articulo_info)

    def proceso_de_seleccion_final(self, articulo_info):
        self.destroy()
        VentanaDetalleCompra(self.parent, articulo_info, self.callback)


class VentanaDetalleCompra(tk.Toplevel):
    def __init__(self, parent, articulo_info, callback):
        super().__init__(parent)
        self.parent = parent
        self.articulo_info = articulo_info
        self.callback = callback
        self.title(f"Detalles para: {self.articulo_info['nombre']}")
        self.geometry("400x250")
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding="10")
        frame.pack(fill='both', expand=True)
        frame.grid_columnconfigure(1, weight=1)
        ttk.Label(frame, text="Cantidad:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cantidad_entry = ttk.Entry(frame)
        self.cantidad_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(frame, text="Costo Unitario (sin IVA):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.costo_entry = ttk.Entry(frame)
        self.costo_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.costo_entry.insert(0, self.articulo_info.get('costo_sugerido', "0.0"))
        ttk.Label(frame, text="IVA (%):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.iva_combo = ttk.Combobox(frame, values=["0", "10.5", "21"], state="readonly")
        self.iva_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.iva_combo.set(str(self.articulo_info.get('iva_sugerido', "21")))
        btn_aceptar = ttk.Button(frame, text="Aceptar", command=self.aceptar)
        btn_aceptar.grid(row=3, column=0, columnspan=2, pady=15, padx=5, sticky="ew")
        self.cantidad_entry.focus_set()

    def aceptar(self):
        try:
            cantidad = float(self.cantidad_entry.get())
            costo_unit = float(self.costo_entry.get())
            iva_porc = float(self.iva_combo.get())
            if cantidad <= 0 or costo_unit < 0 or iva_porc < 0:
                messagebox.showwarning("Datos Inválidos", "Por favor, ingrese valores numéricos válidos.", parent=self)
                return
        except (ValueError, TypeError):
            messagebox.showwarning("Datos Inválidos", "Por favor, ingrese valores numéricos válidos.", parent=self)
            return
        self.callback(self.articulo_info['id'], cantidad, self.articulo_info['codigo'], self.articulo_info['marca_id'], self.articulo_info['nombre'], costo_unit, iva_porc)
        self.destroy()

class ComprasFrame(ttk.Frame):
    def __init__(self, parent, style, main_window):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.main_window = main_window
        self.items_factura = []

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Frame para Datos de la Factura ---
        factura_frame = ttk.LabelFrame(self, text="Encabezado de Factura", style="TLabelframe")
        factura_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        factura_frame.grid_columnconfigure(1, weight=1)
        factura_frame.grid_columnconfigure(3, weight=1)
        factura_frame.grid_columnconfigure(5, weight=1)

        # Fila 1: Fecha y Proveedor
        ttk.Label(factura_frame, text="Fecha Factura:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        # 2. Reemplazamos el Entry por el DateEntry
        self.fecha_factura_entry = DateEntry(factura_frame, date_pattern='yyyy-mm-dd', width=12, background='darkblue', foreground='white', borderwidth=2)
        self.fecha_factura_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(factura_frame, text="Proveedor:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.proveedor_combo = ttk.Combobox(factura_frame, state="readonly")
        self.proveedor_combo.grid(row=0, column=3, columnspan=3, padx=5, pady=5, sticky="ew")

        # Fila 2: Tipo, Número y Condición
        ttk.Label(factura_frame, text="Tipo Factura:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.tipo_factura_combo = ttk.Combobox(factura_frame, values=["Factura A", "Factura B", "Factura C", "Remito"], state="readonly")
        self.tipo_factura_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(factura_frame, text="N° Factura:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.nro_factura_entry = ttk.Entry(factura_frame)
        self.nro_factura_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        ttk.Label(factura_frame, text="Condición:").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.condicion_combo = ttk.Combobox(factura_frame, values=["Contado", "Cuenta Corriente"], state="readonly")
        self.condicion_combo.grid(row=1, column=5, padx=5, pady=5, sticky="ew")

        # Fila 3: Tipo de Compra
        ttk.Label(factura_frame, text="Tipo de Compra:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.tipo_compra_combo = ttk.Combobox(factura_frame, 
            values=["Mercadería de Reventa", "Consumibles", "Impuestos y Servicios", "Gastos Generales"], 
            state="readonly")
        self.tipo_compra_combo.grid(row=2, column=1, columnspan=5, padx=5, pady=5, sticky="ew")

        # --- El resto de la clase no cambia ---
        articulo_frame = ttk.LabelFrame(self, text="Detalle de Artículo", style="TLabelframe")
        articulo_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.buscar_articulo_btn = ttk.Button(articulo_frame, text="Buscar / Agregar Artículo a la Factura", style="Action.TButton")
        self.buscar_articulo_btn.config(command=self.abrir_ventana_busqueda)
        self.buscar_articulo_btn.pack(pady=5, padx=5, fill='x')

        detalle_frame = ttk.LabelFrame(self, text="Detalle de la Compra", style="TLabelframe")
        detalle_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        detalle_frame.grid_rowconfigure(0, weight=1)
        detalle_frame.grid_columnconfigure(0, weight=1)

        columnas = ("cantidad", "codigo", "marca", "descripcion", "costo_unit", "subtotal")
        self.tree = ttk.Treeview(detalle_frame, columns=columnas, show="headings")
        self.tree.heading("cantidad", text="Cantidad")
        self.tree.heading("codigo", text="Código")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("descripcion", text="Descripción")
        self.tree.heading("costo_unit", text="Costo Unit.")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.column("costo_unit", anchor="e")
        self.tree.column("subtotal", anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")

        acciones_frame = ttk.Frame(self, style="Content.TFrame")
        acciones_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        acciones_frame.grid_columnconfigure(0, weight=1)
        
        totales_frame = ttk.Frame(acciones_frame, style="Content.TFrame")
        totales_frame.grid(row=0, column=0, sticky="e")
        ttk.Label(totales_frame, text="Subtotal:", style="TLabel").grid(row=0, column=0, padx=5, sticky="e")
        self.subtotal_label = ttk.Label(totales_frame, text="$ 0.00", font=("Helvetica", 10), style="TLabel")
        self.subtotal_label.grid(row=0, column=1, padx=5, sticky="e")
        ttk.Label(totales_frame, text="IVA:", style="TLabel").grid(row=1, column=0, padx=5, sticky="e")
        self.iva_label = ttk.Label(totales_frame, text="$ 0.00", font=("Helvetica", 10), style="TLabel")
        self.iva_label.grid(row=1, column=1, padx=5, sticky="e")
        ttk.Label(totales_frame, text="TOTAL:", font=("Helvetica", 14, "bold"), style="TLabel").grid(row=2, column=0, padx=5, sticky="e")
        self.total_label = ttk.Label(totales_frame, text="$ 0.00", font=("Helvetica", 14, "bold"), style="TLabel")
        self.total_label.grid(row=2, column=1, padx=5, sticky="e")
        
        self.guardar_btn = ttk.Button(acciones_frame, text="Guardar Factura Completa", style="Action.TButton", command=self.guardar_factura)
        self.guardar_btn.grid(row=0, rowspan=3, column=1, padx=20, ipady=10, sticky="ns")

        self.cargar_proveedores()

    def cargar_proveedores(self):
        proveedores = proveedores_db.obtener_proveedores()
        self.proveedores_data = {f"{p[1]} ({p[2]})" if p[2] else p[1]: p[0] for p in proveedores}
        self.proveedor_combo['values'] = list(self.proveedores_data.keys())

    def abrir_ventana_busqueda(self):
        VentanaBuscarArticulo(self, callback=self.agregar_articulo_a_factura, main_window=self.main_window)

    def agregar_articulo_a_factura(self, articulo_id, cantidad, codigo, marca_id, nombre, costo_unit, iva_porc):
        marca_nombre = next((m[1] for m in articulos_db.obtener_marcas() if m[0] == marca_id), "")
        subtotal_neto = cantidad * costo_unit
        monto_iva_item = subtotal_neto * (iva_porc / 100)
        
        item_data = {
            "articulo_id": articulo_id, "cantidad": cantidad, "codigo": codigo,
            "marca_nombre": marca_nombre, "nombre": nombre, "costo_unit": costo_unit, 
            "subtotal_neto": subtotal_neto, "iva_porc": iva_porc, "monto_iva": monto_iva_item
        }
        self.items_factura.append(item_data)
        
        valores_vista = (f"{cantidad:.2f}", codigo, marca_nombre, nombre, f"${costo_unit:.2f}", f"${subtotal_neto:.2f}")
        self.tree.insert("", "end", values=valores_vista)
        self.actualizar_total_factura()
        
    def actualizar_total_factura(self):
        subtotal_general = sum(item['subtotal_neto'] for item in self.items_factura)
        iva_total = sum(item['monto_iva'] for item in self.items_factura)
        total_factura = subtotal_general + iva_total
        self.subtotal_label.config(text=f"$ {subtotal_general:.2f}")
        self.iva_label.config(text=f"$ {iva_total:.2f}")
        self.total_label.config(text=f"$ {total_factura:.2f}")

    def guardar_factura(self):
        proveedor_str = self.proveedor_combo.get()
        if not proveedor_str:
            messagebox.showwarning("Dato Faltante", "Por favor, seleccione un proveedor.")
            return
        if not self.items_factura:
            messagebox.showwarning("Factura Vacía", "Por favor, agregue al menos un artículo a la factura.")
            return
            
        total_factura = sum(item['subtotal_neto'] + item['monto_iva'] for item in self.items_factura)

        datos_factura = {
            "proveedor_id": self.proveedores_data.get(proveedor_str),
            "numero_factura": self.nro_factura_entry.get(),
            "fecha_compra": self.fecha_factura_entry.get(),
            "monto_total": total_factura,
            "condicion": self.condicion_combo.get(),
            "tipo_compra": self.tipo_compra_combo.get()
        }
        resultado = compras_db.registrar_compra(datos_factura, self.items_factura)
        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado)
            self.limpiar_formulario()
        else:
            messagebox.showerror("Error", resultado)
            
    def limpiar_formulario(self):
        self.proveedor_combo.set('')
        self.nro_factura_entry.delete(0, tk.END)
        # self.fecha_factura_entry.set_date(datetime.date.today()) # No funciona así directamente
        self.tipo_factura_combo.set('')
        self.condicion_combo.set('')
        self.tipo_compra_combo.set('')
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.items_factura = []
        self.actualizar_total_factura()