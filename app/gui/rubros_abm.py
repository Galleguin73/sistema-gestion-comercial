import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import articulos_db

class RubrosFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent)
        self.style = style

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        rubros_frame = ttk.LabelFrame(self, text="Rubros", style="TLabelframe")
        rubros_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        rubros_frame.rowconfigure(0, weight=1)
        rubros_frame.columnconfigure(0, weight=1)

        self.tree_rubros = ttk.Treeview(rubros_frame, columns=("ID", "Nombre"), show="headings")
        self.tree_rubros.heading("ID", text="ID")
        self.tree_rubros.heading("Nombre", text="Nombre")
        self.tree_rubros.column("ID", width=50, anchor="center")
        self.tree_rubros.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.tree_rubros.bind("<<TreeviewSelect>>", self.actualizar_lista_subrubros)

        btn_agregar_rubro = ttk.Button(rubros_frame, text="Agregar Rubro", command=self.agregar_rubro, style="Action.TButton")
        btn_agregar_rubro.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        btn_eliminar_rubro = ttk.Button(rubros_frame, text="Eliminar Rubro", command=self.eliminar_rubro, style="Action.TButton")
        btn_eliminar_rubro.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        subrubros_frame = ttk.LabelFrame(self, text="Subrubros (del rubro seleccionado)", style="TLabelframe")
        subrubros_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        subrubros_frame.rowconfigure(0, weight=1)
        subrubros_frame.columnconfigure(0, weight=1)

        self.tree_subrubros = ttk.Treeview(subrubros_frame, columns=("ID", "Nombre"), show="headings")
        self.tree_subrubros.heading("ID", text="ID")
        self.tree_subrubros.heading("Nombre", text="Nombre")
        self.tree_subrubros.column("ID", width=50, anchor="center")
        self.tree_subrubros.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        btn_agregar_subrubro = ttk.Button(subrubros_frame, text="Agregar Subrubro", command=self.agregar_subrubro, style="Action.TButton")
        btn_agregar_subrubro.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        btn_eliminar_subrubro = ttk.Button(subrubros_frame, text="Eliminar Subrubro", command=self.eliminar_subrubro, style="Action.TButton")
        btn_eliminar_subrubro.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.actualizar_lista_rubros()

    def actualizar_lista_rubros(self):
        for row in self.tree_rubros.get_children():
            self.tree_rubros.delete(row)
        for rubro in articulos_db.obtener_rubros():
            self.tree_rubros.insert("", "end", values=rubro)
        self.actualizar_lista_subrubros()

    def actualizar_lista_subrubros(self, event=None):
        for row in self.tree_subrubros.get_children():
            self.tree_subrubros.delete(row)
        
        selected_item = self.tree_rubros.focus()
        if selected_item:
            rubro_id = self.tree_rubros.item(selected_item, "values")[0]
            for subrubro in articulos_db.obtener_subrubros_por_rubro(rubro_id):
                self.tree_subrubros.insert("", "end", values=subrubro)

    def agregar_rubro(self):
        nombre = simpledialog.askstring("Nuevo Rubro", "Ingrese el nombre del nuevo rubro:", parent=self)
        if nombre:
            resultado = articulos_db.agregar_rubro(nombre)
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista_rubros()

    def eliminar_rubro(self):
        selected_item = self.tree_rubros.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un rubro para eliminar.")
            return
        rubro_id = self.tree_rubros.item(selected_item, "values")[0]
        nombre = self.tree_rubros.item(selected_item, "values")[1]
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el rubro '{nombre}'? Se eliminarán todos sus subrubros asociados."):
            resultado = articulos_db.eliminar_rubro(rubro_id)
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista_rubros()
            
    def agregar_subrubro(self):
        selected_item = self.tree_rubros.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un rubro para agregarle un subrubro.")
            return
        rubro_id = self.tree_rubros.item(selected_item, "values")[0]
        nombre = simpledialog.askstring("Nuevo Subrubro", "Ingrese el nombre del nuevo subrubro:", parent=self)
        if nombre:
            resultado = articulos_db.agregar_subrubro(nombre, rubro_id)
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista_subrubros()

    def eliminar_subrubro(self):
        selected_item = self.tree_subrubros.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un subrubro para eliminar.")
            return
        subrubro_id = self.tree_subrubros.item(selected_item, "values")[0]
        nombre = self.tree_subrubros.item(selected_item, "values")[1]
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el subrubro '{nombre}'?"):
            resultado = articulos_db.eliminar_subrubro(subrubro_id)
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista_subrubros()