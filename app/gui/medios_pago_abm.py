import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import config_db # Importación corregida

class MediosPagoFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent)
        self.style = style

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = ttk.LabelFrame(self, text="Medios de Pago", style="TLabelframe")
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(main_frame, columns=("ID", "Nombre"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        
        btn_agregar = ttk.Button(main_frame, text="Agregar", command=self.agregar, style="Action.TButton")
        btn_agregar.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        btn_modificar = ttk.Button(main_frame, text="Modificar", command=self.modificar, style="Action.TButton")
        btn_modificar.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        btn_eliminar = ttk.Button(main_frame, text="Eliminar", command=self.eliminar, style="Action.TButton")
        btn_eliminar.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        self.actualizar_lista()

    def actualizar_lista(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for medio in config_db.obtener_medios_de_pago(): # Referencia actualizada
            self.tree.insert("", "end", values=medio)

    def agregar(self):
        nombre = simpledialog.askstring("Nuevo Medio de Pago", "Ingrese el nombre:", parent=self)
        if nombre:
            resultado = config_db.agregar_medio_pago(nombre) # Referencia actualizada
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista()

    def modificar(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un medio de pago para modificar.")
            return
        item_id = self.tree.item(selected_item, "values")[0]
        nombre_actual = self.tree.item(selected_item, "values")[1]
        
        nuevo_nombre = simpledialog.askstring("Modificar", "Ingrese el nuevo nombre:", initialvalue=nombre_actual, parent=self)
        if nuevo_nombre and nuevo_nombre != nombre_actual:
            resultado = config_db.modificar_medio_pago(item_id, nuevo_nombre) # Referencia actualizada
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista()

    def eliminar(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un medio de pago para eliminar.")
            return
        item_id = self.tree.item(selected_item, "values")[0]
        nombre = self.tree.item(selected_item, "values")[1]
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar '{nombre}'?"):
            resultado = config_db.eliminar_medio_pago(item_id) # Referencia actualizada
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista()