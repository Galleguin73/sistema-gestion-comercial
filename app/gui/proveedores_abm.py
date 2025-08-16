import tkinter as tk
from tkinter import ttk, messagebox
from app.database import proveedores_db, compras_db, config_db, caja_db
from tkcalendar import DateEntry
from datetime import datetime

class VentanaProveedor(tk.Toplevel):
    def __init__(self, parent, proveedor_id=None):
        super().__init__(parent)
        self.parent = parent
        self.proveedor_id = proveedor_id

        titulo = "Editar Proveedor" if self.proveedor_id else "Agregar Nuevo Proveedor"
        self.title(titulo)
        self.geometry("600x450")
        self.transient(parent)
        self.grab_set()

        self.frame = ttk.Frame(self, padding="10")
        self.frame.pack(fill='both', expand=True)
        self.frame.grid_columnconfigure(1, weight=1)

        self.entries = {}
        row_num = 0

        ttk.Label(self.frame, text="Razón Social:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['razon_social'] = ttk.Entry(self.frame)
        self.entries['razon_social'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        row_num += 1
        
        ttk.Label(self.frame, text="CUIT/DNI:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['cuit_dni'] = ttk.Entry(self.frame)
        self.entries['cuit_dni'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        row_num += 1

        ttk.Label(self.frame, text="Condición IVA:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['condicion_iva'] = ttk.Combobox(self.frame, values=["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"], state="readonly")
        self.entries['condicion_iva'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        row_num += 1

        campos_restantes = [
            ("Domicilio:", 'domicilio'), ("Localidad:", 'localidad'),
            ("Provincia:", 'provincia'), ("Email:", 'email'),
            ("Teléfono:", 'telefono'), ("Contacto:", 'persona_de_contacto'),
            ("Observaciones:", 'observaciones')
        ]
        
        for texto, clave in campos_restantes:
            label = ttk.Label(self.frame, text=texto)
            label.grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(self.frame, width=50)
            entry.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
            self.entries[clave] = entry
            row_num += 1
        
        self.save_btn = ttk.Button(self.frame, text="Guardar", command=self.guardar)
        self.save_btn.grid(row=row_num, column=0, columnspan=2, pady=10, padx=5, sticky="ew")

        if self.proveedor_id:
            self.cargar_datos_proveedor()

    def cargar_datos_proveedor(self):
        proveedor = proveedores_db.obtener_proveedor_por_id(self.proveedor_id)
        if proveedor:
            keys = proveedores_db.get_proveedor_column_names()
            proveedor_dict = dict(zip(keys, proveedor))
            for clave, entry in self.entries.items():
                valor = proveedor_dict.get(clave, "") or ""
                if isinstance(entry, ttk.Combobox):
                    entry.set(valor)
                else:
                    entry.insert(0, valor)

    def guardar(self):
        datos = {clave: entry.get() for clave, entry in self.entries.items()}
        
        if not datos.get("razon_social"):
            messagebox.showwarning("Campo Vacío", "La Razón Social es obligatoria.", parent=self)
            return
            
        if self.proveedor_id:
            datos['id'] = self.proveedor_id
            resultado = proveedores_db.modificar_proveedor(datos)
        else:
            resultado = proveedores_db.agregar_proveedor(datos)

        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            self.parent.actualizar_lista()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

class VentanaPagoCtaCte(tk.Toplevel):
    def __init__(self, parent, proveedor_info, caja_id, callback_exito):
        super().__init__(parent)
        self.parent = parent
        self.proveedor_id = proveedor_info[0]
        self.proveedor_nombre = proveedor_info[1]
        self.caja_id = caja_id
        self.callback = callback_exito
        self.pagos_realizados = []

        self.title(f"Registrar Pago a {self.proveedor_nombre}")
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
        ttk.Label(resumen_frame, text="Total a Pagar:", font=("Helvetica", 12, "bold")).grid(row=0, column=0, sticky='w')
        self.total_a_pagar_entry = ttk.Entry(resumen_frame, font=("Helvetica", 12, "bold"))
        self.total_a_pagar_entry.grid(row=0, column=1, sticky='e')
        self.total_a_pagar_entry.bind("<KeyRelease>", self.actualizar_resumen)
        
        ttk.Label(resumen_frame, text="Restante:", font=("Helvetica", 12, "bold")).grid(row=1, column=0, sticky='w')
        self.restante_label = ttk.Label(resumen_frame, text="$ 0.00", font=("Helvetica", 12, "bold"), foreground="red")
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

        self.tree_pagos = ttk.Treeview(lista_frame, columns=("medio", "monto"), show="headings")
        self.tree_pagos.heading("medio", text="Medio de Pago")
        self.tree_pagos.heading("monto", text="Monto")
        self.tree_pagos.column("monto", anchor='e')
        self.tree_pagos.grid(row=0, column=0, sticky='nsew')

        self.btn_confirmar = ttk.Button(self.frame, text="Confirmar Pago", command=self.confirmar, state="disabled")
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
        self.tree_pagos.insert("", "end", values=(medio_pago_nombre, f"$ {monto:.2f}"))
        self.monto_entry.delete(0, tk.END)
        self.actualizar_resumen()
        
    def actualizar_resumen(self, event=None):
        try:
            total_a_pagar = float(self.total_a_pagar_entry.get() or 0)
        except ValueError:
            total_a_pagar = 0
        
        total_pagado = sum(p['monto'] for p in self.pagos_realizados)
        restante = total_a_pagar - total_pagado
        
        self.restante_label.config(text=f"$ {restante:.2f}")

        if abs(restante) < 0.01 and total_a_pagar > 0:
            self.restante_label.config(foreground="green", text="$ 0.00")
            self.btn_confirmar.config(state="normal")
        else:
            self.restante_label.config(foreground="red")
            self.btn_confirmar.config(state="disabled")

    def confirmar(self):
        concepto = f"Pago a Cta. Cte. de Proveedor: {self.proveedor_nombre}"
        resultado = proveedores_db.registrar_pago_cuenta_corriente(self.caja_id, self.proveedor_id, self.pagos_realizados, concepto)
        
        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self.parent)
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

class ProveedoresFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        filtros_frame = ttk.Frame(self, style="Content.TFrame")
        filtros_frame.grid(row=0, column=0, padx=10, pady=(10,0), sticky="ew")
        
        ttk.Label(filtros_frame, text="Buscar Proveedor:").pack(side="left", padx=(0,5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda name, index, mode: self.actualizar_lista())
        search_entry = ttk.Entry(filtros_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", fill="x", expand=True)

        self.tree_frame = ttk.Frame(self, style="Content.TFrame")
        self.tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        
        columnas = ("id", "razon_social", "cuit_dni", "telefono")
        self.tree = ttk.Treeview(self.tree_frame, columns=columnas, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("razon_social", text="Razón Social")
        self.tree.heading("cuit_dni", text="CUIT/DNI")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.column("id", width=50, anchor='center')
        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind("<Double-1>", self.abrir_ventana_edicion)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.button_frame = ttk.Frame(self, style="Content.TFrame")
        self.button_frame.grid(row=1, column=1, padx=10, pady=10, sticky="ns")

        self.add_btn = ttk.Button(self.button_frame, text="Agregar Nuevo", command=self.abrir_ventana_creacion, style="Action.TButton")
        self.add_btn.pack(pady=5, fill='x')
        self.update_btn = ttk.Button(self.button_frame, text="Modificar", command=self.abrir_ventana_edicion, style="Action.TButton")
        self.update_btn.pack(pady=5, fill='x')
        self.delete_btn = ttk.Button(self.button_frame, text="Eliminar", command=self.eliminar_proveedor, style="Action.TButton")
        self.delete_btn.pack(pady=5, fill='x')
        self.history_btn = ttk.Button(self.button_frame, text="Ver Historial", command=self.ver_historial_proveedor, style="Action.TButton")
        self.history_btn.pack(pady=5, fill='x')
        self.pago_cta_cte_btn = ttk.Button(self.button_frame, text="Registrar Pago Cta. Cte.", command=self.registrar_pago_cta_cte, style="Action.TButton")
        self.pago_cta_cte_btn.pack(pady=5, fill='x')

        self.actualizar_lista()

    def actualizar_lista(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        criterio = self.search_var.get()
        proveedores = proveedores_db.obtener_proveedores(criterio=criterio)
        for proveedor in proveedores:
            self.tree.insert("", "end", values=proveedor)

    def abrir_ventana_creacion(self):
        VentanaProveedor(self)

    def abrir_ventana_edicion(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un proveedor de la lista.")
            return
        proveedor_id = self.tree.item(selected_item, "values")[0]
        VentanaProveedor(self, proveedor_id=proveedor_id)

    def eliminar_proveedor(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un proveedor de la lista.")
            return
        proveedor_id = self.tree.item(selected_item, "values")[0]
        razon_social = self.tree.item(selected_item, "values")[1]
        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar a '{razon_social}'?"):
            proveedores_db.eliminar_proveedor(proveedor_id)
            self.actualizar_lista()
            
    def ver_historial_proveedor(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un proveedor de la lista.")
            return

        values = self.tree.item(selected_item, "values")
        proveedor_id, proveedor_nombre = values[0], values[1]

        historial_window = tk.Toplevel(self)
        historial_window.title(f"Historial de Compras - {proveedor_nombre}")
        historial_window.transient(self)
        historial_window.grab_set()

        filtros_frame = ttk.Frame(historial_window, padding="10")
        filtros_frame.pack(fill="x")
        ttk.Label(filtros_frame, text="Desde:").pack(side="left", padx=(0,5))
        fecha_desde_entry = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12)
        fecha_desde_entry.pack(side="left", padx=5)
        ttk.Label(filtros_frame, text="Hasta:").pack(side="left", padx=5)
        fecha_hasta_entry = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12)
        fecha_hasta_entry.pack(side="left", padx=5)
        
        tree_frame = ttk.Frame(historial_window)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columnas = ("id", "fecha", "nro", "total", "estado")
        tree_historial = ttk.Treeview(tree_frame, columns=columnas, show="headings", displaycolumns=("fecha", "nro", "total", "estado"))
        tree_historial.heading("fecha", text="Fecha")
        tree_historial.heading("nro", text="N° Factura")
        tree_historial.heading("total", text="Monto Total")
        tree_historial.heading("estado", text="Estado")
        tree_historial.column("total", anchor="e")
        tree_historial.pack(side="left", fill="both", expand=True)

        scrollbar_historial = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_historial.yview)
        scrollbar_historial.pack(side='right', fill='y')
        tree_historial.configure(yscrollcommand=scrollbar_historial.set)

        def cargar_historial():
            for row in tree_historial.get_children():
                tree_historial.delete(row)
            
            desde = fecha_desde_entry.get() if fecha_desde_entry.get_date() else None
            hasta = fecha_hasta_entry.get() if fecha_hasta_entry.get_date() else None
            
            compras = compras_db.obtener_compras_por_proveedor(proveedor_id, desde, hasta)
            for compra in compras:
                id_compra, fecha, nro_factura, monto_total, estado = compra
                valores_formateados = (id_compra, fecha, nro_factura, f"$ {monto_total:.2f}", estado)
                tree_historial.insert("", "end", values=valores_formateados)
        
        ttk.Button(filtros_frame, text="Filtrar", command=cargar_historial).pack(side="left", padx=10)

        fecha_desde_entry.set_date(None)
        fecha_hasta_entry.set_date(None)
        cargar_historial()

    def registrar_pago_cta_cte(self):
        caja_abierta = caja_db.obtener_estado_caja()
        if not caja_abierta:
            messagebox.showerror("Caja Cerrada", "Debe abrir la caja para registrar un pago.", parent=self)
            return

        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un proveedor de la lista.", parent=self)
            return
            
        values = self.tree.item(selected_item, "values")
        proveedor_info = (values[0], values[1]) # (id, razon_social)
        
        VentanaPagoCtaCte(self, proveedor_info, caja_abierta[0], self.actualizar_lista)