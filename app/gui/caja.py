import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import caja_db, config_db, proveedores_db
from datetime import datetime

class VentanaEgreso(tk.Toplevel):
    def __init__(self, parent, caja_id, callback_exito):
        super().__init__(parent)
        self.parent = parent
        self.caja_id = caja_id
        self.callback = callback_exito
        self.pagos_realizados = []

        self.title("Registrar Nuevo Egreso")
        self.geometry("750x600")
        self.transient(parent)
        self.grab_set()

        # --- Frame Principal ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)

        # --- Sección de Datos del Egreso ---
        datos_frame = ttk.LabelFrame(main_frame, text="Datos del Egreso", style="TLabelframe")
        datos_frame.pack(fill="x", padx=10, pady=5)
        datos_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(datos_frame, text="Tipo de Egreso:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tipo_egreso_combo = ttk.Combobox(datos_frame, values=["Pago de Impuestos", "Gastos Generales", "Consumibles", "Pago a Proveedor", "Retiro"], state='readonly')
        self.tipo_egreso_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.tipo_egreso_combo.bind("<<ComboboxSelected>>", self.toggle_vista_proveedor)

        ttk.Label(datos_frame, text="Detalle/Concepto:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.detalle_entry = ttk.Entry(datos_frame)
        self.detalle_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # --- Sección de Pago a Proveedores (Dinámica) ---
        self.proveedor_frame = ttk.LabelFrame(main_frame, text="Pago a Proveedor", style="TLabelframe")
        self.proveedor_frame.columnconfigure(1, weight=1)
        self.proveedor_frame.rowconfigure(1, weight=1)
        
        ttk.Label(self.proveedor_frame, text="Proveedor:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.proveedor_combo = ttk.Combobox(self.proveedor_frame, state='readonly', width=40)
        self.proveedor_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.proveedor_combo.bind("<<ComboboxSelected>>", self.cargar_facturas_proveedor)

        self.tree_facturas = ttk.Treeview(self.proveedor_frame, columns=("id", "fecha", "nro", "monto"), show="headings", selectmode="extended")
        self.tree_facturas.heading("id", text="ID")
        self.tree_facturas.heading("fecha", text="Fecha")
        self.tree_facturas.heading("nro", text="N° Factura")
        self.tree_facturas.heading("monto", text="Monto")
        self.tree_facturas.column("id", width=40)
        self.tree_facturas.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.tree_facturas.bind("<<TreeviewSelect>>", self.actualizar_monto_pago)
        
        # --- Sección para Agregar Pagos ---
        self.pago_frame = ttk.LabelFrame(main_frame, text="Forma de Pago", style="TLabelframe")
        self.pago_frame.pack(fill="x", padx=10, pady=5)
        self.pago_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(self.pago_frame, text="Importe Total Egreso:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.total_entry = ttk.Entry(self.pago_frame)
        self.total_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.total_entry.bind("<FocusOut>", lambda e: self.actualizar_resumen())
        self.total_entry.bind("<Return>", lambda e: self.actualizar_resumen())

        ttk.Label(self.pago_frame, text="Monto Pago Parcial:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.monto_pago_entry = ttk.Entry(self.pago_frame)
        self.monto_pago_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.pago_frame, text="Medio de Pago:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.medio_pago_combo = ttk.Combobox(self.pago_frame, state='readonly')
        self.medio_pago_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.medios_de_pago_data = config_db.obtener_medios_de_pago()
        self.medio_pago_combo['values'] = [m[1] for m in self.medios_de_pago_data]
        
        btn_agregar_pago = ttk.Button(self.pago_frame, text="Agregar Pago", command=self.agregar_pago)
        btn_agregar_pago.grid(row=3, column=1, padx=5, pady=5, sticky='e')

        # --- Sección de Resumen y Pagos ---
        resumen_frame = ttk.Frame(main_frame)
        resumen_frame.pack(fill='both', expand=True, padx=10, pady=5)
        resumen_frame.grid_columnconfigure(0, weight=1)
        resumen_frame.grid_rowconfigure(0, weight=1)

        lista_pagos_frame = ttk.LabelFrame(resumen_frame, text="Pagos a Registrar", style="TLabelframe")
        lista_pagos_frame.grid(row=0, column=0, sticky="nsew", pady=(0,10))
        lista_pagos_frame.grid_columnconfigure(0, weight=1)
        lista_pagos_frame.grid_rowconfigure(0, weight=1)

        self.tree_pagos = ttk.Treeview(lista_pagos_frame, columns=("medio", "monto"), show="headings")
        self.tree_pagos.heading("medio", text="Medio de Pago")
        self.tree_pagos.heading("monto", text="Monto")
        self.tree_pagos.column("monto", anchor='e')
        self.tree_pagos.pack(fill='both', expand=True)

        totales_frame = ttk.Frame(resumen_frame)
        totales_frame.grid(row=1, column=0, sticky="ew")
        totales_frame.columnconfigure(1, weight=1)
        ttk.Label(totales_frame, text="Restante por Pagar:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="e", padx=5)
        self.restante_label = ttk.Label(totales_frame, text="$ 0.00", font=("Helvetica", 10, "bold"), foreground="red")
        self.restante_label.grid(row=0, column=1, sticky="w", padx=5)

        self.btn_guardar = ttk.Button(main_frame, text="Guardar Egreso", command=self.guardar, state="disabled")
        self.btn_guardar.pack(pady=10, padx=10, fill="x")
        
        self.toggle_vista_proveedor()

    def toggle_vista_proveedor(self, event=None):
        if self.tipo_egreso_combo.get() == "Pago a Proveedor":
            self.proveedor_frame.pack(fill="both", expand=True, padx=10, pady=5)
            self.total_entry.config(state="readonly")
            self.proveedores_data = proveedores_db.obtener_todos_los_proveedores_para_reporte()
            self.proveedor_combo['values'] = [p[1] for p in self.proveedores_data]
            self.detalle_entry.delete(0, tk.END)
            self.detalle_entry.insert(0, "Pago según detalle de facturas")
        else:
            self.proveedor_frame.pack_forget()
            self.total_entry.config(state="normal")
            self.total_entry.delete(0, tk.END)
            self.detalle_entry.delete(0, tk.END)
        self.limpiar_pagos()

    def cargar_facturas_proveedor(self, event=None):
        for row in self.tree_facturas.get_children(): self.tree_facturas.delete(row)
        proveedor_nombre = self.proveedor_combo.get()
        proveedor_id = next((pid for pid, nombre in self.proveedores_data if nombre == proveedor_nombre), None)
        if proveedor_id:
            facturas = proveedores_db.obtener_compras_impagas(proveedor_id)
            for fact in facturas:
                self.tree_facturas.insert("", "end", values=fact)
        self.actualizar_monto_pago()
    
    def actualizar_monto_pago(self, event=None):
        monto_total = 0.0
        for selected_item in self.tree_facturas.selection():
            monto_total += float(self.tree_facturas.item(selected_item, "values")[3])
        
        self.total_entry.config(state="normal")
        self.total_entry.delete(0, tk.END)
        self.total_entry.insert(0, f"{monto_total:.2f}")
        self.total_entry.config(state="readonly")
        self.limpiar_pagos()
        self.actualizar_resumen()
        
    def limpiar_pagos(self):
        self.pagos_realizados = []
        for row in self.tree_pagos.get_children(): self.tree_pagos.delete(row)
        self.monto_pago_entry.delete(0, tk.END)
        self.actualizar_resumen()
    
    def actualizar_resumen(self, event=None):
        try:
            total_a_pagar = float(self.total_entry.get() or 0)
        except ValueError:
            self.restante_label.config(text="Importe Total Inválido")
            return
        
        total_pagado = sum(p['monto'] for p in self.pagos_realizados)
        restante = total_a_pagar - total_pagado
        
        self.restante_label.config(text=f"$ {restante:.2f}")

        if restante <= 0.01 and total_a_pagar > 0:
            self.restante_label.config(foreground="green")
            self.btn_guardar.config(state="normal")
        else:
            self.restante_label.config(foreground="red")
            self.btn_guardar.config(state="disabled")
            
    def agregar_pago(self):
        try:
            monto = float(self.monto_pago_entry.get())
            if monto <= 0:
                messagebox.showwarning("Dato Inválido", "El monto debe ser positivo.", parent=self)
                return
        except ValueError:
            messagebox.showwarning("Dato Inválido", "Ingrese un monto numérico.", parent=self)
            return

        medio_pago_nombre = self.medio_pago_combo.get()
        if not medio_pago_nombre:
            messagebox.showwarning("Dato Faltante", "Seleccione un medio de pago.", parent=self)
            return
            
        medio_pago_id = next(mid for mid, nombre in self.medios_de_pago_data if nombre == medio_pago_nombre)
        self.pagos_realizados.append({'medio_pago_id': medio_pago_id, 'monto': monto, 'nombre': medio_pago_nombre})
        self.tree_pagos.insert("", "end", values=(medio_pago_nombre, f"$ {monto:.2f}"))
        self.monto_pago_entry.delete(0, tk.END)
        self.actualizar_resumen()

    def guardar(self):
        if self.tipo_egreso_combo.get() == "Pago a Proveedor":
            self.guardar_pago_proveedor()
        else:
            self.guardar_egreso_simple()

    def guardar_pago_proveedor(self):
        selected_items = self.tree_facturas.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Seleccione al menos una factura para pagar.", parent=self)
            return
        
        compra_ids = [self.tree_facturas.item(item, "values")[0] for item in selected_items]
        proveedor_nombre = self.proveedor_combo.get()
        proveedor_id = next((pid for pid, nombre in self.proveedores_data if nombre == proveedor_nombre), None)
        
        resultado = proveedores_db.registrar_pago_a_proveedor(
            self.caja_id, proveedor_id, compra_ids, self.pagos_realizados,
            f"Pago facturas N° {compra_ids}", self.detalle_entry.get()
        )
        
        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

    def guardar_egreso_simple(self):
        concepto = f"{self.tipo_egreso_combo.get()} - Det: {self.detalle_entry.get()}"
        if not self.tipo_egreso_combo.get():
            messagebox.showwarning("Datos Faltantes", "Debe especificar un Tipo de Egreso.", parent=self)
            return

        for pago in self.pagos_realizados:
            datos_movimiento = {
                'caja_id': self.caja_id, 'tipo': 'EGRESO', 'concepto': concepto,
                'monto': pago['monto'], 'medio_pago_id': pago['medio_pago_id']
            }
            caja_db.registrar_movimiento_caja(datos_movimiento)
        
        messagebox.showinfo("Éxito", "Egreso registrado correctamente.", parent=self)
        self.callback()
        self.destroy()

class CajaFrame(ttk.Frame):
    def __init__(self, parent, style, callback_actualizar_estado):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.callback_actualizar_estado = callback_actualizar_estado
        self.caja_actual_id = None

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        estado_frame = ttk.LabelFrame(self, text="Estado de Caja", style="TLabelframe")
        estado_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Label(estado_frame, text="Estado Actual:").pack(side="left", padx=10, pady=10)
        self.estado_label = ttk.Label(estado_frame, text="CERRADA", font=("Helvetica", 12, "bold"), foreground="red")
        self.estado_label.pack(side="left", padx=10, pady=10)
        
        self.boton_apertura = ttk.Button(estado_frame, text="Abrir Caja", style="Action.TButton", command=self.abrir_caja)
        self.boton_apertura.pack(side="right", padx=10, pady=10)
        self.boton_cierre = ttk.Button(estado_frame, text="Cerrar Caja", style="Action.TButton", command=self.cerrar_caja)
        self.boton_cierre.pack(side="right", padx=10, pady=10)
        
        movimientos_frame = ttk.LabelFrame(self, text="Movimientos del Día", style="TLabelframe")
        movimientos_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,5), sticky="nsew")
        movimientos_frame.grid_rowconfigure(0, weight=1)
        movimientos_frame.grid_columnconfigure(0, weight=1)

        columnas = ("id", "fecha", "tipo", "concepto", "monto", "medio_pago")
        self.tree = ttk.Treeview(movimientos_frame, columns=columnas, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("fecha", text="Fecha y Hora")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("concepto", text="Concepto")
        self.tree.heading("monto", text="Monto")
        self.tree.heading("medio_pago", text="Medio de Pago")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("monto", anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(movimientos_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        acciones_mov_frame = ttk.Frame(self, style="Content.TFrame")
        acciones_mov_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(0,10), sticky="ew")
        
        self.boton_egreso = ttk.Button(acciones_mov_frame, text="Registrar Egreso", style="Action.TButton", command=self.registrar_egreso)
        self.boton_egreso.pack(side="left", padx=(0,5))
        self.boton_eliminar_mov = ttk.Button(acciones_mov_frame, text="Eliminar Movimiento", style="Action.TButton", command=self.eliminar_movimiento)
        self.boton_eliminar_mov.pack(side="left")

        totales_frame = ttk.LabelFrame(self, text="Resumen de Caja", style="TLabelframe")
        totales_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        totales_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(totales_frame, text="Monto Inicial:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.monto_inicial_label = ttk.Label(totales_frame, text="$ 0.00")
        self.monto_inicial_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        ttk.Label(totales_frame, text="Total Ingresos:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.total_ingresos_label = ttk.Label(totales_frame, text="$ 0.00")
        self.total_ingresos_label.grid(row=1, column=1, padx=10, pady=5, sticky="e")
        ttk.Label(totales_frame, text="Total Egresos:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.total_egresos_label = ttk.Label(totales_frame, text="$ 0.00")
        self.total_egresos_label.grid(row=2, column=1, padx=10, pady=5, sticky="e")
        ttk.Label(totales_frame, text="Saldo Esperado:", font=("Helvetica", 10, "bold")).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.saldo_esperado_label = ttk.Label(totales_frame, text="$ 0.00", font=("Helvetica", 10, "bold"))
        self.saldo_esperado_label.grid(row=3, column=1, padx=10, pady=10, sticky="e")

        self.verificar_estado_caja()

    def verificar_estado_caja(self):
        caja_abierta = caja_db.obtener_estado_caja()
        if caja_abierta:
            self.caja_actual_id, fecha_apertura, monto_inicial = caja_abierta
            self.estado_label.config(text="ABIERTA", foreground="green")
            self.boton_apertura.config(state="disabled")
            self.boton_cierre.config(state="normal")
            self.boton_egreso.config(state="normal")
            self.boton_eliminar_mov.config(state="normal")
            self.monto_inicial_label.config(text=f"$ {monto_inicial:.2f}")
            self.actualizar_resumen()
        else:
            self.caja_actual_id = None
            self.estado_label.config(text="CERRADA", foreground="red")
            self.boton_apertura.config(state="normal")
            self.boton_cierre.config(state="disabled")
            self.boton_egreso.config(state="disabled")
            self.boton_eliminar_mov.config(state="disabled")
            self.limpiar_vista()
        self.callback_actualizar_estado(self.caja_actual_id)

    def abrir_caja(self):
        monto_inicial = simpledialog.askfloat("Apertura de Caja", "Ingrese el monto inicial:", parent=self, minvalue=0.0)
        if monto_inicial is not None:
            resultado = caja_db.abrir_caja(monto_inicial)
            if "exitosamente" in resultado:
                self.verificar_estado_caja()
            else:
                messagebox.showerror("Error", resultado)
    
    def cerrar_caja(self):
        saldo_esperado_str = self.saldo_esperado_label.cget("text").replace("$", "").strip()
        saldo_esperado = float(saldo_esperado_str)
        monto_real = simpledialog.askfloat("Cierre de Caja", f"El saldo esperado es ${saldo_esperado:.2f}\n\nIngrese el monto final real en caja:", parent=self)
        if monto_real is not None:
            diferencia = monto_real - saldo_esperado
            resultado = caja_db.cerrar_caja(self.caja_actual_id, monto_real, saldo_esperado, diferencia)
            if "exitosamente" in resultado:
                messagebox.showinfo("Caja Cerrada", f"La caja ha sido cerrada.\nDiferencia: ${diferencia:.2f}")
                self.verificar_estado_caja()
            else:
                messagebox.showerror("Error", resultado)

    def registrar_egreso(self):
        VentanaEgreso(self, self.caja_actual_id, callback_exito=self.verificar_estado_caja)

    def eliminar_movimiento(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un movimiento de la lista para eliminar.")
            return
        
        movimiento_id = self.tree.item(selected_item, "values")[0]
        
        if messagebox.askyesno("Confirmar Eliminación", "¿Está seguro de que desea eliminar este movimiento? Esta acción no se puede deshacer."):
            resultado = caja_db.eliminar_movimiento_caja(movimiento_id)
            if "correctamente" in resultado:
                messagebox.showinfo("Éxito", resultado)
                self.actualizar_resumen()
            else:
                messagebox.showerror("Error", resultado)

    def actualizar_resumen(self):
        if not self.caja_actual_id: return
        movimientos = caja_db.obtener_movimientos(self.caja_actual_id)
        for row in self.tree.get_children(): self.tree.delete(row)

        total_ingresos = 0
        total_egresos = 0
        for mov in movimientos:
            mov_id, fecha, tipo, concepto, monto, medio_pago = mov
            try:
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S.%f')
                fecha_formateada = fecha_obj.strftime('%d/%m/%Y %H:%M')
            except (ValueError, TypeError):
                fecha_formateada = fecha

            self.tree.insert("", "end", values=(mov_id, fecha_formateada, tipo, concepto, f"$ {monto:.2f}", medio_pago or ""))
            if tipo == 'INGRESO':
                total_ingresos += monto
            elif tipo == 'EGRESO':
                total_egresos += monto
        
        monto_inicial_str = self.monto_inicial_label.cget("text").replace("$", "").strip()
        monto_inicial = float(monto_inicial_str)
        saldo_esperado = monto_inicial + total_ingresos - total_egresos

        self.total_ingresos_label.config(text=f"$ {total_ingresos:.2f}")
        self.total_egresos_label.config(text=f"$ {total_egresos:.2f}")
        self.saldo_esperado_label.config(text=f"$ {saldo_esperado:.2f}")

    def limpiar_vista(self):
        self.monto_inicial_label.config(text="$ 0.00")
        self.total_ingresos_label.config(text="$ 0.00")
        self.total_egresos_label.config(text="$ 0.00")
        self.saldo_esperado_label.config(text="$ 0.00")
        for row in self.tree.get_children():
            self.tree.delete(row)