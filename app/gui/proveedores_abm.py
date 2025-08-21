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
        self.title("Editar Proveedor" if self.proveedor_id else "Nuevo Proveedor")
        self.geometry("600x450")
        self.transient(parent); self.grab_set()
        self.frame = ttk.Frame(self, padding="10")
        self.frame.pack(fill='both', expand=True); self.frame.grid_columnconfigure(1, weight=1)
        self.entries = {}
        row_num = 0
        campos_restantes = [("Razón Social:", 'razon_social'),("CUIT/DNI:", 'cuit_dni'),("Condición IVA:", 'condicion_iva', ["Responsable Inscripto", "Monotributo", "Exento", "Consumidor Final"]),("Domicilio:", 'domicilio'), ("Localidad:", 'localidad'),("Provincia:", 'provincia'), ("Email:", 'email'),("Teléfono:", 'telefono'), ("Contacto:", 'persona_de_contacto'),("Observaciones:", 'observaciones')]
        for item in campos_restantes:
            texto, clave, *valores = item
            label = ttk.Label(self.frame, text=texto); label.grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
            if valores: entry = ttk.Combobox(self.frame, values=valores[0], state="readonly")
            else: entry = ttk.Entry(self.frame, width=50)
            entry.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
            self.entries[clave] = entry
            row_num += 1
        self.save_btn = ttk.Button(self.frame, text="Guardar", command=self.guardar, style="Action.TButton"); self.save_btn.grid(row=row_num, column=0, columnspan=2, pady=10, padx=5, sticky="ew")
        if self.proveedor_id: self.cargar_datos_proveedor()
    
    def cargar_datos_proveedor(self):
        proveedor = proveedores_db.obtener_proveedor_por_id(self.proveedor_id)
        if proveedor:
            keys = proveedores_db.get_proveedor_column_names()
            proveedor_dict = dict(zip(keys, proveedor))
            for clave, entry in self.entries.items():
                valor = proveedor_dict.get(clave, "") or ""
                if isinstance(entry, ttk.Combobox): entry.set(valor)
                else: entry.delete(0, tk.END); entry.insert(0, valor)

    def guardar(self):
        datos = {clave: entry.get() for clave, entry in self.entries.items()}
        if not datos.get("razon_social"): messagebox.showwarning("Campo Vacío", "La Razón Social es obligatoria.", parent=self); return
        if self.proveedor_id:
            datos['id'] = self.proveedor_id
            resultado = proveedores_db.modificar_proveedor(datos)
        else:
            resultado = proveedores_db.agregar_proveedor(datos)
        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            if hasattr(self.parent, 'actualizar_lista_proveedores'): self.parent.actualizar_lista_proveedores()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

