import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import compras_db, articulos_db, proveedores_db
from .articulos_abm import VentanaArticulo
from tkcalendar import DateEntry
from datetime import datetime

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
        self.tree.heading("ID", text="ID"); self.tree.heading("Codigo", text="Código"); self.tree.heading("Marca", text="Marca"); self.tree.heading("Nombre", text="Nombre"); self.tree.heading("Stock", text="Stock Actual")
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
        for row in self.tree.get_children(): self.tree.delete(row)
        articulos = articulos_db.obtener_articulos_para_compra(criterio)
        for articulo in articulos: self.tree.insert("", "end", values=articulo)
    def crear_nuevo(self):
        temp_articulos_frame = self.main_window.obtener_frame_articulos()
        ventana_nuevo_articulo = VentanaArticulo(temp_articulos_frame)
        ventana_nuevo_articulo.guardar = self.crear_y_seleccionar_wrapper(ventana_nuevo_articulo)
    def crear_y_seleccionar_wrapper(self, ventana_abm):
        guardar_original = ventana_abm.guardar
        def guardar_y_seleccionar():
            articulo_guardado_datos = guardar_original()
            if articulo_guardado_datos:
                self.proceso_de_seleccion_final({'id': articulo_guardado_datos['id'], 'codigo': articulo_guardado_datos['codigo_barras'],'marca_id': articulo_guardado_datos.get('marca_id'), 'nombre': articulo_guardado_datos['nombre'],'costo_sugerido': float(articulo_guardado_datos.get('precio_costo', 0.0) or 0.0),'iva_sugerido': float(articulo_guardado_datos.get('iva', 0.0) or 0.0)})
        return guardar_y_seleccionar
    def seleccionar(self):
        selected_item = self.tree.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Por favor, seleccione un artículo.", parent=self); return
        articulo_id = self.tree.item(selected_item, "values")[0]
        articulo_completo = articulos_db.obtener_articulo_por_id(articulo_id)
        articulo_info = {'id': articulo_id, 'codigo': articulo_completo[1], 'marca_id': articulo_completo[3],'nombre': articulo_completo[2], 'costo_sugerido': articulo_completo[6] or 0.0,'iva_sugerido': articulo_completo[7] or 0.0}
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
        self.geometry("400x250"); self.transient(parent); self.grab_set()
        frame = ttk.Frame(self, padding="10"); frame.pack(fill='both', expand=True); frame.grid_columnconfigure(1, weight=1)
        ttk.Label(frame, text="Cantidad:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cantidad_entry = ttk.Entry(frame); self.cantidad_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(frame, text="Costo Unitario (sin IVA):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.costo_entry = ttk.Entry(frame); self.costo_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.costo_entry.insert(0, self.articulo_info.get('costo_sugerido', "0.0"))
        ttk.Label(frame, text="IVA (%):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.iva_combo = ttk.Combobox(frame, values=["0", "10.5", "21"], state="readonly")
        self.iva_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.iva_combo.set(str(self.articulo_info.get('iva_sugerido', "21")))
        btn_aceptar = ttk.Button(frame, text="Aceptar", command=self.aceptar); btn_aceptar.grid(row=3, column=0, columnspan=2, pady=15, sticky="ew")
        self.cantidad_entry.focus_set()
    def aceptar(self):
        try:
            cantidad = float(self.cantidad_entry.get())
            costo_unit = float(self.costo_entry.get())
            iva_porc = float(self.iva_combo.get())
            if cantidad <= 0 or costo_unit < 0 or iva_porc < 0:
                messagebox.showwarning("Datos Inválidos", "Por favor, ingrese valores numéricos válidos.", parent=self); return
        except (ValueError, TypeError):
            messagebox.showwarning("Datos Inválidos", "Por favor, ingrese valores numéricos válidos.", parent=self); return
        self.callback(self.articulo_info['id'], cantidad, self.articulo_info['codigo'], self.articulo_info['marca_id'], self.articulo_info['nombre'], costo_unit, iva_porc)
        self.destroy()
class VentanaEditarItem(tk.Toplevel):
    def __init__(self, parent, item_actual):
        super().__init__(parent)
        self.parent = parent
        self.resultado = None
        self.title("Editar Ítem")
        self.geometry("400x250"); self.transient(parent); self.grab_set()
        frame = ttk.Frame(self, padding="15"); frame.pack(fill="both", expand=True); frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Producto:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(frame, text=item_actual['nombre']).grid(row=0, column=1, sticky="w", pady=5)
        ttk.Label(frame, text="Cantidad:").grid(row=1, column=0, sticky="w", pady=5)
        self.cantidad_var = tk.StringVar(value=item_actual['cantidad']); self.cantidad_entry = ttk.Entry(frame, textvariable=self.cantidad_var); self.cantidad_entry.grid(row=1, column=1, sticky="ew")
        ttk.Label(frame, text="Costo Unitario (sin IVA):").grid(row=2, column=0, sticky="w", pady=5)
        self.costo_var = tk.StringVar(value=item_actual['costo_unit']); self.costo_entry = ttk.Entry(frame, textvariable=self.costo_var); self.costo_entry.grid(row=2, column=1, sticky="ew")
        ttk.Label(frame, text="IVA (%):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.iva_var = tk.StringVar(value=item_actual['iva_porc']); self.iva_combo = ttk.Combobox(frame, values=["0", "10.5", "21"], state="readonly", textvariable=self.iva_var); self.iva_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        btn_guardar = ttk.Button(frame, text="Guardar Cambios", command=self.guardar, style="Action.TButton"); btn_guardar.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(15,0))
        self.cantidad_entry.focus_set(); self.cantidad_entry.select_range(0, 'end')
    def guardar(self):
        try:
            nueva_cantidad = float(self.cantidad_var.get()); nuevo_costo = float(self.costo_var.get()); nuevo_iva = float(self.iva_var.get())
            if nueva_cantidad <= 0 or nuevo_costo < 0 or nuevo_iva < 0: raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Cantidad, costo e IVA deben ser números válidos y positivos.", parent=self); return
        self.resultado = {'cantidad': nueva_cantidad, 'costo': nuevo_costo, 'iva': nuevo_iva}
        self.destroy()
class VentanaVerDetalle(tk.Toplevel):
    def __init__(self, parent, compra_id):
        super().__init__(parent)
        self.title(f"Detalle de Compra ID: {compra_id}"); self.geometry("750x550"); self.transient(parent); self.grab_set()
        encabezado, detalles = compras_db.obtener_detalle_compra(compra_id)
        if not encabezado: messagebox.showerror("Error", f"No se pudo cargar la compra con ID {compra_id}.", parent=self); self.destroy(); return
        header_frame = ttk.LabelFrame(self, text="Datos de la Factura", padding=10); header_frame.pack(padx=10, pady=10, fill="x")
        header_frame.columnconfigure(1, weight=1); header_frame.columnconfigure(3, weight=1)
        ttk.Label(header_frame, text="Fecha:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w"); ttk.Label(header_frame, text=encabezado[0]).grid(row=0, column=1, sticky="w")
        ttk.Label(header_frame, text="Proveedor:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky="w"); ttk.Label(header_frame, text=encabezado[1]).grid(row=1, column=1, columnspan=3, sticky="w")
        ttk.Label(header_frame, text="Factura N°:", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky="w", padx=(10,0)); ttk.Label(header_frame, text=encabezado[2]).grid(row=0, column=3, sticky="w")
        ttk.Label(header_frame, text="Condición:", font=("Helvetica", 10, "bold")).grid(row=2, column=0, sticky="w"); ttk.Label(header_frame, text=encabezado[4] or "N/A").grid(row=2, column=1, sticky="w")
        ttk.Label(header_frame, text="Estado:", font=("Helvetica", 10, "bold")).grid(row=2, column=2, sticky="w", padx=(10,0)); ttk.Label(header_frame, text=encabezado[5]).grid(row=2, column=3, sticky="w")
        ttk.Label(header_frame, text=f"Total: $ {encabezado[3]:.2f}", font=("Helvetica", 12, "bold")).grid(row=3, column=0, columnspan=4, sticky="w", pady=10)
        items_frame = ttk.LabelFrame(self, text="Artículos Comprados", padding=10); items_frame.pack(padx=10, pady=5, fill="both", expand=True)
        items_frame.rowconfigure(0, weight=1); items_frame.columnconfigure(0, weight=1)
        columnas = ("descripcion", "cantidad", "costo", "subtotal"); tree = ttk.Treeview(items_frame, columns=columnas, show="headings")
        tree.heading("descripcion", text="Descripción"); tree.heading("cantidad", text="Cantidad"); tree.heading("costo", text="Costo Unit."); tree.heading("subtotal", text="Subtotal")
        tree.column("cantidad", anchor="center", width=80); tree.column("costo", anchor="e", width=100); tree.column("subtotal", anchor="e", width=100)
        tree.grid(row=0, column=0, sticky="nsew"); scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=tree.yview); scrollbar.grid(row=0, column=1, sticky="ns"); tree.configure(yscrollcommand=scrollbar.set)
        for item in detalles:
            nombre, cantidad, precio, subtotal = item
            valores = (nombre, f"{cantidad or 0.0:.2f}", f"$ {precio or 0.0:.2f}", f"$ {subtotal or 0.0:.2f}")
            tree.insert("", "end", values=valores)
        ttk.Button(self, text="Cerrar", command=self.destroy, style="Action.TButton").pack(pady=10)

# --- CLASE 5: El formulario de carga/edición ---
class VentanaGestionCompra(tk.Toplevel):
    def __init__(self, parent, main_window, compra_id=None):
        super().__init__(parent)
        self.parent = parent
        self.main_window = main_window
        self.compra_id = compra_id
        self.items_factura = []
        
        titulo = "Editar Compra" if self.compra_id else "Cargar Nueva Compra"
        self.title(titulo)
        self.geometry("950x700")
        self.transient(parent); self.grab_set()

        self.grid_rowconfigure(2, weight=1); self.grid_columnconfigure(0, weight=1)

        factura_frame = ttk.LabelFrame(self, text="Encabezado de Factura", style="TLabelframe")
        factura_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        factura_frame.grid_columnconfigure(1, weight=1); factura_frame.grid_columnconfigure(3, weight=1); factura_frame.grid_columnconfigure(5, weight=1)
        ttk.Label(factura_frame, text="Fecha Factura:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.fecha_factura_entry = DateEntry(factura_frame, date_pattern='yyyy-mm-dd', width=12)
        self.fecha_factura_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(factura_frame, text="Proveedor:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.proveedor_combo = ttk.Combobox(factura_frame, state="readonly")
        self.proveedor_combo.grid(row=0, column=3, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Label(factura_frame, text="Tipo Factura:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # --- LÍNEA MODIFICADA: Añadimos "Nota de Crédito" a las opciones ---
        self.tipo_factura_combo = ttk.Combobox(factura_frame, values=["Factura A", "Factura B", "Factura C", "Remito", "Nota de Crédito"], state="readonly")
        
        self.tipo_factura_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(factura_frame, text="N° Factura:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.nro_factura_entry = ttk.Entry(factura_frame)
        self.nro_factura_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        ttk.Label(factura_frame, text="Condición:").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.condicion_combo = ttk.Combobox(factura_frame, values=["Contado", "Cuenta Corriente"], state="readonly")
        self.condicion_combo.grid(row=1, column=5, padx=5, pady=5, sticky="ew")

        articulo_frame = ttk.LabelFrame(self, text="Detalle de Artículo", style="TLabelframe")
        articulo_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.buscar_articulo_btn = ttk.Button(articulo_frame, text="Buscar / Agregar Artículo a la Factura", style="Action.TButton", command=self.abrir_ventana_busqueda)
        self.buscar_articulo_btn.pack(pady=5, padx=5, fill='x')

        detalle_frame = ttk.LabelFrame(self, text="Detalle de la Compra", style="TLabelframe")
        detalle_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        detalle_frame.grid_rowconfigure(0, weight=1); detalle_frame.grid_columnconfigure(0, weight=1)

        columnas = ("id", "cantidad", "codigo", "marca", "descripcion", "costo_unit", "subtotal")
        self.tree = ttk.Treeview(detalle_frame, columns=columnas, show="headings", displaycolumns=("cantidad", "codigo", "marca", "descripcion", "costo_unit", "subtotal"))
        self.tree.heading("cantidad", text="Cantidad"); self.tree.heading("codigo", text="Código"); self.tree.heading("marca", text="Marca"); self.tree.heading("descripcion", text="Descripción"); self.tree.heading("costo_unit", text="Costo Unit."); self.tree.heading("subtotal", text="Subtotal")
        self.tree.column("id", width=0, stretch=tk.NO); self.tree.column("cantidad", width=80, anchor="center"); self.tree.column("descripcion", width=350); self.tree.column("costo_unit", anchor="e"); self.tree.column("subtotal", anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew"); scrollbar = ttk.Scrollbar(detalle_frame, orient="vertical", command=self.tree.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree.configure(yscrollcommand=scrollbar.set)
        
        list_actions_frame = ttk.Frame(self); list_actions_frame.grid(row=2, column=1, padx=10, pady=10, sticky="ns")
        btn_edit_item = ttk.Button(list_actions_frame, text="Editar Ítem", command=self.abrir_ventana_edicion_item, style="Action.TButton"); btn_edit_item.pack(pady=5, fill='x')
        btn_remove_item = ttk.Button(list_actions_frame, text="Quitar Ítem", command=self.quitar_item, style="Action.TButton"); btn_remove_item.pack(pady=5, fill='x')
        
        acciones_frame = ttk.Frame(self, style="Content.TFrame"); acciones_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        acciones_frame.grid_columnconfigure(0, weight=1); totales_frame = ttk.Frame(acciones_frame, style="Content.TFrame"); totales_frame.grid(row=0, column=0, sticky="e")
        ttk.Label(totales_frame, text="Subtotal:").grid(row=0, column=0, padx=5, sticky="e"); self.subtotal_label = ttk.Label(totales_frame, text="$ 0.00", font=("Helvetica", 10)); self.subtotal_label.grid(row=0, column=1, padx=5, sticky="e")
        ttk.Label(totales_frame, text="IVA:").grid(row=1, column=0, padx=5, pady=5, sticky="e"); self.iva_label = ttk.Label(totales_frame, text="$ 0.00", font=("Helvetica", 10)); self.iva_label.grid(row=1, column=1, padx=5, sticky="e")
        ttk.Label(totales_frame, text="TOTAL:", font=("Helvetica", 14, "bold")).grid(row=2, column=0, padx=5, sticky="e"); self.total_label = ttk.Label(totales_frame, text="$ 0.00", font=("Helvetica", 14, "bold")); self.total_label.grid(row=2, column=1, padx=5, sticky="e")
        
        texto_boton_guardar = "Guardar Cambios" if self.compra_id else "Guardar Factura Completa"
        self.guardar_btn = ttk.Button(acciones_frame, text=texto_boton_guardar, style="Action.TButton", command=self.guardar_factura)
        self.guardar_btn.grid(row=0, rowspan=3, column=1, padx=20, ipady=10, sticky="ns")
        
        self.cargar_proveedores()
        if self.compra_id:
            self._cargar_datos_compra()

    def _cargar_datos_compra(self):
        encabezado, detalles = compras_db.obtener_compra_completa_por_id(self.compra_id)
        if not encabezado: messagebox.showerror("Error", "No se encontraron datos para editar.", parent=self); self.destroy(); return
        
        self.fecha_factura_entry.set_date(encabezado[3])
        proveedor_id = encabezado[1]
        proveedor_nombre = next((nombre for nombre, pid in self.proveedores_data.items() if pid == proveedor_id), None)
        if proveedor_nombre: self.proveedor_combo.set(proveedor_nombre)
        self.tipo_factura_combo.set(encabezado[5])
        self.nro_factura_entry.insert(0, encabezado[2])
        condicion = encabezado[7]
        if condicion: self.condicion_combo.set(condicion)
        
        for item in detalles:
            self.agregar_articulo_a_factura(articulo_id=item[0], cantidad=item[4], codigo=item[1], marca_id=None, nombre=item[3], costo_unit=item[5], iva_porc=item[6], marca_nombre_directo=item[2])

    def cargar_proveedores(self):
        proveedores = proveedores_db.obtener_proveedores()
        self.proveedores_data = {f"{p[1]} ({p[2]})" if p[2] else p[1]: p[0] for p in proveedores}
        self.proveedor_combo['values'] = list(self.proveedores_data.keys())

    def abrir_ventana_busqueda(self):
        VentanaBuscarArticulo(self, callback=self.agregar_articulo_a_factura, main_window=self.main_window)

    def agregar_articulo_a_factura(self, articulo_id, cantidad, codigo, marca_id, nombre, costo_unit, iva_porc, marca_nombre_directo=None):
        articulo_id = int(articulo_id)
        if self.compra_id is None:
            if any(item['articulo_id'] == articulo_id for item in self.items_factura):
                messagebox.showwarning("Artículo Duplicado", f"El artículo '{nombre}' ya está en la lista.", parent=self); return
        marca_nombre = marca_nombre_directo if marca_nombre_directo is not None else next((m[1] for m in articulos_db.obtener_marcas() if m[0] == marca_id), "")
        subtotal_neto = cantidad * costo_unit
        monto_iva_item = subtotal_neto * (iva_porc / 100)
        item_data = {"articulo_id": articulo_id, "cantidad": cantidad, "codigo": codigo, "marca_nombre": marca_nombre, "nombre": nombre, "costo_unit": costo_unit, "subtotal_neto": subtotal_neto, "iva_porc": iva_porc, "monto_iva": monto_iva_item}
        self.items_factura.append(item_data)
        valores_vista = (articulo_id, f"{cantidad:.2f}", codigo, marca_nombre, nombre, f"${costo_unit:.2f}", f"${subtotal_neto:.2f}")
        self.tree.insert("", "end", values=valores_vista, iid=articulo_id)
        self.actualizar_total_factura()
        
    def actualizar_total_factura(self):
        subtotal_general = sum(item['subtotal_neto'] for item in self.items_factura)
        iva_total = sum(item['monto_iva'] for item in self.items_factura)
        total_factura = subtotal_general + iva_total
        self.subtotal_label.config(text=f"$ {subtotal_general:.2f}"); self.iva_label.config(text=f"$ {iva_total:.2f}"); self.total_label.config(text=f"$ {total_factura:.2f}")

    def quitar_item(self):
        selected_iid = self.tree.focus()
        if not selected_iid: messagebox.showwarning("Sin Selección", "Seleccione un ítem de la lista para quitar."); return
        self.items_factura = [item for item in self.items_factura if item['articulo_id'] != int(selected_iid)]
        self.tree.delete(selected_iid)
        self.actualizar_total_factura()
    
    def abrir_ventana_edicion_item(self):
        selected_iid = self.tree.focus()
        if not selected_iid: messagebox.showwarning("Sin Selección", "Seleccione un ítem para editar."); return
        item_a_editar = next((item for item in self.items_factura if item['articulo_id'] == int(selected_iid)), None)
        if not item_a_editar: return
        ventana_edicion = VentanaEditarItem(self, item_a_editar); self.wait_window(ventana_edicion)
        if ventana_edicion.resultado:
            nuevos_datos = ventana_edicion.resultado
            item_a_editar.update({ 'cantidad': nuevos_datos['cantidad'], 'costo_unit': nuevos_datos['costo'], 'iva_porc': nuevos_datos['iva'], 'subtotal_neto': nuevos_datos['cantidad'] * nuevos_datos['costo'], 'monto_iva': (nuevos_datos['cantidad'] * nuevos_datos['costo']) * (nuevos_datos['iva'] / 100) })
            nuevos_valores_vista = (item_a_editar['articulo_id'], f"{item_a_editar['cantidad']:.2f}", item_a_editar['codigo'], item_a_editar['marca_nombre'], item_a_editar['nombre'], f"${item_a_editar['costo_unit']:.2f}", f"${item_a_editar['subtotal_neto']:.2f}")
            self.tree.item(selected_iid, values=nuevos_valores_vista)
            self.actualizar_total_factura()

    def guardar_factura(self):
        proveedor_str = self.proveedor_combo.get()
        if not proveedor_str or not self.condicion_combo.get() or not self.tipo_factura_combo.get():
            messagebox.showwarning("Datos Faltantes", "Proveedor, Condición y Tipo de Factura son obligatorios.", parent=self); return
        if not self.items_factura:
            messagebox.showwarning("Factura Vacía", "Agregue al menos un artículo.", parent=self); return
            
        total_factura = sum(item['subtotal_neto'] + item['monto_iva'] for item in self.items_factura)
        datos_factura = {"proveedor_id": self.proveedores_data.get(proveedor_str), "numero_factura": self.nro_factura_entry.get(), "fecha_compra": self.fecha_factura_entry.get(), "monto_total": total_factura, "condicion": self.condicion_combo.get(), "tipo_compra": self.tipo_factura_combo.get()}
        
        if self.compra_id:
            resultado = compras_db.modificar_compra(self.compra_id, datos_factura, self.items_factura)
        else:
            resultado = compras_db.registrar_compra(datos_factura, self.items_factura)
        
        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self); self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

class ComprasFrame(ttk.Frame):
    def __init__(self, parent, style, main_window):
        super().__init__(parent, style="Content.TFrame")
        self.main_window = main_window
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        filtros_frame = ttk.Frame(self, style="Content.TFrame")
        filtros_frame.grid(row=0, column=0, padx=10, pady=(10,0), sticky="ew")
        ttk.Label(filtros_frame, text="Buscar:").pack(side="left", padx=(0,5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda n, i, m: self.actualizar_lista())
        search_entry = ttk.Entry(filtros_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", fill="x", expand=True)

        self.tree_frame = ttk.Frame(self, style="Content.TFrame")
        self.tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        
        columnas = ("id", "fecha", "proveedor", "factura", "total", "estado")
        self.tree = ttk.Treeview(self.tree_frame, columns=columnas, show="headings", displaycolumns=("fecha", "proveedor", "factura", "total", "estado"))
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("proveedor", text="Proveedor")
        self.tree.heading("factura", text="N° Factura")
        self.tree.heading("total", text="Total")
        self.tree.heading("estado", text="Estado")
        self.tree.column("id", width=0, stretch=tk.NO)
        self.tree.column("proveedor", width=300)
        self.tree.column("total", anchor='e')
        self.tree.column("estado", anchor='center')
        
        # --- NUEVO: Definición de los estilos de color para las filas ---
        self.tree.tag_configure('pagada', background='#d4edda', foreground='#155724') # Fondo verde claro, texto verde oscuro
        self.tree.tag_configure('impaga', background='#fff3cd', foreground='#856404') # Fondo amarillo, texto oscuro
        self.tree.tag_configure('anulada', foreground='gray') # Texto gris
        
        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind("<Double-1>", self.ver_detalle)
        self.tree.bind("<<TreeviewSelect>>", self._actualizar_estado_botones)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.button_frame = ttk.Frame(self, style="Content.TFrame")
        self.button_frame.grid(row=1, column=1, padx=10, pady=10, sticky="ns")
        
        self.add_btn = ttk.Button(self.button_frame, text="Cargar Nueva Compra", command=self.cargar_nueva_compra, style="Action.TButton")
        self.add_btn.pack(pady=5, fill='x')
        self.view_btn = ttk.Button(self.button_frame, text="Ver Detalle", command=self.ver_detalle, style="Action.TButton")
        self.view_btn.pack(pady=5, fill='x')
        self.anular_btn = ttk.Button(self.button_frame, text="Anular Compra", command=self.anular_compra, style="Action.TButton")
        self.anular_btn.pack(pady=5, fill='x')

        self.actualizar_lista()

    def _actualizar_estado_botones(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            self.view_btn.config(state="disabled")
            self.anular_btn.config(state="disabled")
            return

        self.view_btn.config(state="normal")
        valores = self.tree.item(selected_item, "values")
        if not valores: return
        
        estado = valores[5]
        if estado == 'ANULADA':
            self.anular_btn.config(state="disabled")
        else:
            self.anular_btn.config(state="normal")

    def actualizar_lista(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        compras = compras_db.obtener_resumen_compras(self.search_var.get())
        
        for compra in compras:
            # compra = (id, fecha, proveedor, factura, total, estado)
            estado = compra[5]
            
            # --- NUEVO: Asignamos un tag de color según el estado ---
            tag_color = ''
            if estado == 'PAGADA':
                tag_color = 'pagada'
            elif estado == 'IMPAGA' or estado == 'PAGO PARCIAL':
                tag_color = 'impaga'
            elif estado == 'ANULADA':
                tag_color = 'anulada'

            # Formateamos el total como moneda
            valores = list(compra)
            valores[4] = f"$ {compra[4]:.2f}"
            
            # Insertamos la fila en la tabla con su tag de color
            self.tree.insert("", "end", values=tuple(valores), tags=(tag_color,))
            
        self._actualizar_estado_botones()

    def cargar_nueva_compra(self):
        # Para esta ventana, necesitaríamos el código completo de VentanaGestionCompra
        # Asumo que ya lo tienes en tu archivo
        # ventana = VentanaGestionCompra(self, self.main_window)
        # self.wait_window(ventana)
        # self.actualizar_lista()
        messagebox.showinfo("Info", "Funcionalidad de Cargar Nueva Compra no incluida en este fragmento.")


    def ver_detalle(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Seleccione una compra de la lista."); return
        compra_id = self.tree.item(selected_item, "values")[0]
        # VentanaVerDetalle(self, compra_id)
        messagebox.showinfo("Info", f"Se abriría el detalle para la compra ID: {compra_id}")

    def anular_compra(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        valores = self.tree.item(selected_item, "values")
        compra_id, proveedor, estado = valores[0], valores[2], valores[5]
        if estado == 'ANULADA': messagebox.showwarning("Acción no permitida", "Esta compra ya ha sido anulada.", parent=self); return
        if messagebox.askyesno("Confirmar Anulación", f"¿Está seguro de anular la compra a '{proveedor}' (ID: {compra_id})?\n\nEsta acción revertirá el stock y la cuenta corriente.", parent=self):
            resultado = compras_db.anular_o_eliminar_compra(compra_id)
            messagebox.showinfo("Resultado", resultado, parent=self)
            self.actualizar_lista()