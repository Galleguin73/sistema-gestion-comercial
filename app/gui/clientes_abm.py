import tkinter as tk
from tkinter import ttk, messagebox
# CORRECCIÓN: Importamos desde los nuevos módulos de base de datos
from app.database import clientes_db, config_db 

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

        self.frame = ttk.Frame(self, padding="10")
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

class ClientesFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style

        self.style.configure("Action.TButton", font=("Helvetica", 10, "bold"))
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tree_frame = ttk.Frame(self, style="Content.TFrame")
        self.tree_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        columnas = ("id", "razon_social", "nombre_fantasia", "tipo_cuenta", "fecha_alta", "estado")
        self.tree = ttk.Treeview(self.tree_frame, columns=columnas, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("razon_social", text="Razón Social")
        self.tree.heading("nombre_fantasia", text="Nombre Fantasía")
        self.tree.heading("tipo_cuenta", text="Tipo")
        self.tree.heading("fecha_alta", text="Fecha de Alta")
        self.tree.heading("estado", text="Estado")

        self.tree.column("id", width=50, anchor='center')
        self.tree.column("razon_social", width=250)
        self.tree.column("nombre_fantasia", width=250)
        self.tree.column("tipo_cuenta", width=100, anchor='center')
        self.tree.column("fecha_alta", width=120, anchor='center')
        self.tree.column("estado", width=100, anchor='center')

        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind("<Double-1>", self.abrir_ventana_edicion)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.button_frame = ttk.Frame(self, style="Content.TFrame")
        self.button_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

        self.add_btn = ttk.Button(self.button_frame, text="Agregar Nuevo", command=self.abrir_ventana_creacion, style="Action.TButton")
        self.add_btn.pack(pady=5, fill='x')
        
        self.update_btn = ttk.Button(self.button_frame, text="Modificar", command=self.abrir_ventana_edicion, style="Action.TButton")
        self.update_btn.pack(pady=5, fill='x')
        
        self.delete_btn = ttk.Button(self.button_frame, text="Eliminar", command=self.eliminar_cliente, style="Action.TButton")
        self.delete_btn.pack(pady=5, fill='x')

        self.actualizar_lista()

    def actualizar_lista(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        clientes = clientes_db.obtener_clientes() # Referencia actualizada
        for cliente in clientes:
            self.tree.insert("", "end", values=cliente)

    def abrir_ventana_creacion(self):
        VentanaCliente(self)

    def abrir_ventana_edicion(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un cliente de la lista para modificar.")
            return
        cliente_id = self.tree.item(selected_item, "values")[0]
        VentanaCliente(self, cliente_id=cliente_id)

    def eliminar_cliente(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un cliente de la lista para eliminar.")
            return
        cliente_id = self.tree.item(selected_item, "values")[0]
        razon_social = self.tree.item(selected_item, "values")[1]
        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar a '{razon_social}'?"):
            clientes_db.eliminar_cliente(cliente_id)
            messagebox.showinfo("Éxito", "Cliente eliminado correctamente.")
            self.actualizar_lista()