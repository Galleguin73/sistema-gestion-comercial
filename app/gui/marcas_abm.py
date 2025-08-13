import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import articulos_db

class MarcasFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent)
        self.style = style

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = ttk.LabelFrame(self, text="Marcas", style="TLabelframe")
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(main_frame, columns=("ID", "Nombre"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        
        btn_agregar = ttk.Button(main_frame, text="Agregar", command=self.agregar_marca, style="Action.TButton")
        btn_agregar.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        btn_modificar = ttk.Button(main_frame, text="Modificar", command=self.modificar_marca, style="Action.TButton")
        btn_modificar.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        btn_eliminar = ttk.Button(main_frame, text="Eliminar", command=self.eliminar_marca, style="Action.TButton")
        btn_eliminar.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        self.actualizar_lista()

    def actualizar_lista(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for marca in articulos_db.obtener_marcas():
            self.tree.insert("", "end", values=marca)

    def agregar_marca(self):
        nombre = simpledialog.askstring("Nueva Marca", "Ingrese el nombre de la nueva marca:", parent=self)
        if nombre:
            resultado = articulos_db.agregar_marca(nombre)
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista()

    def modificar_marca(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una marca para modificar.")
            return
        marca_id = self.tree.item(selected_item, "values")[0]
        nombre_actual = self.tree.item(selected_item, "values")[1]
        
        nuevo_nombre = simpledialog.askstring("Modificar Marca", "Ingrese el nuevo nombre:", initialvalue=nombre_actual, parent=self)
        if nuevo_nombre and nuevo_nombre != nombre_actual:
            resultado = articulos_db.modificar_marca(marca_id, nuevo_nombre)
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista()

    def eliminar_marca(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una marca para eliminar.")
            return
        marca_id = self.tree.item(selected_item, "values")[0]
        nombre = self.tree.item(selected_item, "values")[1]
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la marca '{nombre}'?"):
            resultado = articulos_db.eliminar_marca(marca_id)
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista()