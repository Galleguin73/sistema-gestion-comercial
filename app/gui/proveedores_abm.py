import tkinter as tk
from tkinter import ttk, messagebox
from app.database import proveedores_db, compras_db, config_db, caja_db
from tkcalendar import DateEntry
from datetime import datetime
# --- 1. IMPORTAMOS NUESTRO AYUDANTE DE FORMATO ---
from .mixins.locale_validation_mixin import LocaleValidationMixin

def format_db_date(date_str):
    if not date_str:
        return ""
    try:
        return datetime.fromisoformat(date_str.split(' ')[0]).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return date_str

class VentanaProveedor(tk.Toplevel):
    # (Esta clase no muestra números con formato, se mantiene la lógica original)
    def __init__(self, parent, proveedor_id=None, on_success_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.proveedor_id = proveedor_id
        self.on_success_callback = on_success_callback
        titulo = "Editar Proveedor" if self.proveedor_id else "Nuevo Proveedor"
        self.title(titulo)
        self.geometry("600x450")
        self.transient(parent); self.grab_set()

        style = ttk.Style(self)
        style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")

        main_container = ttk.Frame(self, style="ContentPane.TFrame", padding=10)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        ttk.Label(main_container, text=titulo, style="SectionTitle.TLabel").pack(fill="x", expand=True, side="top")
        
        self.frame = ttk.Frame(main_container, padding="10")
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
            if self.on_success_callback: self.on_success_callback()
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

        style = ttk.Style(self)
        style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")

        frame = ttk.Frame(self, padding="10"); frame.pack(fill='both', expand=True); frame.grid_columnconfigure(0, weight=1); frame.grid_rowconfigure(1, weight=1)
        
        pago_container = ttk.Frame(frame, style="ContentPane.TFrame")
        pago_container.grid(row=0, column=0, pady=5, sticky='nsew')
        ttk.Label(pago_container, text="Agregar Medio de Pago", style="SectionTitle.TLabel").pack(fill="x")
        pago_frame = ttk.Frame(pago_container, padding=10)
        pago_frame.pack(fill="x")
        pago_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(pago_frame, text="Monto a Pagar:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.monto_entry = ttk.Entry(pago_frame); self.monto_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        ttk.Label(pago_frame, text="Medio de Pago:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.medio_pago_combo = ttk.Combobox(pago_frame, state='readonly'); self.medio_pago_combo.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        self.medios_de_pago_data = config_db.obtener_medios_de_pago(); self.medio_pago_combo['values'] = [m[1] for m in self.medios_de_pago_data]
        
        btn_agregar_pago = ttk.Button(pago_frame, text="Agregar Pago", command=self.agregar_pago); btn_agregar_pago.grid(row=2, column=1, padx=5, pady=5, sticky='e')

        lista_container = ttk.Frame(frame, style="ContentPane.TFrame")
        lista_container.grid(row=1, column=0, pady=5, sticky='nsew')
        lista_container.rowconfigure(1, weight=1); lista_container.columnconfigure(0, weight=1)
        ttk.Label(lista_container, text="Pagos a Realizar", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        lista_frame = ttk.Frame(lista_container, padding=5)
        lista_frame.grid(row=1, column=0, sticky="nsew")
        lista_frame.grid_rowconfigure(0, weight=1); lista_frame.grid_columnconfigure(0, weight=1)

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
        self.tree_pagos.insert("", "end", values=(medio_pago_nombre, f"$ {LocaleValidationMixin._format_local_number(monto)}"))
        self.monto_entry.delete(0, tk.END); self.medio_pago_combo.set('')
        self.btn_confirmar.config(state="normal")
        
    def confirmar(self):
        if not self.pagos_realizados: messagebox.showwarning("Sin Pagos", "Debe agregar al menos un medio de pago.", parent=self); return
        concepto = f"Pago Cta. Cte. a Proveedor: {self.proveedor_nombre}"
        resultado = proveedores_db.registrar_pago_a_facturas(self.caja_id, self.proveedor_id, self.pagos_realizados, self.ids_facturas, concepto)
        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self.parent)
            self.parent.actualizar_lista_proveedores()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

class ProveedoresFrame(ttk.Frame):
    def __init__(self, parent, style, main_window):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.main_window = main_window

        self.style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        self.style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")

        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True, padx=10, pady=10)

        left_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(left_panel, weight=1)
        self._crear_panel_izquierdo(left_panel)
        
        right_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(right_panel, weight=2)
        self._crear_panel_derecho(right_panel)
        
        self.actualizar_lista_proveedores()

    def _crear_panel_izquierdo(self, parent):
        parent.grid_rowconfigure(0, weight=1); parent.grid_columnconfigure(0, weight=1)
        
        proveedores_container = ttk.Frame(parent, style="ContentPane.TFrame")
        proveedores_container.grid(row=0, column=0, sticky="nsew", pady=(0,5))
        proveedores_container.rowconfigure(2, weight=1); proveedores_container.columnconfigure(0, weight=1)
        
        ttk.Label(proveedores_container, text="Listado de Proveedores", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        
        search_frame = ttk.Frame(proveedores_container, padding=5); search_frame.grid(row=1, column=0, sticky="ew")
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text="Buscar:").grid(row=0, column=0)
        self.search_var_prov = tk.StringVar(); self.search_var_prov.trace_add("write", lambda n, i, m: self.actualizar_lista_proveedores())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var_prov); search_entry.grid(row=0, column=1, sticky="ew", padx=5)

        tree_content = ttk.Frame(proveedores_container); tree_content.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0,5))
        tree_content.grid_rowconfigure(0, weight=1); tree_content.grid_columnconfigure(0, weight=1)

        columnas_prov = ("id", "razon_social", "saldo"); self.tree_prov = ttk.Treeview(tree_content, columns=columnas_prov, show="headings", displaycolumns=("razon_social", "saldo"))
        self.tree_prov.heading("razon_social", text="Razón Social"); self.tree_prov.heading("saldo", text="Saldo")
        self.tree_prov.column("saldo", anchor="e", width=100)
        self.tree_prov.grid(row=0, column=0, sticky="nsew")
        self.tree_prov.bind("<<TreeviewSelect>>", self.on_proveedor_selected)
        
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=1, column=0, sticky="ew")
        ttk.Button(buttons_frame, text="Nuevo", command=self.abrir_ventana_creacion_proveedor).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(buttons_frame, text="Modificar", command=self.abrir_ventana_edicion_proveedor).pack(side="left", expand=True, fill="x", padx=2)

    def _crear_panel_derecho(self, parent):
        parent.grid_rowconfigure(1, weight=1); parent.grid_columnconfigure(0, weight=1)
        
        self.placeholder_label = ttk.Label(parent, text="Seleccione un proveedor para ver su detalle", font=("Helvetica", 14, "italic"), style="TLabel")
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

        self.detalle_container = ttk.Frame(parent)
        
        datos_container = ttk.Frame(self.detalle_container, style="ContentPane.TFrame")
        datos_container.pack(fill="x", pady=(0, 10))
        ttk.Label(datos_container, text="Datos del Proveedor", style="SectionTitle.TLabel").pack(fill="x")
        datos_frame = ttk.Frame(datos_container, padding=10); datos_frame.pack(fill="x")
        datos_frame.columnconfigure(1, weight=1)
        
        self.detalle_labels = {}
        campos = [("Razón Social:", "razon_social"), ("CUIT/DNI:", "cuit_dni"), ("Teléfono:", "telefono"), ("Saldo Actual:", "saldo_cuenta_corriente")]
        for i, (texto, clave) in enumerate(campos):
            ttk.Label(datos_frame, text=texto, font=("Helvetica", 9, "bold")).grid(row=i, column=0, sticky="w")
            self.detalle_labels[clave] = ttk.Label(datos_frame, text="-")
            self.detalle_labels[clave].grid(row=i, column=1, sticky="w", padx=5)

        historial_container = ttk.Frame(self.detalle_container, style="ContentPane.TFrame")
        historial_container.pack(fill="both", expand=True)
        historial_container.rowconfigure(1, weight=1); historial_container.columnconfigure(0, weight=1)
        ttk.Label(historial_container, text="Historial de Cuenta Corriente", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        
        historial_frame = ttk.Frame(historial_container); historial_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        historial_frame.rowconfigure(0, weight=1); historial_frame.columnconfigure(0, weight=1)

        columnas_hist = ("fecha", "tipo", "monto", "saldo"); self.tree_historial = ttk.Treeview(historial_frame, columns=columnas_hist, show="headings")
        self.tree_historial.heading("fecha", text="Fecha"); self.tree_historial.heading("tipo", text="Tipo Movimiento"); self.tree_historial.heading("monto", text="Monto"); self.tree_historial.heading("saldo", text="Saldo Resultante")
        self.tree_historial.column("monto", anchor="e"); self.tree_historial.column("saldo", anchor="e"); self.tree_historial.grid(row=0, column=0, sticky="nsew")
        
        buttons_hist_frame = ttk.Frame(self.detalle_container)
        buttons_hist_frame.pack(fill="x", pady=10)
        ttk.Button(buttons_hist_frame, text="Registrar Pago", command=self.registrar_pago).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(buttons_hist_frame, text="Imprimir Resumen", command=self.imprimir_resumen).pack(side="left", expand=True, fill="x", padx=2)

    def actualizar_lista_proveedores(self):
        self.on_proveedor_selected(None)
        for row in self.tree_prov.get_children(): self.tree_prov.delete(row)
        
        criterio = self.search_var_prov.get() if hasattr(self, 'search_var_prov') else ""
        proveedores = proveedores_db.obtener_proveedores(criterio)
        proveedores_con_saldo = {p[0]: p[2] for p in proveedores_db.obtener_proveedores_con_saldo()}
        
        for prov in proveedores:
            prov_id, nombre = prov[0], prov[1]
            saldo = proveedores_con_saldo.get(prov_id, 0.0)
            if abs(saldo) < 0.01: saldo = 0.0
            
            display_nombre = f"💰 {nombre}" if saldo != 0 else nombre
            display_saldo = f"$ {LocaleValidationMixin._format_local_number(saldo)}" if saldo != 0 else ""
            
            self.tree_prov.insert("", "end", iid=prov_id, values=(prov_id, display_nombre, display_saldo))

    def on_proveedor_selected(self, event=None):
        selected_item = self.tree_prov.focus()
        if not selected_item:
            self.detalle_container.pack_forget(); self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")
            return
        
        self.placeholder_label.place_forget(); self.detalle_container.pack(fill="both", expand=True, pady=(0,5))
        proveedor_id = int(selected_item)
        
        proveedor_data = proveedores_db.obtener_proveedor_por_id(proveedor_id)
        if proveedor_data:
            keys = proveedores_db.get_proveedor_column_names()
            proveedor_dict = dict(zip(keys, proveedor_data))
            
            self.detalle_labels["razon_social"].config(text=proveedor_dict.get("razon_social", "-"))
            self.detalle_labels["cuit_dni"].config(text=proveedor_dict.get("cuit_dni", "-"))
            self.detalle_labels["telefono"].config(text=proveedor_dict.get("telefono", "-"))
            
            saldo_actual = 0.0
            historial = proveedores_db.obtener_cuenta_corriente_proveedor(proveedor_id)
            if historial:
                saldo_actual = historial[-1][3]
            if abs(saldo_actual) < 0.01: saldo_actual = 0.0
            
            self.detalle_labels["saldo_cuenta_corriente"].config(text=f"$ {LocaleValidationMixin._format_local_number(saldo_actual)}", foreground="red" if saldo_actual != 0 else "green")
            
        for row in self.tree_historial.get_children(): self.tree_historial.delete(row)
        
        for mov in historial:
            fecha, tipo, monto, saldo_res = mov
            if abs(monto) < 0.01: monto = 0.0
            if abs(saldo_res) < 0.01: saldo_res = 0.0
            valores = (format_db_date(fecha), tipo, f"$ {LocaleValidationMixin._format_local_number(monto)}", f"$ {LocaleValidationMixin._format_local_number(saldo_res)}")
            self.tree_historial.insert("", "end", values=valores)

    def abrir_ventana_creacion_proveedor(self):
        VentanaProveedor(self, on_success_callback=self.actualizar_lista_proveedores)

    def abrir_ventana_edicion_proveedor(self, event=None):
        selected_item = self.tree_prov.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Por favor, seleccione un proveedor."); return
        proveedor_id = int(selected_item)
        VentanaProveedor(self, proveedor_id=proveedor_id, on_success_callback=self.actualizar_lista_proveedores)

    def registrar_pago(self):
        if not self.main_window.caja_actual_id: messagebox.showerror("Caja Cerrada", "Debe abrir la caja para registrar un pago.", parent=self); return
        selected_item = self.tree_prov.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Seleccione un proveedor para registrar un pago.", parent=self); return
        
        proveedor_id = int(selected_item)
        proveedor_nombre = self.tree_prov.item(selected_item, "values")[1].replace("💰 ", "")
        
        facturas_impagas = compras_db.obtener_compras_impagas(proveedor_id)
        if not facturas_impagas:
            messagebox.showinfo("Sin Deuda", f"El proveedor {proveedor_nombre} no tiene facturas pendientes de pago.", parent=self)
            return
            
        ids_facturas = [f[0] for f in facturas_impagas]
        VentanaPagoCtaCte(self, self.main_window.caja_actual_id, proveedor_id, proveedor_nombre, ids_facturas)
    
    def imprimir_resumen(self):
        messagebox.showinfo("En Desarrollo", "La funcionalidad para imprimir resúmenes se implementará próximamente.")