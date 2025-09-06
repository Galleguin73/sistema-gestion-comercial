import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import compras_db, proveedores_db, articulos_db
from tkcalendar import DateEntry
from datetime import datetime
from .mixins.locale_validation_mixin import LocaleValidationMixin
from .articulos_abm import VentanaArticulo

def format_db_date(date_str):
    if not date_str: return ""
    try: return datetime.fromisoformat(date_str.split(' ')[0]).strftime('%d/%m/%Y')
    except (ValueError, TypeError): return date_str

class VentanaDetalleCompra(tk.Toplevel):
    def __init__(self, parent, compra_id):
        super().__init__(parent)
        self.title(f"Detalle de Compra ID: {compra_id}")
        self.geometry("800x500")
        self.transient(parent)
        self.grab_set()

        style = ttk.Style(self)
        style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")

        encabezado, detalles = compras_db.obtener_detalle_compra(compra_id)
        if not encabezado:
            messagebox.showerror("Error", f"No se pudo cargar la compra con ID {compra_id}.", parent=self)
            self.destroy()
            return

        header_container = ttk.Frame(self, style="ContentPane.TFrame")
        header_container.pack(padx=10, pady=10, fill="x")
        ttk.Label(header_container, text="Datos de la Compra", style="SectionTitle.TLabel").pack(fill="x")
        header_frame = ttk.Frame(header_container, padding=10)
        header_frame.pack(fill="x")
        header_frame.columnconfigure((1, 3), weight=1)
        fecha_formateada = datetime.strptime(encabezado[0], '%Y-%m-%d').strftime('%d/%m/%Y')
        ttk.Label(header_frame, text="Fecha:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header_frame, text=fecha_formateada).grid(row=0, column=1, sticky="w")
        ttk.Label(header_frame, text="Proveedor:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky="w")
        ttk.Label(header_frame, text=encabezado[1]).grid(row=1, column=1, columnspan=3, sticky="w")
        ttk.Label(header_frame, text="N° Factura:", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky="w", padx=(10,0))
        ttk.Label(header_frame, text=encabezado[2]).grid(row=0, column=3, sticky="w")
        ttk.Label(header_frame, text="Condición:", font=("Helvetica", 10, "bold")).grid(row=2, column=0, sticky="w")
        ttk.Label(header_frame, text=encabezado[4]).grid(row=2, column=1, sticky="w")
        ttk.Label(header_frame, text="Estado:", font=("Helvetica", 10, "bold")).grid(row=2, column=2, sticky="w", padx=(10,0))
        ttk.Label(header_frame, text=encabezado[5]).grid(row=2, column=3, sticky="w")
        total_formateado = LocaleValidationMixin._format_local_number(encabezado[3])
        ttk.Label(header_frame, text=f"Total: $ {total_formateado}", font=("Helvetica", 12, "bold")).grid(row=3, column=0, columnspan=4, sticky="w", pady=10)
        items_container = ttk.Frame(self, style="ContentPane.TFrame")
        items_container.pack(padx=10, pady=5, fill="both", expand=True)
        items_container.rowconfigure(1, weight=1); items_container.columnconfigure(0, weight=1)
        ttk.Label(items_container, text="Artículos Comprados", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        items_frame = ttk.Frame(items_container, padding=5)
        items_frame.grid(row=1, column=0, sticky="nsew")
        items_frame.rowconfigure(0, weight=1); items_frame.columnconfigure(0, weight=1)
        columnas = ("nombre", "cantidad", "costo_unit", "subtotal")
        tree = ttk.Treeview(items_frame, columns=columnas, show="headings")
        tree.heading("nombre", text="Producto"); tree.heading("cantidad", text="Cantidad"); tree.heading("costo_unit", text="Costo Unitario"); tree.heading("subtotal", text="Subtotal")
        tree.column("cantidad", anchor="center", width=80); tree.column("costo_unit", anchor="e", width=120); tree.column("subtotal", anchor="e", width=120)
        tree.grid(row=0, column=0, sticky="nsew")
        for item in detalles:
            nombre, cant, costo, subtotal = item
            valores = (nombre, cant, f"$ {LocaleValidationMixin._format_local_number(costo)}", f"$ {LocaleValidationMixin._format_local_number(subtotal)}")
            tree.insert("", "end", values=valores)
        ttk.Button(self, text="Cerrar", command=self.destroy, style="Action.TButton").pack(pady=10)

class DialogoDetalleItem(simpledialog.Dialog):
    def __init__(self, parent, title, initial_values=None):
        self.initial_values = initial_values or {}
        super().__init__(parent, title=title)
    def body(self, master):
        master.columnconfigure(1, weight=1)
        ttk.Label(master, text="Cantidad:").grid(row=0, sticky="w", padx=5, pady=5)
        self.cantidad_entry = ttk.Entry(master)
        self.cantidad_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.cantidad_entry.insert(0, self.initial_values.get('cantidad', '1.0'))
        ttk.Label(master, text="Costo Unitario:").grid(row=1, sticky="w", padx=5, pady=5)
        self.costo_entry = ttk.Entry(master)
        self.costo_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.costo_entry.insert(0, self.initial_values.get('costo_unitario', '0.0'))
        ttk.Label(master, text="IVA (%):").grid(row=2, sticky="w", padx=5, pady=5)
        self.iva_combo = ttk.Combobox(master, values=["0", "10.5", "21"], state="readonly")
        self.iva_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.iva_combo.set(self.initial_values.get('iva', '21'))
        ttk.Label(master, text="Fecha Vencimiento:").grid(row=3, sticky="w", padx=5, pady=5)
        self.fecha_venc_entry = DateEntry(master, date_pattern='dd/mm/yyyy', width=12, toplevel_parent=self)
        self.fecha_venc_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        fecha_inicial = self.initial_values.get('vencimiento')
        if fecha_inicial and isinstance(fecha_inicial, str):
            try: fecha_inicial = datetime.strptime(fecha_inicial, '%Y-%m-%d').date()
            except ValueError: fecha_inicial = None
        if fecha_inicial: self.fecha_venc_entry.set_date(fecha_inicial)
        else: self.fecha_venc_entry.set_date(None)
        ttk.Label(master, text="Lote:").grid(row=4, sticky="w", padx=5, pady=5)
        self.lote_entry = ttk.Entry(master)
        self.lote_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        self.lote_entry.insert(0, self.initial_values.get('lote', ''))
        return self.cantidad_entry
    def apply(self):
        try:
            cantidad = float(self.cantidad_entry.get())
            costo = float(self.costo_entry.get())
            iva = float(self.iva_combo.get())
            fecha_venc = self.fecha_venc_entry.get_date()
            lote = self.lote_entry.get()
            if cantidad <= 0 or costo < 0:
                messagebox.showwarning("Datos Inválidos", "La cantidad debe ser positiva y el costo no puede ser negativo.", parent=self)
                self.result = None; return
            self.result = {
                'cantidad': cantidad, 
                'costo_unitario': costo, 
                'iva': iva, 
                'vencimiento': fecha_venc, 
                'lote': lote
            }
        except (ValueError, tk.TclError):
            messagebox.showwarning("Datos Inválidos", "Por favor, ingrese valores numéricos válidos.", parent=self)
            self.result = None

class VentanaCompra(tk.Toplevel, LocaleValidationMixin):
    def __init__(self, parent, compra_id=None):
        super().__init__(parent)
        self.parent = parent
        self.compra_id = compra_id
        self.items_compra = {} 
        self._after_id = None
        
        titulo = "Editar Compra" if self.compra_id else "Nueva Compra"
        self.title(titulo)
        self.geometry("1200x700")
        self.transient(parent)
        self.grab_set()

        style = ttk.Style(self)
        style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")

        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill='both', expand=True)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._crear_widgets()

        if self.compra_id:
            self.cargar_datos_compra()

    def _crear_widgets(self):
        datos_container = ttk.Frame(self.main_frame, style="ContentPane.TFrame")
        datos_container.grid(row=0, column=0, sticky="ew", pady=(0,5))
        ttk.Label(datos_container, text="Datos del Comprobante", style="SectionTitle.TLabel").pack(fill="x")
        datos_factura_frame = ttk.Frame(datos_container, padding=10)
        datos_factura_frame.pack(fill="x")
        datos_factura_frame.columnconfigure(1, weight=1); datos_factura_frame.columnconfigure(3, weight=1); datos_factura_frame.columnconfigure(5, weight=1)
        
        ttk.Label(datos_factura_frame, text="Proveedor:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.proveedor_combo = ttk.Combobox(datos_factura_frame, state="readonly")
        self.proveedor_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(datos_factura_frame, text="Nº Factura:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.nro_factura_entry = ttk.Entry(datos_factura_frame)
        self.nro_factura_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Label(datos_factura_frame, text="Fecha Compra:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.fecha_compra_entry = DateEntry(datos_factura_frame, date_pattern='dd/mm/yyyy', width=12, toplevel_parent=self)
        self.fecha_compra_entry.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        ttk.Label(datos_factura_frame, text="Condición:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.condicion_combo = ttk.Combobox(datos_factura_frame, values=["Contado", "Cuenta Corriente"], state="readonly")
        self.condicion_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.condicion_combo.set("Cuenta Corriente")

        ttk.Label(datos_factura_frame, text="Tipo de Comprobante:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.tipo_compra_combo = ttk.Combobox(datos_factura_frame, values=["Ticket Factura A", "Ticket Factura B", "Ticket Factura C", "Factura A", "Factura B", "Factura C", "Remito"], state="readonly")
        self.tipo_compra_combo.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        self.tipo_compra_combo.set("Factura A")

        items_container = ttk.Frame(self.main_frame, style="ContentPane.TFrame")
        items_container.grid(row=1, column=0, sticky="nsew", pady=5)
        items_container.rowconfigure(1, weight=1); items_container.columnconfigure(0, weight=1)
        ttk.Label(items_container, text="Artículos de la Compra", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        items_frame = ttk.Frame(items_container, padding=10)
        items_frame.grid(row=1, column=0, sticky="nsew")
        items_frame.grid_rowconfigure(1, weight=1); items_frame.grid_columnconfigure(0, weight=1)
        
        acciones_items_frame = ttk.Frame(items_frame)
        acciones_items_frame.grid(row=0, column=0, sticky="ew", pady=(0,5))
        acciones_items_frame.columnconfigure(1, weight=1)
        ttk.Label(acciones_items_frame, text="Buscar Artículo:").grid(row=0, column=0, padx=(0,5))
        self.articulo_search = ttk.Entry(acciones_items_frame)
        self.articulo_search.grid(row=0, column=1, sticky="ew")
        self.articulo_search.bind("<KeyRelease>", self._iniciar_busqueda_articulo)
        self.articulo_search.bind("<Return>", self.buscar_y_agregar_articulo)
        
        ttk.Button(acciones_items_frame, text="Agregar", command=self.buscar_y_agregar_articulo).grid(row=0, column=2, padx=5)
        ttk.Button(acciones_items_frame, text="Crear Artículo", command=self.abrir_ventana_crear_articulo).grid(row=0, column=3, padx=5)

        self.resultados_busqueda = tk.Listbox(acciones_items_frame)
        self.resultados_busqueda.bind("<Double-Button-1>", self._seleccionar_articulo_busqueda)
        
        columnas = ("codigo", "nombre", "marca", "costo_unit", "iva", "cantidad", "subtotal")
        self.tree_items = ttk.Treeview(items_frame, columns=columnas, show="headings")
        self.tree_items.grid(row=1, column=0, sticky="nsew")

        self.tree_items.heading("codigo", text="Código Barras")
        self.tree_items.heading("nombre", text="Artículo")
        self.tree_items.heading("marca", text="Marca")
        self.tree_items.heading("costo_unit", text="Costo Unit.")
        self.tree_items.heading("iva", text="IVA%")
        self.tree_items.heading("cantidad", text="Cantidad")
        self.tree_items.heading("subtotal", text="Subtotal")
        
        self.tree_items.column("codigo", width=120)
        self.tree_items.column("nombre", width=300)
        self.tree_items.column("marca", width=120)
        self.tree_items.column("costo_unit", anchor="e", width=100)
        self.tree_items.column("iva", anchor="center", width=60)
        self.tree_items.column("cantidad", anchor="center", width=80)
        self.tree_items.column("subtotal", anchor="e", width=100)

        bottom_frame = ttk.Frame(self.main_frame); bottom_frame.grid(row=2, column=0, sticky="ew", pady=(5,0)); bottom_frame.columnconfigure(2, weight=1)
        acciones_finales_frame = ttk.Frame(bottom_frame); acciones_finales_frame.grid(row=0, column=0, sticky="w")
        ttk.Button(acciones_finales_frame, text="Quitar Item", command=self._quitar_item_seleccionado).pack(side="left", padx=(0,5))
        ttk.Button(acciones_finales_frame, text="Editar Item", command=self._editar_item_seleccionado).pack(side="left")
        
        totales_container = ttk.Frame(bottom_frame, style="ContentPane.TFrame"); totales_container.grid(row=0, column=2, sticky="e")
        ttk.Label(totales_container, text="Totales", style="SectionTitle.TLabel").pack(fill="x")
        totales_frame = ttk.Frame(totales_container, padding=10); totales_frame.pack(fill="x"); totales_frame.columnconfigure(1, weight=1)
        ttk.Label(totales_frame, text="Total Factura:", font=("Helvetica", 12, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.total_label = ttk.Label(totales_frame, text="$ 0,00", font=("Helvetica", 12, "bold")); self.total_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        botones_guardado_frame = ttk.Frame(bottom_frame); botones_guardado_frame.grid(row=0, column=3, sticky="e", padx=(10,0))
        btn_guardar_borrador = ttk.Button(botones_guardado_frame, text="Guardar Borrador", style="Action.TButton", command=lambda: self.guardar(finalizada=False))
        btn_guardar_borrador.pack(fill="x", ipady=5, pady=(0,2))
        btn_finalizar = ttk.Button(botones_guardado_frame, text="Finalizar Compra", style="Action.TButton", command=lambda: self.guardar(finalizada=True))
        btn_finalizar.pack(fill="x", ipady=5, pady=(2,0))
        
        self.cargar_datos_proveedor()
    
    def abrir_ventana_crear_articulo(self):
        VentanaArticulo(self)

    def buscar_y_agregar_articulo(self, event=None):
        criterio = self.articulo_search.get()
        if not criterio: return
        articulos = articulos_db.obtener_articulos_para_compra(criterio)
        if len(articulos) == 1: self._agregar_item_al_carrito(articulos[0])
        elif len(articulos) > 1: self._actualizar_resultados_busqueda()
        else:
            if messagebox.askyesno("Sin Resultados", "No se encontraron artículos. ¿Desea crear uno nuevo?", parent=self):
                self.abrir_ventana_crear_articulo()
        self.articulo_search.delete(0, tk.END)

    def cargar_datos_proveedor(self):
        self.proveedores = proveedores_db.obtener_todos_los_proveedores_para_reporte()
        self.proveedor_combo['values'] = [p[1] for p in self.proveedores]

    def _iniciar_busqueda_articulo(self, event):
        if self._after_id: self.after_cancel(self._after_id)
        self._after_id = self.after(300, self._actualizar_resultados_busqueda)
    
    def _actualizar_resultados_busqueda(self):
        criterio = self.articulo_search.get()
        if len(criterio) < 2:
            self.resultados_busqueda.grid_forget(); return
        self.articulos_encontrados = articulos_db.obtener_articulos_para_compra(criterio)
        self.resultados_busqueda.delete(0, tk.END)
        if self.articulos_encontrados:
            for art in self.articulos_encontrados:
                self.resultados_busqueda.insert(tk.END, f"{art[3]} ({art[2]}) - Cód: {art[1]}")
            self.resultados_busqueda.grid(row=1, column=1, columnspan=4, sticky="ew")
        else: self.resultados_busqueda.grid_forget()

    def _seleccionar_articulo_busqueda(self, event):
        seleccion = self.resultados_busqueda.curselection()
        if not seleccion: return
        articulo_seleccionado = self.articulos_encontrados[seleccion[0]]
        self.resultados_busqueda.grid_forget(); self.articulo_search.delete(0, tk.END)
        self._agregar_item_al_carrito(articulo_seleccionado)

    def _agregar_item_al_carrito(self, articulo_data):
        item_id = articulo_data[0]
        if item_id in self.items_compra:
            messagebox.showinfo("Artículo ya agregado", "Este artículo ya está en la lista. Puede editarlo.", parent=self); return
        
        dialogo = DialogoDetalleItem(self, title=f"Detalles para: {articulo_data[3]}")
        resultado = dialogo.result
        
        if resultado:
            self.items_compra[item_id] = {
                'articulo_id': item_id, 'codigo': articulo_data[1],
                'marca': articulo_data[2], 'nombre': articulo_data[3],
                **resultado }
            self._actualizar_tree_y_totales()

    def _quitar_item_seleccionado(self):
        selected = self.tree_items.focus()
        if not selected: messagebox.showwarning("Sin selección", "Seleccione un artículo para quitar.", parent=self); return
        item_id = int(selected)
        if messagebox.askyesno("Confirmar", "¿Quitar el artículo seleccionado de la lista?"):
            del self.items_compra[item_id]; self._actualizar_tree_y_totales()

    def _editar_item_seleccionado(self):
        selected = self.tree_items.focus()
        if not selected: messagebox.showwarning("Sin selección", "Seleccione un artículo para editar.", parent=self); return
        item_id = int(selected)
        item_actual = self.items_compra[item_id]
        
        dialogo = DialogoDetalleItem(self, title="Editar Ítem", initial_values=item_actual)
        resultado = dialogo.result

        if resultado:
            self.items_compra[item_id].update(resultado)
            self._actualizar_tree_y_totales()

    def _actualizar_tree_y_totales(self):
        for row in self.tree_items.get_children(): self.tree_items.delete(row)
        total_compra = 0.0
        for item_id, data in self.items_compra.items():
            subtotal = data['cantidad'] * data['costo_unitario']
            total_compra += subtotal
            
            valores = (
                data.get('codigo', ''),
                data['nombre'],
                data.get('marca', ''),
                f"$ {self._format_local_number(data['costo_unitario'])}",
                f"{data['iva']}%",
                self._format_local_number(data['cantidad']),
                f"$ {self._format_local_number(subtotal)}"
            )
            self.tree_items.insert("", "end", values=valores, iid=item_id)
        self.total_label.config(text=f"$ {self._format_local_number(total_compra)}")
    
    def guardar(self, finalizada=True):
        proveedor_nombre = self.proveedor_combo.get()
        if not proveedor_nombre: messagebox.showwarning("Datos Faltantes", "Debe seleccionar un proveedor.", parent=self); return
        if not self.items_compra: messagebox.showwarning("Sin Artículos", "Debe agregar al menos un artículo a la compra.", parent=self); return
        
        proveedor_id = next((pid for pid, nombre in self.proveedores if nombre == proveedor_nombre), None)
        
        datos_factura = {
            'proveedor_id': proveedor_id, 
            'numero_factura': self.nro_factura_entry.get(), 
            'fecha_compra': self.fecha_compra_entry.get_date().strftime('%Y-%m-%d'), 
            'monto_total': self._parse_local_number(self.total_label.cget("text").replace("$", "")), 
            'condicion': self.condicion_combo.get(), 
            'tipo_compra': self.tipo_compra_combo.get()
        }
        
        items_para_db = list(self.items_compra.values())
        
        if finalizada:
            resultado = compras_db.finalizar_compra(datos_factura, items_para_db, self.compra_id)
        else:
            resultado, self.compra_id = compras_db.guardar_borrador(datos_factura, items_para_db, self.compra_id)
        
        if "exitosamente" in resultado or isinstance(resultado, int):
            messagebox.showinfo("Éxito", resultado if isinstance(resultado, str) else "Operación exitosa.", parent=self.parent)
            self.parent.actualizar_lista_compras()
            if finalizada:
                self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

    def cargar_datos_compra(self):
        encabezado, detalles = compras_db.obtener_compra_completa_por_id(self.compra_id)
        if not encabezado: return
        keys = compras_db.get_compra_column_names(); compra_dict = dict(zip(keys, encabezado))
        proveedor_nombre = next((p[1] for p in self.proveedores if p[0] == compra_dict.get('proveedor_id')), "")
        self.proveedor_combo.set(proveedor_nombre); self.nro_factura_entry.insert(0, compra_dict.get('numero_factura', '')); self.condicion_combo.set(compra_dict.get('condicion', '')); self.tipo_compra_combo.set(compra_dict.get('tipo_compra', ''))
        fecha_db = compra_dict.get('fecha_compra')
        if fecha_db: self.fecha_compra_entry.set_date(datetime.strptime(fecha_db, '%Y-%m-%d').date())
        for item in detalles:
            item_id, codigo, marca, nombre, cantidad, costo_unitario, iva, lote, fecha_venc = item
            self.items_compra[item_id] = {
                'articulo_id': item_id, 'codigo': codigo, 'marca': marca, 'nombre': nombre, 
                'cantidad': cantidad, 'costo_unitario': costo_unitario, 'iva': iva, 'lote': lote, 'vencimiento': fecha_venc
            }
        self._actualizar_tree_y_totales()

class ComprasFrame(ttk.Frame):
    def __init__(self, parent, style, main_window):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.main_window = main_window

        self.style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        self.style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")
        
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)
        
        filtros_container = ttk.Frame(self, style="ContentPane.TFrame")
        filtros_container.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(filtros_container, text="Filtros y Acciones", style="SectionTitle.TLabel").pack(fill="x")
        filtros_frame = ttk.Frame(filtros_container, padding=10)
        filtros_frame.pack(fill="x")

        ttk.Label(filtros_frame, text="Buscar:").pack(side="left", padx=(0,5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda n, i, m: self.actualizar_lista_compras())
        search_entry = ttk.Entry(filtros_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", fill="x", expand=True)
        btn_nuevo = ttk.Button(filtros_frame, text="Nueva Compra", style="Action.TButton", command=self.abrir_ventana_nueva_compra)
        btn_nuevo.pack(side="right", padx=10)

        tree_container = ttk.Frame(self, style="ContentPane.TFrame")
        tree_container.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        tree_container.rowconfigure(1, weight=1); tree_container.columnconfigure(0, weight=1)
        ttk.Label(tree_container, text="Historial de Compras", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        tree_frame = ttk.Frame(tree_container, padding=5)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1); tree_frame.grid_columnconfigure(0, weight=1)
        
        columnas = ("id", "fecha", "proveedor", "factura", "total", "estado")
        self.tree_compras = ttk.Treeview(tree_frame, columns=columnas, show="headings")
        self.tree_compras.configure(displaycolumns=("fecha", "proveedor", "factura", "total", "estado"))
        self.tree_compras.heading("fecha", text="Fecha"); self.tree_compras.heading("proveedor", text="Proveedor"); self.tree_compras.heading("factura", text="Nº Factura"); self.tree_compras.heading("total", text="Total"); self.tree_compras.heading("estado", text="Estado")
        self.tree_compras.column("total", anchor="e")
        self.tree_compras.grid(row=0, column=0, sticky="nsew")
        
        acciones_tree_frame = ttk.Frame(self)
        acciones_tree_frame.grid(row=2, column=0, sticky="w", padx=10, pady=(0,10))
        ttk.Button(acciones_tree_frame, text="Ver Detalle", command=self.ver_detalle_compra).pack(side="left", padx=(0,5))
        ttk.Button(acciones_tree_frame, text="Editar", command=self.editar_compra_seleccionada).pack(side="left", padx=(0,5))
        ttk.Button(acciones_tree_frame, text="Anular", command=self.anular_compra_seleccionada).pack(side="left")

        self.actualizar_lista_compras()
        
    def actualizar_lista_compras(self):
        for row in self.tree_compras.get_children(): self.tree_compras.delete(row)
        criterio = self.search_var.get()
        compras = compras_db.obtener_resumen_compras(criterio)
        for compra in compras:
            id_compra, fecha, proveedor, factura, total, estado = compra
            fecha_formateada = format_db_date(fecha)
            total_formateado = f"$ {LocaleValidationMixin._format_local_number(total or 0.0)}"
            valores_mostrados = (id_compra, fecha_formateada, proveedor, factura, total_formateado, estado)
            self.tree_compras.insert("", "end", values=valores_mostrados, iid=id_compra)
    
    def abrir_ventana_nueva_compra(self):
        VentanaCompra(self)
        
    def ver_detalle_compra(self):
        selected = self.tree_compras.focus()
        if not selected: messagebox.showwarning("Sin selección", "Seleccione una compra para ver el detalle."); return
        compra_id = self.tree_compras.item(selected)['values'][0]
        VentanaDetalleCompra(self, compra_id)

    def editar_compra_seleccionada(self):
        selected = self.tree_compras.focus()
        if not selected: messagebox.showwarning("Sin selección", "Seleccione una compra para editar."); return
        compra_id = self.tree_compras.item(selected)['values'][0]
        VentanaCompra(self, compra_id=compra_id)

    def anular_compra_seleccionada(self):
        selected = self.tree_compras.focus()
        if not selected: messagebox.showwarning("Sin selección", "Seleccione una compra para anular."); return
        compra_id = self.tree_compras.item(selected)['values'][0]
        if messagebox.askyesno("Confirmar Anulación", f"¿Está seguro que desea anular la compra ID {compra_id}? Esta acción es irreversible y revertirá el stock de los artículos involucrados."):
            resultado = compras_db.anular_o_eliminar_compra(compra_id)
            if "exitosamente" in resultado:
                messagebox.showinfo("Éxito", resultado)
                self.actualizar_lista_compras()
            else:
                messagebox.showerror("Error", resultado)