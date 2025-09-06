# Ubicación: app/gui/obligaciones_tipos_abm.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.database import obligaciones_db
from .mixins.centering_mixin import CenteringMixin

class VentanaObligacionTipo(tk.Toplevel, CenteringMixin):
    def __init__(self, parent, on_success_callback, tipo_id=None):
        super().__init__(parent)
        self.withdraw()
        self.parent = parent
        self.on_success_callback = on_success_callback
        self.tipo_id = tipo_id

        titulo = "Editar Tipo de Obligación" if self.tipo_id else "Nuevo Tipo de Obligación"
        self.title(titulo)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding="15")
        frame.pack(expand=True, fill="both")
        frame.columnconfigure(1, weight=1)

        self.entries = {}
        campos = [
            ("Nombre:", "nombre"),
            ("Categoría:", "categoria", ["Impuestos", "Servicios", "Alquileres", "Otros"]),
            ("Descripción:", "descripcion")
        ]

        for i, (texto, clave, *valores) in enumerate(campos):
            label = ttk.Label(frame, text=texto)
            label.grid(row=i, column=0, padx=5, pady=8, sticky="w")
            if valores:
                entry = ttk.Combobox(frame, values=valores[0], state="readonly")
            else:
                entry = ttk.Entry(frame, width=40)
            entry.grid(row=i, column=1, padx=5, pady=8, sticky="ew")
            self.entries[clave] = entry
        
        btn_guardar = ttk.Button(frame, text="Guardar", command=self.guardar, style="Action.TButton")
        btn_guardar.grid(row=len(campos), column=0, columnspan=2, pady=15, sticky="ew")

        if self.tipo_id:
            self.cargar_datos()

        self.center_window()
        self.deiconify()

    def cargar_datos(self):
        datos_tupla = obligaciones_db.obtener_tipo_por_id(self.tipo_id)
        columnas = obligaciones_db.get_tipo_column_names()
        datos_dict = dict(zip(columnas, datos_tupla))
        
        for clave, widget in self.entries.items():
            valor = datos_dict.get(clave, "")
            if isinstance(widget, ttk.Combobox):
                widget.set(valor)
            else:
                widget.insert(0, valor)

    def guardar(self):
        datos = {clave: widget.get() for clave, widget in self.entries.items()}
        if not datos.get("nombre") or not datos.get("categoria"):
            messagebox.showwarning("Campos Vacíos", "El nombre y la categoría son obligatorios.", parent=self)
            return
            
        if self.tipo_id:
            datos['id'] = self.tipo_id
            resultado = obligaciones_db.modificar_tipo_de_obligacion(datos)
        else:
            resultado = obligaciones_db.agregar_tipo_de_obligacion(datos)
            
        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            self.on_success_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

class ObligacionesTiposFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent)
        self.style = style

        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill='x', padx=20, pady=20)
        
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(expand=True, fill='x', pady=(0, 10))

        columnas = ("id", "nombre", "categoria")
        self.tree = ttk.Treeview(tree_frame, columns=columnas, show="headings", height=8)
        self.tree.pack(side='left', fill='x', expand=True)

        self.tree.heading("nombre", text="Nombre / Concepto")
        self.tree.heading("categoria", text="Categoría")
        self.tree.column("id", width=0, stretch=tk.NO)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x')
        ttk.Button(buttons_frame, text="Nuevo", command=self.abrir_ventana_nuevo, style="Action.TButton").pack(side="left", expand=True, fill='x', padx=(0,2))
        ttk.Button(buttons_frame, text="Modificar", command=self.abrir_ventana_modificar, style="Action.TButton").pack(side="left", expand=True, fill='x', padx=2)
        ttk.Button(buttons_frame, text="Eliminar", command=self.eliminar_seleccionado, style="Action.TButton").pack(side="left", expand=True, fill='x', padx=(2,0))

        self.actualizar_lista()

    def actualizar_lista(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        tipos = obligaciones_db.obtener_tipos_de_obligacion()
        for tipo in tipos:
            self.tree.insert("", "end", iid=tipo[0], values=tipo)
            
    def abrir_ventana_nuevo(self):
        VentanaObligacionTipo(self, on_success_callback=self.actualizar_lista)

    def abrir_ventana_modificar(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un ítem para modificar.")
            return
        tipo_id = self.tree.item(selected_item, "values")[0]
        VentanaObligacionTipo(self, on_success_callback=self.actualizar_lista, tipo_id=tipo_id)

    def eliminar_seleccionado(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un ítem para eliminar.")
            return
        tipo_id = self.tree.item(selected_item, "values")[0]
        nombre = self.tree.item(selected_item, "values")[1]
        
        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar '{nombre}'?", parent=self):
            resultado = obligaciones_db.eliminar_tipo_de_obligacion(tipo_id)
            if "correctamente" in resultado:
                messagebox.showinfo("Éxito", resultado)
                self.actualizar_lista()
            else:
                messagebox.showerror("Error", resultado)