import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import articulos_db, clientes_db, config_db, ventas_db
from .clientes_abm import VentanaCliente
from datetime import datetime

class VentanaDescuento(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        super().__init__(parent, title=title)

    def body(self, master):
        self.result = None
        master.grid_columnconfigure(1, weight=1)

        ttk.Label(master, text="Valor:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.valor_entry = ttk.Entry(master)
        self.valor_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(master, text="Tipo:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.tipo_var = tk.StringVar(value="$")
        ttk.Radiobutton(master, text="Monto Fijo ($)", variable=self.tipo_var, value="$").grid(row=1, column=1, sticky="w", padx=5)
        ttk.Radiobutton(master, text="Porcentaje (%)", variable=self.tipo_var, value="%").grid(row=2, column=1, sticky="w", padx=5)
        
        return self.valor_entry

    def apply(self):
        try:
            valor = float(self.valor_entry.get())
            if valor < 0:
                messagebox.showwarning("Inválido", "El valor no puede ser negativo.", parent=self)
                return
            tipo = self.tipo_var.get()
            self.result = (valor, tipo)
        except (ValueError, TypeError):
            messagebox.showwarning("Inválido", "Por favor ingrese un valor numérico.", parent=self)

class VentanaPago(tk.Toplevel):
    def __init__(self, parent, total_a_pagar, callback_finalizar):
        super().__init__(parent)
        self.parent = parent
        self.total_a_pagar = float(total_a_pagar)
        self.callback = callback_finalizar
        self.pagos_realizados = []

        self.title("Finalizar Venta")
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()

        self.frame = ttk.Frame(self, padding="10")
        self.frame.pack(fill='both', expand=True)
        # ... (El resto del código de VentanaPago no cambia)

class POSFrame(ttk.Frame):
    def __init__(self, parent, style, main_window, caja_id):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.main_window = main_window
        self.caja_actual_id = caja_id
        
        # --- NUEVO LAYOUT: 2 Columnas Principales ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2) # Columna Izquierda (Carrito) más ancha
        self.grid_columnconfigure(1, weight=1) # Columna Derecha (Controles)

        # --- Columna Izquierda: Carrito de Compras ---
        cart_frame = ttk.LabelFrame(self, text="Carrito de Compras", style="TLabelframe")
        cart_frame.grid(row=0, column=0, padx=(10,5), pady=10, sticky="nsew")
        cart_frame.grid_rowconfigure(0, weight=1)
        cart_frame.grid_columnconfigure(0, weight=1)

        columnas = ("cant", "desc", "p_unit", "descuento", "subtotal")
        self.tree = ttk.Treeview(cart_frame, columns=columnas, show="headings")
        self.tree.heading("cant", text="Cant.")
        self.tree.heading("desc", text="Descripción")
        self.tree.heading("p_unit", text="P. Unit.")
        self.tree.heading("descuento", text="Descuento")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.column("cant", width=60, anchor="center")
        self.tree.column("p_unit", width=100, anchor="e")
        self.tree.column("descuento", width=80, anchor="e")
        self.tree.column("subtotal", width=100, anchor="e")
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(cart_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        acciones_carrito_frame = ttk.Frame(cart_frame)
        acciones_carrito_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.btn_descuento_item = ttk.Button(acciones_carrito_frame, text="Descuento a Ítem", command=self.aplicar_descuento_item)
        self.btn_descuento_item.pack(side="left", padx=(0, 5))

        # --- Columna Derecha: Controles Apilados ---
        right_column_frame = ttk.Frame(self, style="Content.TFrame")
        right_column_frame.grid(row=0, column=1, padx=(5,10), pady=10, sticky="nsew")
        right_column_frame.grid_columnconfigure(0, weight=1)
        
        # Panel de Búsqueda de Cliente (Arriba a la derecha)
        cliente_frame = ttk.LabelFrame(right_column_frame, text="Cliente", style="TLabelframe")
        cliente_frame.pack(side="top", fill="x", pady=(0, 5))
        
        self.cliente_search_var = tk.StringVar()
        self.cliente_search_var.trace_add("write", self.actualizar_busqueda_cliente)
        self.cliente_search_entry = ttk.Entry(cliente_frame, width=30, textvariable=self.cliente_search_var)
        self.cliente_search_entry.pack(side="left", padx=5, pady=5)
        self.add_cliente_btn = ttk.Button(cliente_frame, text="+", width=3, command=self.crear_nuevo_cliente)
        self.add_cliente_btn.pack(side="left", padx=5)
        self.cliente_results_listbox = tk.Listbox(self, height=5, font=("Helvetica", 10))
        self.cliente_results = []
        self.cliente_results_listbox.bind("<Double-1>", self.seleccionar_cliente_de_lista)

        # Panel de Búsqueda de Artículo (Centro a la derecha)
        articulo_frame = ttk.LabelFrame(right_column_frame, text="Buscar Artículo (Código o Nombre)", style="TLabelframe")
        articulo_frame.pack(side="top", fill="x", pady=5)
        articulo_frame.grid_columnconfigure(0, weight=1)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.actualizar_resultados_busqueda)
        self.articulo_search_entry = ttk.Entry(articulo_frame, textvariable=self.search_var)
        self.articulo_search_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.articulo_search_entry.bind("<Return>", self.agregar_primer_resultado)
        
        self.search_results_listbox = tk.Listbox(articulo_frame, height=5, font=("Helvetica", 10))
        self.search_results_listbox.grid(row=1, column=0, padx=5, pady=(0,5), sticky="ew")
        self.search_results_listbox.bind("<Double-1>", self.agregar_item_seleccionado)
        self.search_results = []

        # Resumen y Pago (Abajo a la derecha)
        resumen_frame = ttk.LabelFrame(right_column_frame, text="Resumen y Pago", style="TLabelframe")
        resumen_frame.pack(side="top", fill="both", expand=True, pady=5)
        resumen_frame.grid_columnconfigure(0, weight=1)
        
        total_frame = ttk.Frame(resumen_frame, style="Content.TFrame")
        total_frame.pack(side="bottom", fill="x", pady=10, padx=10)
        total_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(total_frame, text="Subtotal:").grid(row=0, column=0, sticky="w")
        self.subtotal_label = ttk.Label(total_frame, text="$ 0.00")
        self.subtotal_label.grid(row=0, column=1, sticky="e")
        ttk.Label(total_frame, text="Descuentos:").grid(row=1, column=0, sticky="w")
        self.descuento_label = ttk.Label(total_frame, text="$ 0.00", foreground="red")
        self.descuento_label.grid(row=1, column=1, sticky="e")
        ttk.Label(total_frame, text="TOTAL:", font=("Helvetica", 18, "bold")).grid(row=2, column=0, sticky="w", pady=(5,0))
        self.total_label = ttk.Label(total_frame, text="$ 0.00", font=("Helvetica", 18, "bold"))
        self.total_label.grid(row=2, column=1, sticky="e", pady=(5,0))
        
        btn_descuento_total = ttk.Button(total_frame, text="Descuento al Total", command=self.aplicar_descuento_total)
        btn_descuento_total.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10,0))
        ttk.Button(total_frame, text="Finalizar Venta", style="Action.TButton", command=self.abrir_ventana_pago).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(5,0))
        ttk.Button(total_frame, text="Cancelar", style="Action.TButton", command=self.limpiar_venta).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(5,0))
        
        self.limpiar_venta()

    def actualizar_busqueda_cliente(self, *args):
        criterio = self.cliente_search_var.get()
        if len(criterio) < 2:
            self.cliente_results_listbox.place_forget()
            return
        
        self.cliente_results = clientes_db.buscar_clientes_pos(criterio)
        self.cliente_results_listbox.delete(0, tk.END)
        
        for cliente in self.cliente_results:
            self.cliente_results_listbox.insert(tk.END, f"{cliente[1]} ({cliente[2]})")

        if self.cliente_results:
            w = self.cliente_search_entry.winfo_width() + self.add_cliente_btn.winfo_width()
            self.cliente_results_listbox.place(in_=self.cliente_search_entry, x=0, y=self.cliente_search_entry.winfo_height(), w=w)
        else:
            self.cliente_results_listbox.place_forget()

    def seleccionar_cliente(self, cliente_info):
        self.cliente_actual = cliente_info
        self.cliente_search_var.set(self.cliente_actual[1])
        self.cliente_results_listbox.place_forget()
        self.articulo_search_entry.focus_set()

    def seleccionar_cliente_de_lista(self, event=None):
        if hasattr(self, 'cliente_results'):
            seleccion = self.cliente_results_listbox.curselection()
            if seleccion:
                cliente_seleccionado = self.cliente_results[seleccion[0]]
                self.seleccionar_cliente(cliente_seleccionado)
            
    def crear_nuevo_cliente(self):
        VentanaCliente(self, on_success_callback=self.cliente_creado_exitosamente)

    def cliente_creado_exitosamente(self, cliente_datos):
        cliente_info = (cliente_datos.get('id'), cliente_datos.get('razon_social'), cliente_datos.get('cuit_dni'))
        if cliente_info[0]: self.seleccionar_cliente(cliente_info)

    def actualizar_resultados_busqueda(self, *args):
        criterio = self.search_var.get()
        self.search_results_listbox.delete(0, tk.END)
        if len(criterio) < 2:
            self.search_results = []
            return
        
        self.search_results = articulos_db.buscar_articulos_pos(criterio)
        if not self.search_results:
            self.search_results_listbox.insert(tk.END, " (No se encontraron resultados)")
            self.search_results_listbox.config(fg="gray")
        else:
            self.search_results_listbox.config(fg="black")
            for item in self.search_results:
                self.search_results_listbox.insert(tk.END, f"{item[1]} - ${item[2]:.2f}")

    def agregar_primer_resultado(self, event=None):
        if hasattr(self, 'search_results') and self.search_results:
            self.solicitar_cantidad_y_agregar(self.search_results[0])

    def agregar_item_seleccionado(self, event=None):
        if hasattr(self, 'search_results'):
            seleccion = self.search_results_listbox.curselection()
            if seleccion:
                item_seleccionado = self.search_results[seleccion[0]]
                self.solicitar_cantidad_y_agregar(item_seleccionado)

    def solicitar_cantidad_y_agregar(self, item_info):
        item_id, descripcion, precio, unidad = item_info
        titulo_dialogo = f"Cantidad para: {descripcion}"
        prompt_dialogo = f"Ingrese la cantidad ({unidad}):"
        try:
            cantidad = simpledialog.askfloat(titulo_dialogo, prompt_dialogo, parent=self)
            if cantidad is None or cantidad <= 0: return
        except tk.TclError:
            return

        self.search_var.set("")
        self.articulo_search_entry.focus_set()

        if item_id in self.carrito_items:
            self.carrito_items[item_id]['cantidad'] += cantidad
        else:
            self.carrito_items[item_id] = {'descripcion': descripcion, 'cantidad': cantidad, 'precio_unit': precio, 'unidad': unidad, 'descuento': 0.0}
        
        self.refrescar_venta()

    def refrescar_venta(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        
        subtotal_general = 0.0
        descuento_items = 0.0
        
        for item_id, data in self.carrito_items.items():
            subtotal_item_bruto = data['cantidad'] * data['precio_unit']
            descuento = data.get('descuento', 0.0)
            subtotal_item_neto = subtotal_item_bruto - descuento

            subtotal_general += subtotal_item_bruto
            descuento_items += descuento
            
            vista_cantidad = f"{data['cantidad']:.2f}" if data['unidad'] == 'KG' else f"{int(data['cantidad'])}"
            vista_precio = f"${data['precio_unit']:.2f}"
            vista_descuento = f"-$ {descuento:.2f}" if descuento > 0 else "$ 0.00"
            vista_subtotal = f"${subtotal_item_neto:.2f}"
            
            self.tree.insert("", "end", iid=item_id, values=(vista_cantidad, data['descripcion'], vista_precio, vista_descuento, vista_subtotal))

        descuento_total = descuento_items + self.descuento_global
        total_final = subtotal_general - descuento_total
        
        self.subtotal_label.config(text=f"$ {subtotal_general:.2f}")
        self.descuento_label.config(text=f"-$ {descuento_total:.2f}")
        self.total_label.config(text=f"$ {total_final:.2f}")

    def limpiar_venta(self):
        self.carrito_items = {}
        self.cliente_actual = None
        self.descuento_global = 0.0
        self.cliente_search_var.set("Consumidor Final")
        self.refrescar_venta()

    def abrir_ventana_pago(self):
        if not self.caja_actual_id:
            messagebox.showerror("Caja Cerrada", "Debe abrir la caja antes de poder registrar una venta.")
            return
        if not self.carrito_items:
            messagebox.showwarning("Carrito Vacío", "No hay artículos en el carrito para vender.")
            return
        
        total = float(self.total_label.cget("text").replace("$", ""))
        VentanaPago(self, total, self.finalizar_venta)

    def finalizar_venta(self, pagos):
        total_final = float(self.total_label.cget("text").replace("$", ""))
        cliente_id_a_guardar = self.cliente_actual[0] if self.cliente_actual else None
        
        if not cliente_id_a_guardar:
            # Lógica para encontrar o crear 'Consumidor Final'
            consumidor_final = clientes_db.buscar_clientes_pos('Consumidor Final')
            if consumidor_final:
                cliente_id_a_guardar = consumidor_final[0][0]
        
        datos_venta = {
            'cliente_id': cliente_id_a_guardar,
            'cliente_nombre': self.cliente_search_var.get(),
            'total': total_final,
            'tipo_comprobante': 'Ticket',
            'caja_id': self.caja_actual_id,
            'descuento_total': self.descuento_global
        }
        
        resultado = ventas_db.registrar_venta(datos_venta, self.carrito_items, pagos)
        
        # El resultado ahora es el ID de la venta o un string de error
        if isinstance(resultado, int):
            venta_id = resultado
            messagebox.showinfo("Venta Finalizada", "Venta registrada exitosamente.")
            
            # Preguntar si se desea imprimir el ticket
            if messagebox.askyesno("Imprimir Ticket", "¿Desea imprimir el ticket de la venta?"):
                try:
                    info_empresa = config_db.obtener_configuracion()
                    filepath = generar_ticket.crear_ticket_venta(venta_id, datos_venta, self.carrito_items, info_empresa)
                    # Abrir el PDF automáticamente
                    if os.name == 'nt': # Para Windows
                        os.startfile(filepath)
                    else: # Para macOS y Linux
                        webbrowser.open(f"file://{os.path.realpath(filepath)}")

                except Exception as e:
                    messagebox.showerror("Error de Impresión", f"No se pudo generar o abrir el ticket.\nError: {e}")
            
            self.limpiar_venta()
        else:
            messagebox.showerror("Error", resultado)
            
    def aplicar_descuento_item(self):
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Sin Selección", "Seleccione un artículo de la lista para aplicarle un descuento.", parent=self)
            return

        item_id = int(selected_item_id)
        item_actual = self.carrito_items[item_id]
        subtotal_bruto = item_actual['cantidad'] * item_actual['precio_unit']
        
        dialogo = VentanaDescuento(self, title="Descuento por Ítem")
        resultado = dialogo.result

        if resultado:
            valor, tipo = resultado
            monto_descuento = 0.0
            
            if tipo == '%':
                monto_descuento = subtotal_bruto * (valor / 100)
            else:
                monto_descuento = valor
            
            if monto_descuento > subtotal_bruto:
                messagebox.showwarning("Inválido", "El descuento no puede ser mayor al subtotal del ítem.", parent=self)
                return

            self.carrito_items[item_id]['descuento'] = monto_descuento
            self.refrescar_venta()
            
    def aplicar_descuento_total(self):
        subtotal_general = sum(data['cantidad'] * data['precio_unit'] for data in self.carrito_items.values())
        descuento_items = sum(data.get('descuento', 0.0) for data in self.carrito_items.values())
        max_descuento = subtotal_general - descuento_items

        dialogo = VentanaDescuento(self, title="Descuento al Total")
        resultado = dialogo.result

        if resultado:
            valor, tipo = resultado
            monto_descuento = 0.0

            if tipo == '%':
                monto_descuento = max_descuento * (valor / 100)
            else:
                monto_descuento = valor

            if monto_descuento > max_descuento:
                messagebox.showwarning("Inválido", "El descuento no puede ser mayor al total restante.", parent=self)
                return

            self.descuento_global = monto_descuento
            self.refrescar_venta()