class VentanaPagoCtaCte(tk.Toplevel):
    def __init__(self, parent, caja_id, proveedor_id, proveedor_nombre, ids_facturas):
        super().__init__(parent)
        self.parent = parent
        self.caja_id = caja_id
        self.proveedor_id = proveedor_id
        self.proveedor_nombre = proveedor_nombre
        self.ids_facturas = ids_facturas
        self.pagos_realizados = []

        self.title(f"Registrar Pago a {self.proveedor_nombre}")
        self.geometry("600x400")
        self.transient(parent); self.grab_set()

        frame = ttk.Frame(self, padding="10"); frame.pack(fill='both', expand=True); frame.grid_columnconfigure(0, weight=1); frame.grid_rowconfigure(1, weight=1)
        
        pago_frame = ttk.LabelFrame(frame, text="Agregar Medio de Pago", style="TLabelframe")
        pago_frame.grid(row=0, column=0, pady=5, sticky='nsew')
        pago_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(pago_frame, text="Monto a Pagar:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.monto_entry = ttk.Entry(pago_frame); self.monto_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        ttk.Label(pago_frame, text="Medio de Pago:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.medio_pago_combo = ttk.Combobox(pago_frame, state='readonly'); self.medio_pago_combo.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        self.medios_de_pago_data = config_db.obtener_medios_de_pago(); self.medio_pago_combo['values'] = [m[1] for m in self.medios_de_pago_data]
        
        btn_agregar_pago = ttk.Button(pago_frame, text="Agregar Pago", command=self.agregar_pago); btn_agregar_pago.grid(row=2, column=1, padx=5, pady=5, sticky='e')

        lista_frame = ttk.LabelFrame(frame, text="Pagos a Realizar", style="TLabelframe"); lista_frame.grid(row=1, column=0, pady=5, sticky='nsew'); lista_frame.grid_rowconfigure(0, weight=1); lista_frame.grid_columnconfigure(0, weight=1)
        self.tree_pagos = ttk.Treeview(lista_frame, columns=("medio", "monto"), show="headings"); self.tree_pagos.heading("medio", text="Medio de Pago"); self.tree_pagos.heading("monto", text="Monto"); self.tree_pagos.column("monto", anchor='e'); self.tree_pagos.grid(row=0, column=0, sticky='nsew')
        
        self.btn_confirmar = ttk.Button(frame, text="Confirmar y Registrar Pago", command=self.confirmar, state="disabled"); self.btn_confirmar.grid(row=2, column=0, pady=10, sticky='ew')
        
    def agregar_pago(self):
        try:
            monto = float(self.monto_entry.get()); medio_pago_nombre = self.medio_pago_combo.get()
            if not medio_pago_nombre: messagebox.showwarning("Dato Faltante", "Seleccione un medio de pago.", parent=self); return
            if monto <= 0: messagebox.showwarning("Dato Inválido", "El monto debe ser positivo.", parent=self); return
        except ValueError: messagebox.showwarning("Dato Inválido", "Ingrese un monto numérico.", parent=self); return
        medio_pago_id = next((mid for mid, nombre in self.medios_de_pago_data if nombre == medio_pago_nombre), None)
        self.pagos_realizados.append({'medio_pago_id': medio_pago_id, 'monto': monto})
        self.tree_pagos.insert("", "end", values=(medio_pago_nombre, f"$ {monto:.2f}"))
        self.monto_entry.delete(0, tk.END); self.medio_pago_combo.set('')
        self.btn_confirmar.config(state="normal")
        
    def confirmar(self):
        if not self.pagos_realizados:
            messagebox.showwarning("Sin Pagos", "Debe agregar al menos un medio de pago.", parent=self)
            return
        concepto = f"Pago Cta. Cte. a Proveedor: {self.proveedor_nombre}"
        resultado = proveedores_db.registrar_pago_a_facturas(self.caja_id, self.proveedor_id, self.pagos_realizados, self.ids_facturas, concepto)
        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self.parent)
            self.parent.actualizar_lista_ctas_pagar()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

