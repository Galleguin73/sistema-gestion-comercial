import tkinter as tk
from tkinter import ttk, messagebox
from app.database import proveedores_db

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

        # Fila 0
        ttk.Label(self.frame, text="Razón Social:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['razon_social'] = ttk.Entry(self.frame)
        self.entries['razon_social'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        row_num += 1
        
        # Fila 1
        ttk.Label(self.frame, text="CUIT/DNI:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['cuit_dni'] = ttk.Entry(self.frame)
        self.entries['cuit_dni'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        row_num += 1

        # Fila 2 (NUEVA)
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

class ProveedoresFrame(ttk.Frame):
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
        self.button_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

        self.add_btn = ttk.Button(self.button_frame, text="Agregar Nuevo", command=self.abrir_ventana_creacion, style="Action.TButton")
        self.add_btn.pack(pady=5, fill='x')
        self.update_btn = ttk.Button(self.button_frame, text="Modificar", command=self.abrir_ventana_edicion, style="Action.TButton")
        self.update_btn.pack(pady=5, fill='x')
        self.delete_btn = ttk.Button(self.button_frame, text="Eliminar", command=self.eliminar_proveedor, style="Action.TButton")
        self.delete_btn.pack(pady=5, fill='x')

        self.actualizar_lista()

    def actualizar_lista(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        proveedores = proveedores_db.obtener_proveedores()
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