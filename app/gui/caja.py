import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import caja_db, config_db, proveedores_db
from datetime import datetime
from collections import defaultdict
from .cierre_caja_window import VentanaCierreCaja
from .mixins.locale_validation_mixin import LocaleValidationMixin

class VentanaEgreso(tk.Toplevel):
    def __init__(self, parent, caja_id, callback_exito):
        super().__init__(parent)
        self.parent = parent
        self.caja_id = caja_id
        self.callback_exito = callback_exito
        self.pagos_realizados = []

        self.title("Registrar Nuevo Egreso")
        self.geometry("1000x650") 
        self.transient(parent)
        self.grab_set()

        # Definimos los estilos que usaremos en esta ventana
        style = ttk.Style(self)
        style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nsew")

        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, pady=5, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # --- Sección Datos del Egreso ---
        datos_container = ttk.Frame(left_frame, style="ContentPane.TFrame")
        datos_container.pack(fill="x", padx=10, pady=5)
        ttk.Label(datos_container, text="Datos del Egreso", style="SectionTitle.TLabel").pack(fill="x")
        datos_frame = ttk.Frame(datos_container, padding=5)
        datos_frame.pack(fill="x")
        datos_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(datos_frame, text="Tipo de Egreso:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tipo_egreso_combo = ttk.Combobox(datos_frame, values=["Pago de Impuestos", "Gastos Generales", "Consumibles", "Pago a Proveedor", "Retiro"], state='readonly')
        self.tipo_egreso_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.tipo_egreso_combo.bind("<<ComboboxSelected>>", self.toggle_vista_proveedor)

        ttk.Label(datos_frame, text="Detalle/Concepto:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.detalle_entry = ttk.Entry(datos_frame)
        self.detalle_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # --- Sección Forma de Pago ---
        pago_container = ttk.Frame(left_frame, style="ContentPane.TFrame")
        pago_container.pack(fill="x", padx=10, pady=(20,5))
        ttk.Label(pago_container, text="Forma de Pago", style="SectionTitle.TLabel").pack(fill="x")
        self.pago_frame = ttk.Frame(pago_container, padding=5)
        self.pago_frame.pack(fill="x")
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
        
        self.btn_guardar = ttk.Button(left_frame, text="Guardar Egreso", command=self.guardar, state="disabled")
        self.btn_guardar.pack(pady=20, padx=10, fill="x")

        # --- Sección Pago a Proveedor ---
        proveedor_container = ttk.Frame(right_frame, style="ContentPane.TFrame")
        proveedor_container.grid(row=0, column=0, sticky="nsew")
        proveedor_container.columnconfigure(0, weight=1)
        proveedor_container.rowconfigure(1, weight=1)
        ttk.Label(proveedor_container, text="Pago a Proveedor", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        self.proveedor_frame = ttk.Frame(proveedor_container, padding=5)
        self.proveedor_frame.grid(row=1, column=0, sticky="nsew")
        self.proveedor_frame.columnconfigure(1, weight=1)
        self.proveedor_frame.rowconfigure(1, weight=1)
        
        ttk.Label(self.proveedor_frame, text="Proveedor:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.proveedor_combo = ttk.Combobox(self.proveedor_frame, state='readonly', width=40)
        self.proveedor_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.proveedor_combo.bind("<<ComboboxSelected>>", self.cargar_facturas_proveedor)

        self.tree_facturas = ttk.Treeview(self.proveedor_frame, columns=("id", "fecha", "nro", "monto"), show="headings", selectmode="extended")
        self.tree_facturas.heading("id", text="ID"); self.tree_facturas.heading("fecha", text="Fecha"); self.tree_facturas.heading("nro", text="N° Factura"); self.tree_facturas.heading("monto", text="Monto")
        self.tree_facturas.column("id", width=40)
        self.tree_facturas.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.tree_facturas.bind("<<TreeviewSelect>>", self.actualizar_monto_pago)

        resumen_frame = ttk.Frame(right_frame)
        resumen_frame.grid(row=1, column=0, sticky="nsew", pady=(10,0))
        resumen_frame.grid_columnconfigure(0, weight=1)
        resumen_frame.grid_rowconfigure(0, weight=1)

        # --- Sección Pagos a Registrar ---
        lista_pagos_container = ttk.Frame(resumen_frame, style="ContentPane.TFrame")
        lista_pagos_container.grid(row=0, column=0, sticky="nsew", pady=(0,10))
        lista_pagos_container.grid_columnconfigure(0, weight=1); lista_pagos_container.grid_rowconfigure(1, weight=1)
        ttk.Label(lista_pagos_container, text="Pagos a Registrar", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        lista_pagos_frame = ttk.Frame(lista_pagos_container, padding=5)
        lista_pagos_frame.grid(row=1, column=0, sticky="nsew")
        lista_pagos_frame.grid_rowconfigure(0, weight=1); lista_pagos_frame.grid_columnconfigure(0, weight=1)

        self.tree_pagos = ttk.Treeview(lista_pagos_frame, columns=("medio", "monto"), show="headings")
        self.tree_pagos.heading("medio", text="Medio de Pago"); self.tree_pagos.heading("monto", text="Monto"); self.tree_pagos.column("monto", anchor='e')
        self.tree_pagos.pack(fill='both', expand=True, side='top') # pack is ok here

        pagos_actions_frame = ttk.Frame(lista_pagos_frame)
        pagos_actions_frame.pack(fill='x', pady=5)
        btn_editar_pago = ttk.Button(pagos_actions_frame, text="Editar Pago", command=self.editar_pago_seleccionado); btn_editar_pago.pack(side="left", padx=5)
        btn_quitar_pago = ttk.Button(pagos_actions_frame, text="Quitar Pago", command=self.quitar_pago_seleccionado); btn_quitar_pago.pack(side="left", padx=5)

        totales_frame = ttk.Frame(resumen_frame)
        totales_frame.grid(row=1, column=0, sticky="ew")
        totales_frame.columnconfigure(1, weight=1)
        ttk.Label(totales_frame, text="Restante por Pagar:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="e", padx=5)
        self.restante_label = ttk.Label(totales_frame, text="$ 0.00", font=("Helvetica", 10, "bold"), foreground="red")
        self.restante_label.grid(row=0, column=1, sticky="w", padx=5)
        
        self.tipo_egreso_combo.set("Pago a Proveedor")
        self.toggle_vista_proveedor()

    def toggle_vista_proveedor(self, event=None):
        if self.tipo_egreso_combo.get() == "Pago a Proveedor":
            self.proveedor_frame.master.grid()
            self.total_entry.config(state="readonly")
            self.proveedores_data = proveedores_db.obtener_todos_los_proveedores_para_reporte()
            self.proveedor_combo['values'] = [p[1] for p in self.proveedores_data]
            self.detalle_entry.delete(0, tk.END)
            self.detalle_entry.insert(0, "Pago según detalle de facturas")
        else:
            self.proveedor_frame.master.grid_remove()
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
        self.limpiar_pagos(); self.actualizar_resumen()
        
    def limpiar_pagos(self):
        self.pagos_realizados = []
        for row in self.tree_pagos.get_children(): self.tree_pagos.delete(row)
        self.monto_pago_entry.delete(0, tk.END); self.actualizar_resumen()
    
    def actualizar_resumen(self, event=None):
        try: total_a_pagar = float(self.total_entry.get() or 0)
        except ValueError: self.restante_label.config(text="Importe Total Inválido"); return
        total_pagado = sum(p['monto'] for p in self.pagos_realizados); restante = total_a_pagar - total_pagado
        self.restante_label.config(text=f"$ {restante:.2f}")
        if abs(restante) < 0.01 and total_a_pagar > 0:
            self.restante_label.config(foreground="green"); self.btn_guardar.config(state="normal")
        else:
            self.restante_label.config(foreground="red"); self.btn_guardar.config(state="disabled")
            
    def agregar_pago(self):
        try:
            monto = float(self.monto_pago_entry.get())
            if monto <= 0: messagebox.showwarning("Dato Inválido", "El monto debe ser positivo.", parent=self); return
        except ValueError: messagebox.showwarning("Dato Inválido", "Ingrese un monto numérico.", parent=self); return
        medio_pago_nombre = self.medio_pago_combo.get()
        if not medio_pago_nombre: messagebox.showwarning("Dato Faltante", "Seleccione un medio de pago.", parent=self); return
        medio_pago_id = next(mid for mid, nombre in self.medios_de_pago_data if nombre == medio_pago_nombre)
        self.pagos_realizados.append({'medio_pago_id': medio_pago_id, 'monto': monto, 'nombre': medio_pago_nombre})
        self.refrescar_arbol_pagos(); self.monto_pago_entry.delete(0, tk.END); self.actualizar_resumen()

    def refrescar_arbol_pagos(self):
        for row in self.tree_pagos.get_children(): self.tree_pagos.delete(row)
        for pago in self.pagos_realizados: self.tree_pagos.insert("", "end", values=(pago['nombre'], f"$ {pago['monto']:.2f}"))

    def quitar_pago_seleccionado(self):
        selected_item_id = self.tree_pagos.focus()
        if not selected_item_id: messagebox.showwarning("Sin Selección", "Seleccione un pago de la lista para quitar.", parent=self); return
        item_index = self.tree_pagos.index(selected_item_id)
        del self.pagos_realizados[item_index]
        self.refrescar_arbol_pagos(); self.actualizar_resumen()

    def editar_pago_seleccionado(self):
        selected_item_id = self.tree_pagos.focus()
        if not selected_item_id: messagebox.showwarning("Sin Selección", "Seleccione un pago de la lista para editar.", parent=self); return
        item_index = self.tree_pagos.index(selected_item_id); pago_actual = self.pagos_realizados[item_index]
        dialog = tk.Toplevel(self); dialog.title("Editar Pago"); dialog.geometry("350x150"); dialog.transient(self); dialog.grab_set()
        dialog_frame = ttk.Frame(dialog, padding="10"); dialog_frame.pack(fill='both', expand=True); dialog_frame.columnconfigure(1, weight=1)
        ttk.Label(dialog_frame, text="Monto:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        monto_entry = ttk.Entry(dialog_frame); monto_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew"); monto_entry.insert(0, f"{pago_actual['monto']:.2f}")
        ttk.Label(dialog_frame, text="Medio de Pago:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        medio_pago_combo = ttk.Combobox(dialog_frame, state='readonly', values=[m[1] for m in self.medios_de_pago_data])
        medio_pago_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew"); medio_pago_combo.set(pago_actual['nombre'])
        resultado_dialogo = {}
        def on_confirm():
            try:
                nuevo_monto = float(monto_entry.get())
                if nuevo_monto <= 0: messagebox.showerror("Error", "El monto debe ser positivo.", parent=dialog); return
            except ValueError: messagebox.showerror("Error", "El monto debe ser un número válido.", parent=dialog); return
            nuevo_medio_pago_nombre = medio_pago_combo.get()
            nuevo_medio_pago_id = next(mid for mid, nombre in self.medios_de_pago_data if nombre == nuevo_medio_pago_nombre)
            resultado_dialogo['monto'] = nuevo_monto; resultado_dialogo['nombre'] = nuevo_medio_pago_nombre; resultado_dialogo['medio_pago_id'] = nuevo_medio_pago_id
            dialog.destroy()
        btn_frame = ttk.Frame(dialog_frame); btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        confirm_button = ttk.Button(btn_frame, text="Guardar Cambios", command=on_confirm); confirm_button.pack(side="left", padx=5)
        cancel_button = ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy); cancel_button.pack(side="left", padx=5)
        self.wait_window(dialog)
        if resultado_dialogo:
            self.pagos_realizados[item_index] = resultado_dialogo; self.refrescar_arbol_pagos(); self.actualizar_resumen()

    def guardar(self):
        if self.tipo_egreso_combo.get() == "Pago a Proveedor": self.guardar_pago_proveedor()
        else: self.guardar_egreso_simple()

    def guardar_pago_proveedor(self):
        selected_items = self.tree_facturas.selection()
        if not selected_items: messagebox.showwarning("Sin Selección", "Seleccione al menos una factura para pagar.", parent=self); return
        compra_ids = [self.tree_facturas.item(item, "values")[0] for item in selected_items]
        proveedor_nombre = self.proveedor_combo.get()
        proveedor_id = next((pid for pid, nombre in self.proveedores_data if nombre == proveedor_nombre), None)
        resultado = proveedores_db.registrar_pago_a_proveedor(self.caja_id, proveedor_id, compra_ids, self.pagos_realizados, f"Pago facturas N° {compra_ids}", self.detalle_entry.get())
        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            if self.callback_exito: self.callback_exito()
            self.destroy()
        else: messagebox.showerror("Error", resultado, parent=self)

    def guardar_egreso_simple(self):
        concepto = f"{self.tipo_egreso_combo.get()} - Det: {self.detalle_entry.get()}"
        if not self.tipo_egreso_combo.get(): messagebox.showwarning("Datos Faltantes", "Debe especificar un Tipo de Egreso.", parent=self); return
        try:
            for pago in self.pagos_realizados:
                datos_movimiento = {'caja_id': self.caja_id, 'fecha': datetime.now(),'tipo': 'EGRESO', 'concepto': concepto,'monto': pago['monto'], 'medio_pago_id': pago['medio_pago_id']}
                caja_db.registrar_movimiento_caja(datos_movimiento)
            messagebox.showinfo("Éxito", "Egreso registrado correctamente.", parent=self)
            if self.callback_exito: self.callback_exito()
            self.destroy()
        except Exception as e: messagebox.showerror("Error", f"No se pudo registrar el egreso:\n{e}", parent=self)

class CajaFrame(ttk.Frame):
    def __init__(self, parent, style, callback_actualizar_estado):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.callback_actualizar_estado = callback_actualizar_estado
        self.caja_actual_id = None
        
        # Aplicamos los estilos que ya deben estar definidos en main_window
        self.style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        self.style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")

        self.grid_rowconfigure(0, weight=1) 
        self.grid_columnconfigure(0, weight=2, minsize=400)
        self.grid_columnconfigure(1, weight=1, minsize=350)

        left_column_frame = ttk.Frame(self)
        left_column_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_column_frame.grid_rowconfigure(0, weight=1)
        left_column_frame.grid_rowconfigure(1, weight=1)
        left_column_frame.grid_columnconfigure(0, weight=1)
        
        # --- Sección Movimientos (Ingresos) ---
        ingresos_container = ttk.Frame(left_column_frame, style="ContentPane.TFrame")
        ingresos_container.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        ingresos_container.grid_rowconfigure(1, weight=1); ingresos_container.grid_columnconfigure(0, weight=1)
        ttk.Label(ingresos_container, text="Movimientos del Día (Ingresos)", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        ingresos_frame = ttk.Frame(ingresos_container, padding=5)
        ingresos_frame.grid(row=1, column=0, sticky="nsew")
        ingresos_frame.grid_rowconfigure(0, weight=1); ingresos_frame.grid_columnconfigure(0, weight=1)

        columnas = ("mov_id", "fecha", "tipo", "concepto", "entidad", "monto", "medio_pago")
        self.tree_ingresos = ttk.Treeview(ingresos_frame, columns=columnas, show="headings")
        self.tree_ingresos.heading("fecha", text="Fecha y Hora"); self.tree_ingresos.heading("tipo", text="Tipo"); self.tree_ingresos.heading("concepto", text="Concepto"); self.tree_ingresos.heading("entidad", text="Cliente/Proveedor"); self.tree_ingresos.heading("monto", text="Monto"); self.tree_ingresos.heading("medio_pago", text="Medio de Pago")
        self.tree_ingresos.column("mov_id", width=0, stretch=tk.NO); self.tree_ingresos.column("fecha", width=120, anchor="w"); self.tree_ingresos.column("tipo", width=80, anchor="w"); self.tree_ingresos.column("monto", width=100, anchor="e"); self.tree_ingresos.column("medio_pago", width=110, anchor="w")
        self.tree_ingresos.grid(row=0, column=0, sticky="nsew")
        scrollbar_ingresos = ttk.Scrollbar(ingresos_frame, orient="vertical", command=self.tree_ingresos.yview)
        scrollbar_ingresos.grid(row=0, column=1, sticky="ns")
        self.tree_ingresos.configure(yscrollcommand=scrollbar_ingresos.set)

        # --- Sección Movimientos (Egresos) ---
        egresos_container = ttk.Frame(left_column_frame, style="ContentPane.TFrame")
        egresos_container.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        egresos_container.grid_rowconfigure(1, weight=1); egresos_container.grid_columnconfigure(0, weight=1)
        ttk.Label(egresos_container, text="Movimientos del Día (Egresos)", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        egresos_frame = ttk.Frame(egresos_container, padding=5)
        egresos_frame.grid(row=1, column=0, sticky="nsew")
        egresos_frame.grid_rowconfigure(0, weight=1); egresos_frame.grid_columnconfigure(0, weight=1)
        
        self.tree_egresos = ttk.Treeview(egresos_frame, columns=columnas, show="headings")
        self.tree_egresos.heading("fecha", text="Fecha y Hora"); self.tree_egresos.heading("tipo", text="Tipo"); self.tree_egresos.heading("concepto", text="Concepto"); self.tree_egresos.heading("entidad", text="Cliente/Proveedor"); self.tree_egresos.heading("monto", text="Monto"); self.tree_egresos.heading("medio_pago", text="Medio de Pago")
        self.tree_egresos.column("mov_id", width=0, stretch=tk.NO); self.tree_egresos.column("fecha", width=120, anchor="w"); self.tree_egresos.column("tipo", width=80, anchor="w"); self.tree_egresos.column("monto", width=100, anchor="e"); self.tree_egresos.column("medio_pago", width=110, anchor="w")
        self.tree_egresos.grid(row=0, column=0, sticky="nsew")
        scrollbar_egresos = ttk.Scrollbar(egresos_frame, orient="vertical", command=self.tree_egresos.yview)
        scrollbar_egresos.grid(row=0, column=1, sticky="ns")
        self.tree_egresos.configure(yscrollcommand=scrollbar_egresos.set)
        
        acciones_mov_frame = ttk.Frame(left_column_frame)
        acciones_mov_frame.grid(row=2, column=0, pady=10, sticky="ew")
        
        self.boton_egreso = ttk.Button(acciones_mov_frame, text="Registrar Egreso", style="Action.TButton", command=self.registrar_egreso)
        self.boton_egreso.pack(side="left", padx=(0,5))
        
        self.boton_anular_mov = ttk.Button(acciones_mov_frame, text="Anular Movimiento", style="Action.TButton", command=self.anular_movimiento_seleccionado)
        self.boton_anular_mov.pack(side="left")

        right_column_frame = ttk.Frame(self)
        right_column_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        right_column_frame.grid_rowconfigure(1, weight=1)
        right_column_frame.grid_columnconfigure(0, weight=1)

        # --- Sección Estado de Caja ---
        estado_container = ttk.Frame(right_column_frame, style="ContentPane.TFrame")
        estado_container.grid(row=0, column=0, pady=(0,10), sticky="ew")
        ttk.Label(estado_container, text="Estado de Caja", style="SectionTitle.TLabel").pack(fill="x")
        estado_frame = ttk.Frame(estado_container, padding=5)
        estado_frame.pack(fill="x")
        
        ttk.Label(estado_frame, text="Estado Actual:").pack(side="left", padx=10, pady=5)
        self.estado_label = ttk.Label(estado_frame, text="CERRADA", font=("Helvetica", 12, "bold"), foreground="red")
        self.estado_label.pack(side="left", padx=10, pady=5)
        
        self.boton_apertura = ttk.Button(estado_frame, text="Abrir Caja", style="Action.TButton", command=self.abrir_caja)
        self.boton_apertura.pack(side="right", padx=10, pady=5)
        self.boton_cierre = ttk.Button(estado_frame, text="Cerrar Caja", style="Action.TButton", command=self.cerrar_caja)
        self.boton_cierre.pack(side="right", padx=10, pady=5)

        # --- Sección Resumen de Caja ---
        totales_container = ttk.Frame(right_column_frame, style="ContentPane.TFrame")
        totales_container.grid(row=1, column=0, sticky="nsew")
        totales_container.grid_columnconfigure(0, weight=1); totales_container.grid_rowconfigure(1, weight=1)
        ttk.Label(totales_container, text="Resumen de Caja", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        totales_frame = ttk.Frame(totales_container, padding=5)
        totales_frame.grid(row=1, column=0, sticky="nsew")
        totales_frame.grid_columnconfigure(0, weight=1); totales_frame.grid_rowconfigure(2, weight=1)

        efectivo_frame = ttk.Frame(totales_frame)
        efectivo_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        efectivo_frame.columnconfigure(1, weight=1)
        ttk.Label(efectivo_frame, text="Monto Inicial (Efectivo):").grid(row=0, column=0, sticky="w")
        self.monto_inicial_label = ttk.Label(efectivo_frame, text="$ 0,00")
        self.monto_inicial_label.grid(row=0, column=1, sticky="e")
        
        ttk.Label(efectivo_frame, text="Saldo Esperado (Efectivo):", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky="w", pady=(10,0))
        self.saldo_esperado_label = ttk.Label(efectivo_frame, text="$ 0,00", font=("Helvetica", 12, "bold"))
        self.saldo_esperado_label.grid(row=1, column=1, sticky="e", pady=(10,0))
        
        ttk.Separator(totales_frame, orient='horizontal').grid(row=1, column=0, sticky='ew', pady=10, padx=10)

        self.tree_resumen = ttk.Treeview(totales_frame, columns=("medio_pago", "ingresos", "egresos", "neto"), show="headings")
        self.tree_resumen.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.tree_resumen.heading("medio_pago", text="Medio de Pago"); self.tree_resumen.heading("ingresos", text="Ingresos"); self.tree_resumen.heading("egresos", text="Egresos"); self.tree_resumen.heading("neto", text="Neto")
        self.tree_resumen.column("medio_pago", width=120); self.tree_resumen.column("ingresos", anchor="e", width=80); self.tree_resumen.column("egresos", anchor="e", width=80); self.tree_resumen.column("neto", anchor="e", width=80)
        
        self.verificar_estado_caja()

    def verificar_estado_caja(self):
        caja_abierta = caja_db.obtener_estado_caja()
        if caja_abierta:
            self.caja_actual_id, _, monto_inicial = caja_abierta
            self.estado_label.config(text="ABIERTA", foreground="green")
            self.boton_apertura.config(state="disabled"); self.boton_cierre.config(state="normal"); self.boton_egreso.config(state="normal"); self.boton_anular_mov.config(state="normal")
            self.monto_inicial_label.config(text=f"$ {LocaleValidationMixin._format_local_number(monto_inicial)}")
            self.actualizar_vista_completa()
        else:
            self.caja_actual_id = None
            self.estado_label.config(text="CERRADA", foreground="red")
            self.boton_apertura.config(state="normal"); self.boton_cierre.config(state="disabled"); self.boton_egreso.config(state="disabled"); self.boton_anular_mov.config(state="disabled")
            self.limpiar_vista()
        self.callback_actualizar_estado(self.caja_actual_id)
    
    def abrir_caja(self):
        monto_inicial = simpledialog.askfloat("Apertura de Caja", "Ingrese el monto inicial en EFECTIVO:", parent=self, minvalue=0.0)
        if monto_inicial is not None:
            resultado = caja_db.abrir_caja(monto_inicial)
            if "exitosamente" in resultado: self.verificar_estado_caja()
            else: messagebox.showerror("Error", resultado)
    
    def cerrar_caja(self):
        movimientos = caja_db.obtener_movimientos_consolidados(self.caja_actual_id)
        resumen = defaultdict(lambda: {'ingresos': 0.0, 'egresos': 0.0})
        for mov in movimientos:
            tipo, monto, medio_pago = mov[2], mov[5], mov[6]
            if tipo == 'INGRESO': resumen[medio_pago]['ingresos'] += monto
            elif tipo == 'EGRESO': resumen[medio_pago]['egresos'] += monto
        monto_inicial_float = LocaleValidationMixin._parse_local_number(self.monto_inicial_label.cget("text").replace("$", "").strip())
        VentanaCierreCaja(self, self.caja_actual_id, monto_inicial_float, resumen, self.verificar_estado_caja)

    def registrar_egreso(self):
        VentanaEgreso(self, self.caja_actual_id, callback_exito=self.actualizar_vista_completa)

    def anular_movimiento_seleccionado(self):
        selected_item = self.tree_ingresos.focus() or self.tree_egresos.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Por favor, seleccione un movimiento para anular."); return
        tree_seleccionado = self.tree_ingresos if self.tree_ingresos.exists(selected_item) else self.tree_egresos
        movimiento_id = tree_seleccionado.item(selected_item, "values")[0]
        if messagebox.askyesno("Confirmar Anulación", f"¿Está seguro de que desea anular el movimiento ID {movimiento_id}?\nSe creará un contraasiento de ajuste."):
            resultado = caja_db.anular_movimiento_caja(movimiento_id, self.caja_actual_id)
            if "correctamente" in resultado: messagebox.showinfo("Éxito", resultado); self.actualizar_vista_completa()
            else: messagebox.showerror("Error", resultado)

    def actualizar_vista_completa(self):
        if not self.caja_actual_id: return
        for tree in [self.tree_ingresos, self.tree_egresos, self.tree_resumen]:
            for row in tree.get_children():
                tree.delete(row)
        movimientos = caja_db.obtener_movimientos_consolidados(self.caja_actual_id)
        resumen = defaultdict(lambda: {'ingresos': 0.0, 'egresos': 0.0})
        for mov in movimientos:
            mov_id, fecha, tipo, concepto, entidad, monto, medio_pago = mov
            fecha_formateada = ""
            if fecha:
                try: fecha_formateada = datetime.strptime(fecha.split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                except ValueError: fecha_formateada = fecha
            else: fecha_formateada = "Sin fecha"
            monto_formateado = f"$ {LocaleValidationMixin._format_local_number(monto or 0.0)}"
            if tipo == 'INGRESO':
                self.tree_ingresos.insert("", "end", values=(mov_id, fecha_formateada, tipo, concepto, entidad or "", monto_formateado, medio_pago or ""))
                resumen[medio_pago]['ingresos'] += monto
            elif tipo == 'EGRESO':
                self.tree_egresos.insert("", "end", values=(mov_id, fecha_formateada, concepto.split('-')[0].strip(), entidad or "", monto_formateado, medio_pago or ""))
                resumen[medio_pago]['egresos'] += monto
        monto_inicial = LocaleValidationMixin._parse_local_number(self.monto_inicial_label.cget("text").replace("$", "").strip())
        for medio, totales in sorted(resumen.items()):
            ingresos, egresos = totales['ingresos'], totales['egresos']; neto = ingresos - egresos
            self.tree_resumen.insert("", "end", values=(medio or "N/A", f"$ {LocaleValidationMixin._format_local_number(ingresos)}", f"$ {LocaleValidationMixin._format_local_number(egresos)}", f"$ {LocaleValidationMixin._format_local_number(neto)}"))
        ingresos_efectivo = resumen.get('Efectivo', {}).get('ingresos', 0.0); egresos_efectivo = resumen.get('Efectivo', {}).get('egresos', 0.0)
        saldo_esperado_efectivo = (monto_inicial or 0.0) + ingresos_efectivo - egresos_efectivo
        self.saldo_esperado_label.config(text=f"$ {LocaleValidationMixin._format_local_number(saldo_esperado_efectivo)}")

    def limpiar_vista(self):
        self.monto_inicial_label.config(text="$ 0,00"); self.saldo_esperado_label.config(text="$ 0,00")
        for row in self.tree_ingresos.get_children(): self.tree_ingresos.delete(row)
        for row in self.tree_egresos.get_children(): self.tree_egresos.delete(row)
        for row in self.tree_resumen.get_children(): self.tree_resumen.delete(row)