class ProveedoresFrame(ttk.Frame):
    def __init__(self, parent, style, main_window):
        super().__init__(parent, style="Content.TFrame")
        self.style = style; self.main_window = main_window
        self.notebook = ttk.Notebook(self); self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.ctas_pagar_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.proveedores_list_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.resumen_cc_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(self.ctas_pagar_tab, text='Cuentas por Pagar')
        self.notebook.add(self.proveedores_list_tab, text='Listado de Proveedores')
        self.notebook.add(self.resumen_cc_tab, text='Resumen de Cuenta')
        self.crear_widgets_ctas_pagar()
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        selected_tab_index = self.notebook.index(self.notebook.select())
        if selected_tab_index == 1 and not self.proveedores_list_tab.winfo_children(): self.crear_widgets_proveedores_list()
        elif selected_tab_index == 2 and not self.resumen_cc_tab.winfo_children(): self.crear_widgets_resumen_cc()

    def crear_widgets_ctas_pagar(self):
        frame = self.ctas_pagar_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        filtros_frame = ttk.Frame(frame, style="Content.TFrame"); filtros_frame.grid(row=0, column=0, padx=0, pady=(0,5), sticky="ew")
        ttk.Label(filtros_frame, text="Buscar:").pack(side="left")
        self.search_var_ctas = tk.StringVar(); self.search_var_ctas.trace_add("write", lambda n,i,m: self.actualizar_lista_ctas_pagar())
        search_entry = ttk.Entry(filtros_frame, textvariable=self.search_var_ctas, width=40); search_entry.pack(side="left", fill="x", expand=True, padx=5)
        tree_frame = ttk.Frame(frame, style="Content.TFrame"); tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1); tree_frame.grid_columnconfigure(0, weight=1)
        columnas = ("id", "proveedor", "factura", "fecha_emision", "fecha_vto", "total", "saldo")
        self.tree_ctas_pagar = ttk.Treeview(tree_frame, columns=columnas, show="headings", selectmode="extended")
        self.tree_ctas_pagar.heading("proveedor", text="Proveedor"); self.tree_ctas_pagar.heading("factura", text="N° Factura"); self.tree_ctas_pagar.heading("fecha_emision", text="F. Emisión"); self.tree_ctas_pagar.heading("fecha_vto", text="F. Vencimiento"); self.tree_ctas_pagar.heading("total", text="Monto Original"); self.tree_ctas_pagar.heading("saldo", text="Saldo Pendiente")
        self.tree_ctas_pagar.column("id", width=0, stretch=tk.NO); self.tree_ctas_pagar.column("proveedor", width=250); self.tree_ctas_pagar.column("total", anchor="e"); self.tree_ctas_pagar.column("saldo", anchor="e")
        self.tree_ctas_pagar.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_ctas_pagar.yview); scrollbar.pack(side='right', fill='y'); self.tree_ctas_pagar.configure(yscrollcommand=scrollbar.set)
        summary_frame = ttk.Frame(frame); summary_frame.grid(row=2, column=0, sticky="ew", pady=(10,0)); summary_frame.columnconfigure(0, weight=1)
        ttk.Button(summary_frame, text="Registrar Pago de Factura(s) Seleccionada(s)", style="Action.TButton", command=self.registrar_pago).pack(side="left")
        self.total_deuda_label = ttk.Label(summary_frame, text="Deuda Total: $ 0.00", font=("Helvetica", 11, "bold")); self.total_deuda_label.pack(side="right")
        self.actualizar_lista_ctas_pagar()
    
    def actualizar_lista_ctas_pagar(self):
        criterio = self.search_var_ctas.get() if hasattr(self, 'search_var_ctas') else None
        for row in self.tree_ctas_pagar.get_children(): self.tree_ctas_pagar.delete(row)
        facturas = proveedores_db.obtener_facturas_impagas(criterio)
        total_deuda = 0.0
        for f in facturas:
            total_deuda += f[6] if f[6] else 0.0
            valores = list(f); valores[5] = f"$ {f[5] or 0.0:.2f}"; valores[6] = f"$ {f[6] or 0.0:.2f}"
            self.tree_ctas_pagar.insert("", "end", values=tuple(valores), iid=f[0])
        self.total_deuda_label.config(text=f"Deuda Total: $ {total_deuda:.2f}")

    def registrar_pago(self):
        if not self.main_window.caja_actual_id: messagebox.showerror("Caja Cerrada", "Debe abrir la caja para registrar un pago.", parent=self); return
        selected_iids = self.tree_ctas_pagar.selection()
        if not selected_iids: messagebox.showwarning("Sin Selección", "Por favor, seleccione al menos una factura para pagar.", parent=self); return
        
        selected_values = [self.tree_ctas_pagar.item(iid, "values") for iid in selected_iids]
        primer_proveedor = selected_values[0][1]
        for values in selected_values[1:]:
            if values[1] != primer_proveedor:
                messagebox.showwarning("Selección Inválida", "Solo puede registrar pagos para un único proveedor a la vez.", parent=self); return
        
        ids_facturas = [vals[0] for vals in selected_values]
        proveedor_id = proveedores_db.obtener_proveedor_por_nombre(primer_proveedor)
        if not proveedor_id: messagebox.showerror("Error", f"No se pudo encontrar el ID del proveedor '{primer_proveedor}'.", parent=self); return
        
        VentanaPagoCtaCte(self, self.main_window.caja_actual_id, proveedor_id, primer_proveedor, ids_facturas)

    def crear_widgets_proveedores_list(self):
        frame = self.proveedores_list_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        filtros_frame = ttk.Frame(frame, style="Content.TFrame"); filtros_frame.grid(row=0, column=0, padx=0, pady=(0,5), sticky="ew")
        ttk.Label(filtros_frame, text="Buscar Proveedor:").pack(side="left", padx=(0,5))
        self.search_var_prov = tk.StringVar(); self.search_var_prov.trace_add("write", lambda n, i, m: self.actualizar_lista_proveedores())
        search_entry = ttk.Entry(filtros_frame, textvariable=self.search_var_prov, width=40); search_entry.pack(side="left", fill="x", expand=True)
        self.tree_frame_prov = ttk.Frame(frame, style="Content.TFrame"); self.tree_frame_prov.grid(row=1, column=0, sticky="nsew")
        self.tree_frame_prov.grid_rowconfigure(0, weight=1); self.tree_frame_prov.grid_columnconfigure(0, weight=1)
        columnas_prov = ("id", "razon_social", "cuit_dni", "telefono"); self.tree_prov = ttk.Treeview(self.tree_frame_prov, columns=columnas_prov, show="headings", displaycolumns=("razon_social", "cuit_dni", "telefono"))
        self.tree_prov.heading("razon_social", text="Razón Social"); self.tree_prov.heading("cuit_dni", text="CUIT/DNI"); self.tree_prov.heading("telefono", text="Teléfono")
        self.tree_prov.column("id", width=0, stretch=tk.NO); self.tree_prov.column("razon_social", width=300)
        self.tree_prov.pack(side='left', fill='both', expand=True); self.tree_prov.bind("<Double-1>", self.abrir_ventana_edicion_proveedor)
        scrollbar_prov = ttk.Scrollbar(self.tree_frame_prov, orient="vertical", command=self.tree_prov.yview); scrollbar_prov.pack(side='right', fill='y'); self.tree_prov.configure(yscrollcommand=scrollbar_prov.set)
        button_frame_prov = ttk.Frame(frame); button_frame_prov.grid(row=1, column=1, padx=10, pady=0, sticky="ns")
        ttk.Button(button_frame_prov, text="Agregar Nuevo", command=self.abrir_ventana_creacion_proveedor, style="Action.TButton").pack(pady=5, fill='x')
        ttk.Button(button_frame_prov, text="Modificar", command=self.abrir_ventana_edicion_proveedor, style="Action.TButton").pack(pady=5, fill='x')
        self.actualizar_lista_proveedores()

    def actualizar_lista_proveedores(self):
        for row in self.tree_prov.get_children(): self.tree_prov.delete(row)
        criterio = self.search_var_prov.get() if hasattr(self, 'search_var_prov') else None
        proveedores = proveedores_db.obtener_proveedores(criterio=criterio)
        for proveedor in proveedores: self.tree_prov.insert("", "end", values=proveedor)

    def abrir_ventana_creacion_proveedor(self):
        ventana = VentanaProveedor(self); self.wait_window(ventana)

    def abrir_ventana_edicion_proveedor(self, event=None):
        selected_item = self.tree_prov.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Por favor, seleccione un proveedor."); return
        proveedor_id = self.tree_prov.item(selected_item, "values")[0]
        ventana = VentanaProveedor(self, proveedor_id=proveedor_id); self.wait_window(ventana)

    def crear_widgets_resumen_cc(self):
        frame = self.resumen_cc_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        filtros_frame = ttk.LabelFrame(frame, text="Filtros", style="TLabelframe"); filtros_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(filtros_frame, text="Seleccionar Proveedor:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ccp_proveedor_combo = ttk.Combobox(filtros_frame, state="readonly", width=30); self.ccp_proveedor_combo.grid(row=0, column=1, padx=5, pady=5)
        self.proveedores_data_reporte = proveedores_db.obtener_todos_los_proveedores_para_reporte(); self.ccp_proveedor_combo['values'] = [p[1] for p in self.proveedores_data_reporte]
        ttk.Label(filtros_frame, text="Desde:").grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")
        self.ccp_fecha_desde = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12); self.ccp_fecha_desde.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(filtros_frame, text="Hasta:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.ccp_fecha_hasta = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12); self.ccp_fecha_hasta.grid(row=0, column=5, padx=5, pady=5)
        btn_generar = ttk.Button(filtros_frame, text="Generar Resumen", command=self.generar_reporte_cc_proveedor, style="Action.TButton"); btn_generar.grid(row=0, column=6, padx=10, pady=5)
        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        columnas = ("fecha", "tipo", "monto", "saldo"); self.tree_cc_proveedores = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_cc_proveedores.heading("fecha", text="Fecha"); self.tree_cc_proveedores.heading("tipo", text="Tipo Movimiento"); self.tree_cc_proveedores.heading("monto", text="Monto"); self.tree_cc_proveedores.heading("saldo", text="Saldo Resultante")
        self.tree_cc_proveedores.column("monto", anchor="e"); self.tree_cc_proveedores.column("saldo", anchor="e"); self.tree_cc_proveedores.grid(row=0, column=0, sticky="nsew")

    def generar_reporte_cc_proveedor(self):
        proveedor_nombre = self.ccp_proveedor_combo.get()
        if not proveedor_nombre: messagebox.showwarning("Dato Faltante", "Por favor, seleccione un proveedor."); return
        proveedor_id = next((pid for pid, nombre in self.proveedores_data_reporte if nombre == proveedor_nombre), None)
        if proveedor_id is None: messagebox.showerror("Error", "No se pudo encontrar el ID del proveedor seleccionado."); return
        fecha_desde = self.ccp_fecha_desde.get(); fecha_hasta = self.ccp_fecha_hasta.get()
        for row in self.tree_cc_proveedores.get_children(): self.tree_cc_proveedores.delete(row)
        movimientos = proveedores_db.obtener_cuenta_corriente_proveedor(proveedor_id, fecha_desde, fecha_hasta)
        for mov in movimientos:
            valores = (mov[0], mov[1], f"$ {mov[2]:.2f}", f"$ {mov[3]:.2f}")
            self.tree_cc_proveedores.insert("", "end", values=valores)