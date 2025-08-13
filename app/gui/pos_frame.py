import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import articulos_db, clientes_db, config_db, ventas_db
from .clientes_abm import VentanaCliente
from datetime import datetime

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
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)

        resumen_frame = ttk.Frame(self.frame)
        resumen_frame.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky='ew')
        resumen_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(resumen_frame, text="Total Venta:", font=("Helvetica", 12, "bold")).grid(row=0, column=0, sticky='w')
        ttk.Label(resumen_frame, text=f"$ {self.total_a_pagar:.2f}", font=("Helvetica", 12, "bold")).grid(row=0, column=1, sticky='e')
        ttk.Label(resumen_frame, text="Restante:", font=("Helvetica", 12, "bold")).grid(row=1, column=0, sticky='w')
        self.restante_label = ttk.Label(resumen_frame, text=f"$ {self.total_a_pagar:.2f}", font=("Helvetica", 12, "bold"), foreground="red")
        self.restante_label.grid(row=1, column=1, sticky='e')

        pago_frame = ttk.LabelFrame(self.frame, text="Agregar Pago", style="TLabelframe")
        pago_frame.grid(row=1, column=0, pady=5, sticky='nsew')
        pago_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(pago_frame, text="Monto:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.monto_entry = ttk.Entry(pago_frame)
        self.monto_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        ttk.Label(pago_frame, text="Medio de Pago:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.medio_pago_combo = ttk.Combobox(pago_frame, state='readonly')
        self.medio_pago_combo.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        self.medios_de_pago_data = config_db.obtener_medios_de_pago()
        self.medio_pago_combo['values'] = [m[1] for m in self.medios_de_pago_data]

        btn_agregar_pago = ttk.Button(pago_frame, text="Agregar Pago", command=self.agregar_pago)
        btn_agregar_pago.grid(row=2, column=1, padx=5, pady=5, sticky='e')

        lista_frame = ttk.LabelFrame(self.frame, text="Pagos", style="TLabelframe")
        lista_frame.grid(row=2, column=0, pady=5, sticky='nsew')
        lista_frame.grid_rowconfigure(0, weight=1)
        lista_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(lista_frame, columns=("medio", "monto"), show="headings")
        self.tree.heading("medio", text="Medio de Pago")
        self.tree.heading("monto", text="Monto")
        self.tree.column("monto", anchor='e')
        self.tree.grid(row=0, column=0, sticky='nsew')

        self.btn_confirmar = ttk.Button(self.frame, text="Confirmar Venta", command=self.confirmar, state="disabled")
        self.btn_confirmar.grid(row=3, column=0, pady=10, sticky='ew')
        
        self.actualizar_resumen()

    def agregar_pago(self):
        try:
            monto = float(self.monto_entry.get())
            medio_pago_nombre = self.medio_pago_combo.get()
            if not medio_pago_nombre:
                messagebox.showwarning("Dato Faltante", "Seleccione un medio de pago.", parent=self)
                return
            if monto <= 0:
                messagebox.showwarning("Dato Inválido", "El monto debe ser positivo.", parent=self)
                return
        except ValueError:
            messagebox.showwarning("Dato Inválido", "Ingrese un monto numérico.", parent=self)
            return

        medio_pago_id = next(mid for mid, nombre in self.medios_de_pago_data if nombre == medio_pago_nombre)
        self.pagos_realizados.append({'medio_pago_id': medio_pago_id, 'monto': monto})
        self.tree.insert("", "end", values=(medio_pago_nombre, f"$ {monto:.2f}"))
        self.monto_entry.delete(0, tk.END)
        self.actualizar_resumen()
        
    def actualizar_resumen(self):
        total_pagado = sum(p['monto'] for p in self.pagos_realizados)
        restante = self.total_a_pagar - total_pagado
        
        self.restante_label.config(text=f"$ {restante:.2f}")

        if restante <= 0.01:
            self.restante_label.config(foreground="green")
            self.btn_confirmar.config(state="normal")
        else:
            self.restante_label.config(foreground="red")
            self.btn_confirmar.config(state="disabled")

    def confirmar(self):
        self.callback(self.pagos_realizados)
        self.destroy()

class POSFrame(ttk.Frame):
    def __init__(self, parent, style, main_window, caja_id):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.main_window = main_window
        self.caja_actual_id = caja_id
        self.carrito_items = {}
        self.cliente_actual = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        top_frame = ttk.Frame(self, style="Content.TFrame")
        top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        cliente_frame = ttk.LabelFrame(top_frame, text="Cliente", style="TLabelframe")
        cliente_frame.grid(row=0, column=0, padx=(0,10), sticky="ew")
        
        self.cliente_search_var = tk.StringVar()
        self.cliente_search_var.trace_add("write", self.actualizar_busqueda_cliente)
        self.cliente_search_entry = ttk.Entry(cliente_frame, width=30, textvariable=self.cliente_search_var)
        self.cliente_search_entry.pack(side="left", padx=5, pady=5)
        self.add_cliente_btn = ttk.Button(cliente_frame, text="+", width=3, command=self.crear_nuevo_cliente)
        self.add_cliente_btn.pack(side="left", padx=5)

        self.cliente_results_listbox = tk.Listbox(self, height=5, font=("Helvetica", 10))
        self.cliente_results = []
        self.cliente_results_listbox.bind("<Double-1>", self.seleccionar_cliente_de_lista)

        articulo_frame = ttk.LabelFrame(top_frame, text="Buscar Artículo (Código o Nombre)", style="TLabelframe")
        articulo_frame.grid(row=0, column=1, sticky="ew")
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

        cart_frame = ttk.LabelFrame(self, text="Carrito de Compras", style="TLabelframe")
        cart_frame.grid(row=1, column=1, padx=(5,10), pady=5, sticky="nsew")
        cart_frame.grid_rowconfigure(0, weight=1)
        cart_frame.grid_columnconfigure(0, weight=1)

        columnas = ("cant", "desc", "p_unit", "subtotal")
        self.tree = ttk.Treeview(cart_frame, columns=columnas, show="headings")
        self.tree.heading("cant", text="Cant.")
        self.tree.heading("desc", text="Descripción")
        self.tree.heading("p_unit", text="P. Unit.")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.column("cant", width=60, anchor="center")
        self.tree.column("p_unit", width=100, anchor="e")
        self.tree.column("subtotal", width=100, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(cart_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        left_frame = ttk.Frame(self, style="Content.TFrame")
        left_frame.grid(row=1, column=0, padx=(10,5), pady=5, sticky="nsew")
        left_frame.grid_rowconfigure(0, weight=1)

        resumen_frame = ttk.LabelFrame(left_frame, text="Resumen y Pago", style="TLabelframe")
        resumen_frame.grid(row=0, column=0, sticky="nsew")
        resumen_frame.grid_columnconfigure(0, weight=1)
        
        total_frame = ttk.Frame(resumen_frame, style="Content.TFrame")
        total_frame.pack(side="bottom", fill="x", pady=10, padx=10)
        total_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(total_frame, text="TOTAL:", font=("Helvetica", 18, "bold"), style="TLabel").grid(row=0, column=0, sticky="w")
        self.total_label = ttk.Label(total_frame, text="$ 0.00", font=("Helvetica", 18, "bold"), style="TLabel")
        self.total_label.grid(row=0, column=1, sticky="e")

        ttk.Button(total_frame, text="Finalizar Venta", style="Action.TButton", command=self.abrir_ventana_pago).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10,0))
        ttk.Button(total_frame, text="Cancelar", style="Action.TButton", command=self.limpiar_venta).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5,0))
        
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
            x = self.cliente_search_entry.winfo_x()
            y = self.cliente_search_entry.winfo_y() + self.cliente_search_entry.winfo_height()
            w = self.cliente_search_entry.winfo_width() + self.add_cliente_btn.winfo_width()
            self.cliente_results_listbox.place(in_=self.cliente_search_entry, x=0, y=self.cliente_search_entry.winfo_height(), w=w)
        else:
            self.cliente_results_listbox.place_forget()

    def seleccionar_cliente(self, cliente_info):
        self.cliente_actual = cliente_info
        self.cliente_search_var.set(self.cliente_actual[1])
        self.cliente_results_listbox.place_forget()
        self.articulo_search_entry.focus_set()

    def seleccionar_primer_cliente(self, event=None):
        if hasattr(self, 'cliente_results') and self.cliente_results:
            self.seleccionar_cliente(self.cliente_results[0])

    def seleccionar_cliente_de_lista(self, event=None):
        if hasattr(self, 'cliente_results'):
            seleccion = self.cliente_results_listbox.curselection()
            if seleccion:
                cliente_seleccionado = self.cliente_results[seleccion[0]]
                self.seleccionar_cliente(cliente_seleccionado)
            
    def crear_nuevo_cliente(self):
        VentanaCliente(self, on_success_callback=self.cliente_creado_exitosamente)

    def cliente_creado_exitosamente(self, cliente_datos):
        cliente_info = (
            cliente_datos.get('id'),
            cliente_datos.get('razon_social'),
            cliente_datos.get('cuit_dni')
        )
        if cliente_info[0]:
            self.seleccionar_cliente(cliente_info)

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
            self.carrito_items[item_id] = {'descripcion': descripcion, 'cantidad': cantidad, 'precio_unit': precio, 'unidad': unidad}
        self.actualizar_carrito_visual()

    def actualizar_carrito_visual(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        total_venta = 0.0
        for item_id, data in self.carrito_items.items():
            subtotal = data['cantidad'] * data['precio_unit']
            total_venta += subtotal
            vista_cantidad = f"{data['cantidad']:.2f}" if data['unidad'] == 'KG' else f"{int(data['cantidad'])}"
            vista_precio = f"${data['precio_unit']:.2f}"
            vista_subtotal = f"${subtotal:.2f}"
            self.tree.insert("", "end", iid=item_id, values=(vista_cantidad, data['descripcion'], vista_precio, vista_subtotal))
        self.total_label.config(text=f"$ {total_venta:.2f}")
    
    def limpiar_venta(self):
        self.carrito_items = {}
        self.cliente_actual = None
        self.cliente_search_var.set("Consumidor Final")
        self.actualizar_carrito_visual()

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
        total_venta = float(self.total_label.cget("text").replace("$", ""))
        
        cliente_id_a_guardar = self.cliente_actual[0] if self.cliente_actual else None
        
        if not cliente_id_a_guardar:
            consumidor_final = clientes_db.buscar_clientes_pos('Consumidor Final')
            if consumidor_final:
                cliente_id_a_guardar = consumidor_final[0][0]
            else:
                clientes_db.agregar_cliente({'razon_social': 'Consumidor Final'})
                consumidor_final = clientes_db.buscar_clientes_pos('Consumidor Final')
                if consumidor_final:
                    cliente_id_a_guardar = consumidor_final[0][0]
        
        datos_venta = {
            'cliente_id': cliente_id_a_guardar,
            'total': total_venta,
            'tipo_comprobante': 'Ticket',
            'caja_id': self.caja_actual_id
        }
        
        resultado = ventas_db.registrar_venta(datos_venta, self.carrito_items, pagos)
        
        if "exitosamente" in resultado:
            messagebox.showinfo("Venta Finalizada", resultado)
            self.limpiar_venta()
        else:
            messagebox.showerror("Error", resultado)