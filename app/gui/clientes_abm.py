import tkinter as tk
from tkinter import ttk, messagebox
from app.database import clientes_db, config_db, ventas_db
from tkcalendar import DateEntry
from datetime import datetime

# La ventana para agregar/editar clientes no necesita grandes cambios.
class VentanaCliente(tk.Toplevel):
    def __init__(self, parent, cliente_id=None, on_success_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.cliente_id = cliente_id
        self.on_success_callback = on_success_callback

        titulo = "Editar Cliente" if self.cliente_id else "Agregar Nuevo Cliente"
        self.title(titulo)
        self.geometry("700x600")
        self.transient(parent)
        self.grab_set()
        
        # --- Aplicamos el nuevo estilo de secciones ---
        style = ttk.Style(self)
        style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")
        
        main_container = ttk.Frame(self, style="ContentPane.TFrame", padding=10)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        ttk.Label(main_container, text=titulo, style="SectionTitle.TLabel").pack(fill="x", expand=True, side="top")
        
        self.frame = ttk.Frame(main_container, padding="10")
        self.frame.pack(fill='both', expand=True)
        self.frame.grid_columnconfigure(1, weight=1)

        self.entries = {}
        row_num = 0

        campos_simples = [("Razón Social:", 'razon_social'), ("Nombre Fantasía:", 'nombre_fantasia'),("CUIT/DNI:", 'cuit_dni'), ("Teléfono:", 'telefono'),("Email:", 'email'), ("Domicilio:", 'domicilio')]
        for texto, clave in campos_simples:
            ttk.Label(self.frame, text=texto).grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
            self.entries[clave] = ttk.Entry(self.frame)
            self.entries[clave].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
            row_num += 1

        ttk.Label(self.frame, text="Provincia:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.provincia_combo = ttk.Combobox(self.frame, state="readonly")
        self.provincia_combo.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        self.entries['provincia'] = self.provincia_combo
        row_num += 1
        
        ttk.Label(self.frame, text="Localidad:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.localidad_combo = ttk.Combobox(self.frame)
        self.localidad_combo.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        self.entries['localidad'] = self.localidad_combo
        row_num += 1

        self.provincias_data = config_db.obtener_provincias()
        self.provincia_combo['values'] = [p[1] for p in self.provincias_data]
        self.provincia_combo.bind("<<ComboboxSelected>>", self.actualizar_localidades)

        campos_finales = [("Contacto:", 'persona_de_contacto'),("Condición IVA:", 'condicion_iva', ["Consumidor Final", "Monotributo", "Responsable Inscripto", "Exento"]),("Tipo de Cuenta:", 'tipo_cuenta', ["Individuo", "Empresa"]),("Estado:", 'estado', ["Activo", "Suspendido"])]
        for item in campos_finales:
            texto, clave, *valores = item
            ttk.Label(self.frame, text=texto).grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
            if valores: self.entries[clave] = ttk.Combobox(self.frame, values=valores[0])
            else: self.entries[clave] = ttk.Entry(self.frame)
            self.entries[clave].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
            row_num += 1
        
        ttk.Label(self.frame, text="Fecha de Alta:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.fecha_alta_entry = ttk.Entry(self.frame, state='readonly')
        self.entries['fecha_alta'] = self.fecha_alta_entry
        self.fecha_alta_entry.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        row_num += 1

        self.cc_var = tk.BooleanVar()
        self.entries['cuenta_corriente_habilitada'] = ttk.Checkbutton(self.frame, text="Habilitar Cuenta Corriente", variable=self.cc_var)
        self.entries['cuenta_corriente_habilitada'].grid(row=row_num, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        row_num += 1
        
        ttk.Label(self.frame, text="Límite Cta. Cte.:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['limite_cuenta_corriente'] = ttk.Entry(self.frame)
        self.entries['limite_cuenta_corriente'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        row_num += 1
        
        ttk.Label(self.frame, text="Saldo Cta. Cte.:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.saldo_entry = ttk.Entry(self.frame, state='readonly')
        self.entries['saldo_cuenta_corriente'] = self.saldo_entry
        self.saldo_entry.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        row_num += 1
        
        self.save_btn = ttk.Button(self.frame, text="Guardar", command=self.guardar)
        self.save_btn.grid(row=row_num, column=0, columnspan=2, pady=10, padx=5, sticky="ew")

        if self.cliente_id:
            self.cargar_datos_cliente()
        else:
            self.entries['estado'].set("Activo")

    def actualizar_localidades(self, event=None):
        provincia_nombre = self.provincia_combo.get()
        provincia_id = next((pid for pid, nombre in self.provincias_data if nombre == provincia_nombre), None)
        if provincia_id:
            localidades = config_db.obtener_localidades_por_provincia(provincia_id)
            self.localidad_combo['values'] = localidades
            if self.localidad_combo.get() not in localidades:
                self.localidad_combo.set('')

    def cargar_datos_cliente(self):
        cliente = clientes_db.obtener_cliente_por_id(self.cliente_id)
        if cliente:
            keys = clientes_db.get_cliente_column_names()
            cliente_dict = dict(zip(keys, cliente))
            for clave, entry in self.entries.items():
                valor = cliente_dict.get(clave)
                if isinstance(entry, ttk.Checkbutton): self.cc_var.set(bool(valor))
                elif isinstance(entry, (ttk.Combobox, ttk.Entry)):
                    is_readonly = entry.cget("state") == 'readonly'
                    if is_readonly: entry.config(state='normal')
                    entry.delete(0, tk.END)
                    entry.insert(0, valor if valor is not None else "")
                    if is_readonly: entry.config(state='readonly')
            provincia_guardada = cliente_dict.get('provincia')
            if provincia_guardada:
                self.provincia_combo.set(provincia_guardada)
                self.actualizar_localidades()
                self.localidad_combo.set(cliente_dict.get('localidad'))
    
    def guardar(self):
        datos = {}
        for clave, entry in self.entries.items():
            if clave in ['fecha_alta', 'saldo_cuenta_corriente']: continue
            if isinstance(entry, ttk.Checkbutton): datos[clave] = self.cc_var.get()
            elif isinstance(entry, (ttk.Combobox, ttk.Entry)): datos[clave] = entry.get()
        
        if not datos.get("razon_social"):
            messagebox.showwarning("Campo Vacío", "La Razón Social es obligatoria.", parent=self)
            return
            
        if self.cliente_id:
            datos['id'] = self.cliente_id
            resultado = clientes_db.modificar_cliente(datos)
        else:
            resultado = clientes_db.agregar_cliente(datos)

        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            if hasattr(self.parent, 'actualizar_lista'): self.parent.actualizar_lista()
            if self.on_success_callback: self.on_success_callback(datos)
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

# --- CLASE PRINCIPAL COMPLETAMENTE REESCRITA ---
class ClientesFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        
        # Aplicamos los estilos
        self.style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        self.style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")

        # Usamos PanedWindow para los dos paneles principales
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Panel Izquierdo ---
        left_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(left_panel, weight=1)
        self._crear_panel_izquierdo(left_panel)
        
        # --- Panel Derecho ---
        right_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(right_panel, weight=2)
        self._crear_panel_derecho(right_panel)
        
        self.actualizar_lista()

    def _crear_panel_izquierdo(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Contenedor para la lista de clientes
        clientes_container = ttk.Frame(parent, style="ContentPane.TFrame")
        clientes_container.grid(row=0, column=0, sticky="nsew", pady=(0,5))
        clientes_container.rowconfigure(1, weight=1)
        clientes_container.columnconfigure(0, weight=1)

        ttk.Label(clientes_container, text="Listado de Clientes", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        
        # Filtro de búsqueda
        search_frame = ttk.Frame(clientes_container, padding=5)
        search_frame.grid(row=1, column=0, sticky="ew")
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text="Buscar:").grid(row=0, column=0)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda n, i, m: self.actualizar_lista())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=5)

        # Treeview de clientes
        tree_content = ttk.Frame(clientes_container)
        tree_content.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0,5))
        tree_content.grid_rowconfigure(0, weight=1); tree_content.grid_columnconfigure(0, weight=1)

        columnas = ("id", "nombre", "saldo")
        self.tree = ttk.Treeview(tree_content, columns=columnas, show="headings", displaycolumns=("nombre", "saldo"))
        self.tree.heading("nombre", text="Razón Social")
        self.tree.heading("saldo", text="Saldo")
        self.tree.column("saldo", anchor="e", width=100)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_cliente_selected)

        # Botones de acción para el listado
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=1, column=0, sticky="ew")
        ttk.Button(buttons_frame, text="Nuevo", command=self.abrir_ventana_creacion).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(buttons_frame, text="Modificar", command=self.abrir_ventana_edicion).pack(side="left", expand=True, fill="x", padx=2)

    def _crear_panel_derecho(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Etiqueta inicial
        self.placeholder_label = ttk.Label(parent, text="Seleccione un cliente para ver su detalle", font=("Helvetica", 14, "italic"), style="TLabel")
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- Contenedores que se mostrarán al seleccionar un cliente ---
        self.detalle_container = ttk.Frame(parent) # Contenedor principal para los detalles
        
        # Sección de Datos
        datos_container = ttk.Frame(self.detalle_container, style="ContentPane.TFrame")
        datos_container.pack(fill="x", pady=(0, 10))
        ttk.Label(datos_container, text="Datos del Cliente", style="SectionTitle.TLabel").pack(fill="x")
        datos_frame = ttk.Frame(datos_container, padding=10)
        datos_frame.pack(fill="x")
        datos_frame.columnconfigure(1, weight=1)
        
        self.detalle_labels = {}
        campos = [("Razón Social:", "razon_social"), ("CUIT/DNI:", "cuit_dni"), ("Teléfono:", "telefono"), ("Saldo Actual:", "saldo_cuenta_corriente")]
        for i, (texto, clave) in enumerate(campos):
            ttk.Label(datos_frame, text=texto, font=("Helvetica", 9, "bold")).grid(row=i, column=0, sticky="w")
            self.detalle_labels[clave] = ttk.Label(datos_frame, text="-")
            self.detalle_labels[clave].grid(row=i, column=1, sticky="w", padx=5)

        # Sección de Historial
        historial_container = ttk.Frame(self.detalle_container, style="ContentPane.TFrame")
        historial_container.pack(fill="both", expand=True)
        historial_container.rowconfigure(1, weight=1); historial_container.columnconfigure(0, weight=1)
        ttk.Label(historial_container, text="Historial de Cuenta Corriente", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        
        historial_frame = ttk.Frame(historial_container)
        historial_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        historial_frame.rowconfigure(0, weight=1); historial_frame.columnconfigure(0, weight=1)

        columnas_hist = ("fecha", "tipo", "monto", "saldo")
        self.tree_historial = ttk.Treeview(historial_frame, columns=columnas_hist, show="headings")
        self.tree_historial.heading("fecha", text="Fecha"); self.tree_historial.heading("tipo", text="Tipo Movimiento"); self.tree_historial.heading("monto", text="Monto"); self.tree_historial.heading("saldo", text="Saldo Resultante")
        self.tree_historial.column("monto", anchor="e"); self.tree_historial.column("saldo", anchor="e")
        self.tree_historial.grid(row=0, column=0, sticky="nsew")
        
        # Botones de acción para el historial
        buttons_hist_frame = ttk.Frame(self.detalle_container)
        buttons_hist_frame.pack(fill="x", pady=10)
        ttk.Button(buttons_hist_frame, text="Registrar Pago", command=self.registrar_pago).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(buttons_hist_frame, text="Imprimir Resumen", command=self.imprimir_resumen).pack(side="left", expand=True, fill="x", padx=2)
        
    def actualizar_lista(self):
        # Limpiamos el panel de detalles
        self.on_cliente_selected(None)
        
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        criterio = self.search_var.get()
        # Aquí necesitaremos una función que traiga TODOS los clientes y su saldo.
        # Por ahora, simulamos con las funciones existentes.
        clientes = clientes_db.obtener_clientes(criterio=criterio)
        clientes_con_saldo = {c[0]: c[2] for c in clientes_db.obtener_clientes_con_saldo()}
        
        for cliente in clientes:
            cliente_id = cliente[0]
            nombre = cliente[1]
            saldo = clientes_con_saldo.get(cliente_id, 0.0)
            
            display_nombre = f"💰 {nombre}" if saldo != 0 else nombre
            display_saldo = f"$ {saldo:,.2f}" if saldo != 0 else ""
            
            self.tree.insert("", "end", iid=cliente_id, values=(cliente_id, display_nombre, display_saldo))

    def on_cliente_selected(self, event=None):
        selected_item = self.tree.focus()
        
        if not selected_item:
            # Ocultamos el panel de detalles y mostramos el mensaje inicial
            self.detalle_container.pack_forget()
            self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")
            return
            
        # Si hay selección, mostramos el panel de detalles y ocultamos el mensaje
        self.placeholder_label.place_forget()
        self.detalle_container.pack(fill="both", expand=True, pady=(0,5))
        
        cliente_id = int(selected_item)
        
        # Cargar datos del cliente en el panel de detalles
        cliente_data = clientes_db.obtener_cliente_por_id(cliente_id)
        if cliente_data:
            keys = clientes_db.get_cliente_column_names()
            cliente_dict = dict(zip(keys, cliente_data))
            
            self.detalle_labels["razon_social"].config(text=cliente_dict.get("razon_social", "-"))
            self.detalle_labels["cuit_dni"].config(text=cliente_dict.get("cuit_dni", "-"))
            self.detalle_labels["telefono"].config(text=cliente_dict.get("telefono", "-"))
            
            saldo = cliente_dict.get("saldo_cuenta_corriente", 0.0)
            self.detalle_labels["saldo_cuenta_corriente"].config(text=f"$ {saldo:,.2f}", foreground="red" if saldo > 0 else "green")
            
        # Cargar historial de cuenta corriente
        for row in self.tree_historial.get_children():
            self.tree_historial.delete(row)
        
        historial = clientes_db.obtener_cuenta_corriente_cliente(cliente_id)
        for mov in historial:
            fecha, tipo, monto, saldo_res = mov
            valores = (fecha, tipo, f"$ {monto:,.2f}", f"$ {saldo_res:,.2f}")
            self.tree_historial.insert("", "end", values=valores)

    def abrir_ventana_creacion(self):
        VentanaCliente(self, on_success_callback=lambda data: self.actualizar_lista())

    def abrir_ventana_edicion(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un cliente para modificar.")
            return
        cliente_id = int(selected_item)
        VentanaCliente(self, cliente_id=cliente_id)

    def registrar_pago(self):
        messagebox.showinfo("En Desarrollo", "La funcionalidad para registrar pagos se implementará en el siguiente paso.")
        
    def imprimir_resumen(self):
        messagebox.showinfo("En Desarrollo", "La funcionalidad para imprimir resúmenes se implementará próximamente.")