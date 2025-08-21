import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import articulos_db, clientes_db, config_db, ventas_db
from .clientes_abm import VentanaCliente
from datetime import datetime
import os
from PIL import Image, ImageTk

# (Las clases VentanaDescuento, VentanaPago y VentanaSeleccionArticulo no tienen cambios)
class VentanaDescuento(simpledialog.Dialog):
    def __init__(self, parent, title=None): super().__init__(parent, title=title)
    def body(self, master):
        self.result = None; master.grid_columnconfigure(1, weight=1)
        ttk.Label(master, text="Valor:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.valor_entry = ttk.Entry(master); self.valor_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(master, text="Tipo:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.tipo_var = tk.StringVar(value="$")
        ttk.Radiobutton(master, text="Monto Fijo ($)", variable=self.tipo_var, value="$").grid(row=1, column=1, sticky="w", padx=5)
        ttk.Radiobutton(master, text="Porcentaje (%)", variable=self.tipo_var, value="%").grid(row=2, column=1, sticky="w", padx=5)
        return self.valor_entry
    def apply(self):
        try:
            valor = float(self.valor_entry.get())
            if valor < 0: messagebox.showwarning("Inválido", "El valor no puede ser negativo.", parent=self); return
            self.result = (valor, self.tipo_var.get())
        except (ValueError, TypeError): messagebox.showwarning("Inválido", "Por favor ingrese un valor numérico.", parent=self)

class VentanaPago(tk.Toplevel):
    def __init__(self, parent, total_a_pagar, callback_finalizar):
        super().__init__(parent)
        self.parent = parent; self.total_a_pagar = float(total_a_pagar); self.callback = callback_finalizar; self.pagos_realizados = []
        self.title("Finalizar Venta"); self.geometry("600x450"); self.transient(parent); self.grab_set()
        self.frame = ttk.Frame(self, padding="10"); self.frame.pack(fill='both', expand=True); self.frame.grid_columnconfigure(0, weight=1); self.frame.grid_rowconfigure(2, weight=1)
        resumen_frame = ttk.Frame(self.frame); resumen_frame.grid(row=0, column=0, pady=(0, 10), sticky='ew'); resumen_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(resumen_frame, text="Total a Pagar:", font=("Helvetica", 12, "bold")).grid(row=0, column=0, sticky='w')
        ttk.Label(resumen_frame, text=f"$ {self.total_a_pagar:.2f}", font=("Helvetica", 12, "bold")).grid(row=0, column=1, sticky='e')
        ttk.Label(resumen_frame, text="Restante:", font=("Helvetica", 12, "bold")).grid(row=1, column=0, sticky='w')
        self.restante_label = ttk.Label(resumen_frame, text=f"$ {self.total_a_pagar:.2f}", font=("Helvetica", 12, "bold"), foreground="red"); self.restante_label.grid(row=1, column=1, sticky='e')
        pago_frame = ttk.LabelFrame(self.frame, text="Agregar Pago", style="TLabelframe"); pago_frame.grid(row=1, column=0, pady=5, sticky='nsew'); pago_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(pago_frame, text="Monto:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.monto_entry = ttk.Entry(pago_frame); self.monto_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(pago_frame, text="Medio de Pago:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.medio_pago_combo = ttk.Combobox(pago_frame, state='readonly'); self.medio_pago_combo.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        self.medios_de_pago_data = config_db.obtener_medios_de_pago(); self.medio_pago_combo['values'] = [m[1] for m in self.medios_de_pago_data]
        btn_agregar_pago = ttk.Button(pago_frame, text="Agregar Pago", command=self.agregar_pago); btn_agregar_pago.grid(row=2, column=1, padx=5, pady=5, sticky='e')
        lista_frame = ttk.LabelFrame(self.frame, text="Pagos Ingresados", style="TLabelframe"); lista_frame.grid(row=2, column=0, pady=5, sticky='nsew'); lista_frame.grid_rowconfigure(0, weight=1); lista_frame.grid_columnconfigure(0, weight=1)
        self.tree_pagos = ttk.Treeview(lista_frame, columns=("medio", "monto"), show="headings"); self.tree_pagos.heading("medio", text="Medio de Pago"); self.tree_pagos.heading("monto", text="Monto"); self.tree_pagos.column("monto", anchor='e'); self.tree_pagos.grid(row=0, column=0, sticky='nsew')
        self.btn_confirmar = ttk.Button(self.frame, text="Confirmar Venta", command=self.confirmar, state="disabled"); self.btn_confirmar.grid(row=3, column=0, pady=10, sticky='ew')
        self.actualizar_resumen()
    def agregar_pago(self):
        try:
            monto = float(self.monto_entry.get()); medio_pago_nombre = self.medio_pago_combo.get()
            if not medio_pago_nombre: messagebox.showwarning("Dato Faltante", "Seleccione un medio de pago.", parent=self); return
            if monto <= 0: messagebox.showwarning("Dato Inválido", "El monto debe ser positivo.", parent=self); return
        except ValueError: messagebox.showwarning("Dato Inválido", "Ingrese un monto numérico.", parent=self); return
        medio_pago_id = next((mid for mid, nombre in self.medios_de_pago_data if nombre == medio_pago_nombre), None)
        self.pagos_realizados.append({'medio_pago_id': medio_pago_id, 'monto': monto})
        self.tree_pagos.insert("", "end", values=(medio_pago_nombre, f"$ {monto:.2f}"))
        self.monto_entry.delete(0, tk.END); self.medio_pago_combo.set(''); self.actualizar_resumen()
    def actualizar_resumen(self):
        total_pagado = sum(p['monto'] for p in self.pagos_realizados)
        restante = self.total_a_pagar - total_pagado
        self.restante_label.config(text=f"$ {restante:.2f}")
        if total_pagado >= self.total_a_pagar - 0.01:
            vuelto = total_pagado - self.total_a_pagar
            self.restante_label.config(foreground="blue", text=f"Vuelto: $ {vuelto:.2f}"); self.btn_confirmar.config(state="normal")
        else:
            self.restante_label.config(foreground="red"); self.btn_confirmar.config(state="disabled")
    def confirmar(self): self.callback(self.pagos_realizados); self.destroy()

class VentanaSeleccionArticulo(tk.Toplevel):
    def __init__(self, parent, callback_agregar):
        super().__init__(parent)
        self.callback_agregar = callback_agregar
        self.title("Seleccionar Artículo"); self.geometry("800x600"); self.transient(parent); self.grab_set()
        search_frame = ttk.Frame(self, padding="10"); search_frame.pack(fill='x')
        ttk.Label(search_frame, text="Buscar Artículo:", font=("Helvetica", 12)).pack(side='left', padx=5)
        self.search_var = tk.StringVar(); self.search_var.trace_add("write", self._buscar_articulos)
        self.search_entry = ttk.Entry(search_frame, width=40, textvariable=self.search_var, font=("Helvetica", 12)); self.search_entry.pack(side='left', fill='x', expand=True); self.search_entry.focus_set()
        tree_frame = ttk.Frame(self, padding=(10, 0, 10, 10)); tree_frame.pack(fill='both', expand=True); tree_frame.grid_rowconfigure(0, weight=1); tree_frame.grid_columnconfigure(0, weight=1)
        columnas = ("id", "descripcion", "precio", "unidad", "imagen_path")
        self.tree = ttk.Treeview(tree_frame, columns=columnas, show="headings", style="Large.Treeview")
        self.tree.heading("descripcion", text="Descripción"); self.tree.heading("precio", text="Precio")
        self.tree.column("id", width=0, stretch=tk.NO); self.tree.column("precio", width=120, anchor="e"); self.tree.column("unidad", width=0, stretch=tk.NO); self.tree.column("imagen_path", width=0, stretch=tk.NO)
        self.tree.pack(side='left', fill='both', expand=True); self.tree.bind("<Double-1>", self._seleccionar_y_agregar)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview); scrollbar.pack(side='right', fill='y'); self.tree.configure(yscrollcommand=scrollbar.set)
        action_frame = ttk.Frame(self, padding="10"); action_frame.pack(fill='x')
        ttk.Label(action_frame, text="Cantidad:", font=("Helvetica", 12)).pack(side='left', padx=5)
        self.cantidad_entry = ttk.Entry(action_frame, width=10, font=("Helvetica", 12)); self.cantidad_entry.pack(side='left', padx=5); self.cantidad_entry.insert(0, "1")
        self.cantidad_entry.bind("<Return>", self._seleccionar_y_agregar)
        btn_agregar = ttk.Button(action_frame, text="Agregar al Carrito", command=self._seleccionar_y_agregar, style="Action.TButton"); btn_agregar.pack(side='right', padx=5)
        self._buscar_articulos()
    def _buscar_articulos(self, *args):
        criterio = self.search_var.get()
        for row in self.tree.get_children(): self.tree.delete(row)
        articulos = articulos_db.buscar_articulos_pos(criterio)
        for art in articulos:
            precio = art[2] if art[2] is not None else 0.0
            valores = (art[0], art[1], f"$ {precio:.2f}", art[3], art[4])
            self.tree.insert("", "end", values=valores, iid=art[0])
    def _seleccionar_y_agregar(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Por favor, seleccione un artículo de la lista.", parent=self); return
        try:
            cantidad = float(self.cantidad_entry.get())
            if cantidad <= 0: raise ValueError()
        except ValueError: messagebox.showerror("Cantidad Inválida", "Por favor, ingrese una cantidad numérica positiva.", parent=self); return
        item_values = self.tree.item(selected_item, "values")
        item_info = (item_values[0], item_values[1], float(item_values[2].replace("$", "")), item_values[3], item_values[4])
        self.callback_agregar(item_info, cantidad)
        self.destroy()

class POSFrame(ttk.Frame):
    def __init__(self, parent, style, main_window, caja_id):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.main_window = main_window
        self.caja_actual_id = caja_id
        
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=3); self.grid_columnconfigure(1, weight=1)

        middle_column = ttk.Frame(self, style="Content.TFrame")
        middle_column.grid(row=0, column=0, rowspan=2, padx=(10,5), pady=10, sticky="nsew")
        middle_column.grid_rowconfigure(1, weight=1); middle_column.grid_columnconfigure(0, weight=1)

        top_frame = ttk.LabelFrame(middle_column, text="Datos de Venta", style="TLabelframe")
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        top_frame.columnconfigure(1, weight=1)
        ttk.Label(top_frame, text="Cliente:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        cliente_subframe = ttk.Frame(top_frame, style="Content.TFrame"); cliente_subframe.grid(row=0, column=1, sticky="ew")
        cliente_subframe.columnconfigure(0, weight=1)
        self.cliente_search_var = tk.StringVar(); self.cliente_search_var.trace_add("write", self.actualizar_busqueda_cliente)
        self.cliente_search_entry = ttk.Entry(cliente_subframe, width=30, textvariable=self.cliente_search_var); self.cliente_search_entry.grid(row=0, column=0, padx=(0,5), pady=5, sticky="ew")
        self.add_cliente_btn = ttk.Button(cliente_subframe, text="+", width=3, command=self.crear_nuevo_cliente); self.add_cliente_btn.grid(row=0, column=1, pady=5)
        self.cliente_results_listbox = tk.Listbox(self, height=5, font=("Helvetica", 10)); self.cliente_results = []; self.cliente_results_listbox.bind("<Double-1>", self.seleccionar_cliente_de_lista)
        ttk.Label(top_frame, text="Comprobante:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.comprobante_combo = ttk.Combobox(top_frame, state="readonly"); self.comprobante_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        cart_frame = ttk.LabelFrame(middle_column, text="Carrito de Compras", style="TLabelframe"); cart_frame.grid(row=1, column=0, sticky="nsew")
        cart_frame.grid_rowconfigure(0, weight=1); cart_frame.grid_columnconfigure(0, weight=1)
        columnas = ("cant", "desc", "p_unit", "descuento", "subtotal"); self.tree = ttk.Treeview(cart_frame, columns=columnas, show="headings")
        self.tree.configure(style="Small.Treeview")
        self.tree.heading("cant", text="Cant."); self.tree.heading("desc", text="Descripción"); self.tree.heading("p_unit", text="P. Unit."); self.tree.heading("descuento", text="Desc."); self.tree.heading("subtotal", text="Subtotal")
        self.tree.column("cant", width=70, anchor="center"); self.tree.column("p_unit", width=110, anchor="e"); self.tree.column("descuento", width=90, anchor="e"); self.tree.column("subtotal", width=110, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew"); scrollbar = ttk.Scrollbar(cart_frame, orient="vertical", command=self.tree.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._mostrar_imagen_seleccionada)

        right_column = ttk.Frame(self, style="Content.TFrame")
        right_column.grid(row=0, column=1, rowspan=2, padx=(5,10), pady=10, sticky="nsew")
        right_column.grid_rowconfigure(1, weight=1)
        right_column.grid_columnconfigure(0, weight=1)
        
        item_actions_frame = ttk.Frame(right_column); item_actions_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        item_actions_frame.columnconfigure(0, weight=1)
        btn_buscar_articulo = ttk.Button(item_actions_frame, text="BUSCAR\nAGREGAR ARTÍCULO", style="Action.TButton", command=self.abrir_ventana_seleccion, compound="center"); btn_buscar_articulo.grid(row=0, column=0, sticky="ew", ipady=5)
        small_buttons_frame = ttk.Frame(item_actions_frame); small_buttons_frame.grid(row=1, column=0, sticky="ew", pady=(5,0))
        small_buttons_frame.columnconfigure(0, weight=1); small_buttons_frame.columnconfigure(1, weight=1)
        ttk.Button(small_buttons_frame, text="Descuento a Ítem", command=self.aplicar_descuento_item).grid(row=0, column=0, sticky="ew", padx=(0,2))
        ttk.Button(small_buttons_frame, text="Quitar Artículo", command=self.quitar_item_seleccionado).grid(row=0, column=1, sticky="ew", padx=(2,0))

        image_frame = ttk.LabelFrame(right_column, text="Imagen del Producto"); image_frame.grid(row=1, column=0, sticky="nsew")
        self.image_label = ttk.Label(image_frame, text="Seleccione un ítem del carrito", anchor="center"); self.image_label.pack(fill="both", expand=True, padx=5, pady=5); self.photo_image = None
        
        resumen_frame = ttk.LabelFrame(right_column, text="Resumen y Pago", style="TLabelframe"); resumen_frame.grid(row=2, column=0, sticky="ew", pady=(10,0))
        total_frame = ttk.Frame(resumen_frame, style="Content.TFrame"); total_frame.pack(fill="x", pady=10, padx=10); total_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(total_frame, text="Subtotal:").grid(row=0, column=0, sticky="w"); self.subtotal_label = ttk.Label(total_frame, text="$ 0.00"); self.subtotal_label.grid(row=0, column=1, sticky="e")
        ttk.Label(total_frame, text="Descuentos:").grid(row=1, column=0, sticky="w"); self.descuento_label = ttk.Label(total_frame, text="$ 0.00", foreground="red"); self.descuento_label.grid(row=1, column=1, sticky="e")
        ttk.Label(total_frame, text="TOTAL:", font=("Helvetica", 18, "bold")).grid(row=2, column=0, sticky="w", pady=(5,0)); self.total_label = ttk.Label(total_frame, text="$ 0.00", font=("Helvetica", 18, "bold")); self.total_label.grid(row=2, column=1, sticky="e", pady=(5,0))
        btn_descuento_total = ttk.Button(total_frame, text="Descuento al Total", command=self.aplicar_descuento_total); btn_descuento_total.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10,0))
        ttk.Button(total_frame, text="Finalizar Venta", style="Action.TButton", command=self.abrir_ventana_pago).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(5,0))
        ttk.Button(total_frame, text="Cancelar", style="Action.TButton", command=self.limpiar_venta).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(5,0))
        
        self.limpiar_venta()

    def _mostrar_imagen_seleccionada(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            self.image_label.config(image='', text="Seleccione un ítem del carrito")
            self.photo_image = None
            return

        item_id = int(selected_item)
        item_data = self.carrito_items.get(item_id)
        
        if item_data and item_data.get('imagen_path') and os.path.exists(item_data['imagen_path']):
            try:
                img = Image.open(item_data['imagen_path'])
                img.thumbnail((250, 250))
                self.photo_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.photo_image, text="")
            except Exception as e:
                self.image_label.config(image='', text="Error al cargar\nla imagen"); self.photo_image = None; print(f"Error mostrando imagen: {e}")
        else:
            self.image_label.config(image='', text="Sin imagen"); self.photo_image = None

    def abrir_ventana_seleccion(self): VentanaSeleccionArticulo(self, callback_agregar=self.agregar_item_al_carrito)

    def agregar_item_al_carrito(self, item_info, cantidad):
        item_id_str, descripcion, precio, unidad, imagen_path = item_info
        item_id = int(item_id_str)
        if item_id in self.carrito_items: self.carrito_items[item_id]['cantidad'] += cantidad
        else: self.carrito_items[item_id] = {'descripcion': descripcion, 'cantidad': cantidad, 'precio_unit': precio, 'unidad': unidad, 'descuento': 0.0, 'imagen_path': imagen_path}
        self.refrescar_venta()
    
    def refrescar_venta(self):
        selected_id = self.tree.focus()
        for row in self.tree.get_children(): self.tree.delete(row)
        subtotal_general = 0.0; descuento_items = 0.0
        for item_id, data in self.carrito_items.items():
            subtotal_bruto = data['cantidad'] * data['precio_unit']; descuento = data.get('descuento', 0.0); subtotal_item_neto = subtotal_bruto - descuento
            subtotal_general += subtotal_bruto; descuento_items += descuento
            vista_cantidad = f"{data['cantidad']:.2f}"
            self.tree.insert("", "end", iid=item_id, values=(vista_cantidad, data['descripcion'], f"${data['precio_unit']:.2f}", f"-$ {descuento:.2f}" if descuento > 0 else "$ 0.00", f"${subtotal_item_neto:.2f}"))
        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id); self.tree.focus(selected_id)
        descuento_total = descuento_items + getattr(self, 'descuento_global', 0.0); total_final = subtotal_general - descuento_total
        self.subtotal_label.config(text=f"$ {subtotal_general:.2f}"); self.descuento_label.config(text=f"-$ {descuento_total:.2f}"); self.total_label.config(text=f"$ {total_final:.2f}")

    def quitar_item_seleccionado(self):
        selected_item = self.tree.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Seleccione un ítem del carrito para quitar."); return
        item_id = int(selected_item)
        if item_id in self.carrito_items:
            del self.carrito_items[item_id]
            self.refrescar_venta(); self._mostrar_imagen_seleccionada()

    def actualizar_busqueda_cliente(self, *args):
        criterio = self.cliente_search_var.get()
        if len(criterio) < 2: self.cliente_results_listbox.place_forget(); return
        self.cliente_results = clientes_db.buscar_clientes_pos(criterio); self.cliente_results_listbox.delete(0, tk.END)
        for cliente in self.cliente_results: self.cliente_results_listbox.insert(tk.END, f"{cliente[1]} ({cliente[2]})")
        if self.cliente_results:
            w = self.cliente_search_entry.winfo_width() + self.add_cliente_btn.winfo_width()
            self.cliente_results_listbox.place(in_=self.cliente_search_entry, x=0, y=self.cliente_search_entry.winfo_height(), w=w)
        else: self.cliente_results_listbox.place_forget()

    def seleccionar_cliente(self, cliente_info):
        self.cliente_actual = cliente_info; self.cliente_search_var.set(self.cliente_actual[1]); self.cliente_results_listbox.place_forget()
        self.actualizar_tipos_comprobante()

    def actualizar_tipos_comprobante(self):
        config_empresa = config_db.obtener_configuracion()
        cond_iva_empresa = config_empresa.get('condicion_iva', 'Monotributo')
        comprobantes_disponibles = []
        if cond_iva_empresa == 'Monotributo':
            comprobantes_disponibles = ["Ticket Factura C", "Factura C", "Remito"]
        elif cond_iva_empresa == 'Responsable Inscripto':
            comprobantes_disponibles = ["Ticket Factura A", "Factura A", "Ticket Factura B", "Factura B", "Remito"]
        self.comprobante_combo['values'] = comprobantes_disponibles
        if comprobantes_disponibles: self.comprobante_combo.set(comprobantes_disponibles[0])

    def seleccionar_cliente_de_lista(self, event=None):
        if hasattr(self, 'cliente_results'):
            seleccion = self.cliente_results_listbox.curselection()
            if seleccion: self.seleccionar_cliente(self.cliente_results[seleccion[0]])
            
    def crear_nuevo_cliente(self): VentanaCliente(self, on_success_callback=self.cliente_creado_exitosamente)

    def cliente_creado_exitosamente(self, cliente_datos):
        cliente_info = (cliente_datos.get('id'), cliente_datos.get('razon_social'), cliente_datos.get('cuit_dni'))
        if cliente_info[0]: self.seleccionar_cliente(cliente_info)

    def limpiar_venta(self):
        self.carrito_items = {}; self.cliente_actual = None; self.descuento_global = 0.0
        self.cliente_search_var.set("Consumidor Final")
        self.actualizar_tipos_comprobante()
        self.refrescar_venta()
        self._mostrar_imagen_seleccionada()

    def abrir_ventana_pago(self):
        if not self.caja_actual_id: messagebox.showerror("Caja Cerrada", "Debe abrir la caja."); return
        if not self.carrito_items: messagebox.showwarning("Carrito Vacío", "No hay artículos en el carrito."); return
        total = float(self.total_label.cget("text").replace("$", "")); VentanaPago(self, total, self.finalizar_venta)

    def finalizar_venta(self, pagos):
        total_final = float(self.total_label.cget("text").replace("$", ""))
        cliente_id_a_guardar = self.cliente_actual[0] if self.cliente_actual else None
        if not cliente_id_a_guardar:
            consumidor_final = clientes_db.buscar_clientes_pos('Consumidor Final')
            if consumidor_final: cliente_id_a_guardar = consumidor_final[0][0]
        
        datos_venta = {
            'cliente_id': cliente_id_a_guardar, 
            'cliente_nombre': self.cliente_search_var.get(), 
            'total': total_final, 
            'tipo_comprobante': self.comprobante_combo.get(), 
            'caja_id': self.caja_actual_id, 
            'descuento_total': self.descuento_global
        }
        
        resultado = ventas_db.registrar_venta(datos_venta, self.carrito_items, pagos)
        
        if isinstance(resultado, int):
            venta_id = resultado
            messagebox.showinfo("Venta Finalizada", "Venta registrada exitosamente.")

            # --- NUEVA LÓGICA DE IMPRESIÓN ---
            if messagebox.askyesno("Imprimir Comprobante", "¿Desea imprimir el comprobante de la venta?"):
                # Importamos el generador aquí para evitar importaciones circulares
                from app.reports import ticket_generator
                try:
                    filepath, msg = ticket_generator.crear_comprobante_venta(venta_id)
                    if filepath:
                        # Abrir el PDF con el programa predeterminado del sistema
                        if os.name == 'nt': # Para Windows
                            os.startfile(filepath)
                        else: # Para MacOS y Linux
                            webbrowser.open(f"file://{os.path.realpath(filepath)}")
                    else:
                        messagebox.showerror("Error de Impresión", msg)
                except Exception as e:
                    messagebox.showerror("Error de Impresión", f"No se pudo generar o abrir el comprobante.\nError: {e}")
            
            self.limpiar_venta()
        else:
            messagebox.showerror("Error", resultado)

    def aplicar_descuento_item(self):
        selected_item_id = self.tree.focus()
        if not selected_item_id: messagebox.showwarning("Sin Selección", "Seleccione un artículo.", parent=self); return
        item_id = int(selected_item_id)
        if item_id not in self.carrito_items: return
        item_actual = self.carrito_items[item_id]
        subtotal_bruto = item_actual['cantidad'] * item_actual['precio_unit']
        dialogo = VentanaDescuento(self, title="Descuento por Ítem"); resultado = dialogo.result
        if resultado:
            valor, tipo = resultado; monto_descuento = 0.0
            if tipo == '%': monto_descuento = subtotal_bruto * (valor / 100)
            else: monto_descuento = valor
            if monto_descuento > subtotal_bruto: messagebox.showwarning("Inválido", "El descuento no puede ser mayor al subtotal del ítem.", parent=self); return
            self.carrito_items[item_id]['descuento'] = monto_descuento; self.refrescar_venta()
            
    def aplicar_descuento_total(self):
        subtotal_general = sum(data['cantidad'] * data['precio_unit'] for data in self.carrito_items.values())
        descuento_items = sum(data.get('descuento', 0.0) for data in self.carrito_items.values())
        max_descuento = subtotal_general - descuento_items
        dialogo = VentanaDescuento(self, title="Descuento al Total"); resultado = dialogo.result
        if resultado:
            valor, tipo = resultado; monto_descuento = 0.0
            if tipo == '%': monto_descuento = max_descuento * (valor / 100)
            else: monto_descuento = valor
            if monto_descuento > max_descuento: messagebox.showwarning("Inválido", "El descuento no puede ser mayor al total restante.", parent=self); return
            self.descuento_global = monto_descuento; self.refrescar_venta()