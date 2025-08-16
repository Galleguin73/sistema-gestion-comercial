# En app/gui/empaquetado_frame.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.database import articulos_db
from .empaquetado_abm import ABMEmpaquetadoWindow

# --- CLASE MODIFICADA: Ahora es más simple y la llamamos VentanaProduccion ---
class VentanaProduccion(tk.Toplevel):
    def __init__(self, parent, articulo_a_producir):
        super().__init__(parent)
        self.parent = parent
        self.articulo_a_producir = articulo_a_producir # Tupla del Treeview

        self.title("Producir Artículo Empaquetado")
        self.geometry("450x200")
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding="10")
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        # Info del artículo que vamos a producir
        ttk.Label(frame, text="Producto a Producir:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(frame, text=f"{self.articulo_a_producir[3]}").grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(frame, text="Stock Actual:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(frame, text=f"{self.articulo_a_producir[4]}").grid(row=1, column=1, sticky="w", padx=5, pady=2)


        # Cantidad a producir
        ttk.Label(frame, text="Cantidad a Producir:", font=("Helvetica", 10, "bold")).grid(row=2, column=0, sticky="w", padx=5, pady=10)
        self.cantidad_entry = ttk.Entry(frame)
        self.cantidad_entry.grid(row=2, column=1, sticky="w", padx=5, pady=10)
        self.cantidad_entry.focus_set()

        # Botón de confirmación
        btn_confirmar = ttk.Button(frame, text="Confirmar Producción", command=self.confirmar)
        btn_confirmar.grid(row=3, column=0, columnspan=2, pady=20, padx=5, sticky="ew")

    def confirmar(self):
        try:
            cantidad = float(self.cantidad_entry.get())
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser positiva.")
        except ValueError:
            messagebox.showwarning("Dato Inválido", "Por favor, ingrese una cantidad numérica válida.", parent=self)
            return

        articulo_id = self.articulo_a_producir[0]
        
        # Llamamos a la nueva función de la base de datos
        resultado = articulos_db.realizar_produccion_empaquetado(articulo_id, cantidad)

        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self.parent)
            self.parent.actualizar_lista()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)


class EmpaquetadoFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_frame = ttk.Frame(self, style="Content.TFrame")
        top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=(10,0), sticky="ew")
        ttk.Label(top_frame, text="Empaquetado Propio", font=("Helvetica", 16, "bold")).pack(side="left")

        self.tree_frame = ttk.Frame(self, style="Content.TFrame")
        self.tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        columnas = ("id", "codigo", "marca", "nombre", "stock", "precio_venta")
        self.tree = ttk.Treeview(self.tree_frame, columns=columnas, show="headings",
                                 displaycolumns=("codigo", "nombre", "stock", "precio_venta"))
        self.tree.heading("id", text="ID")
        self.tree.heading("codigo", text="Código")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("precio_venta", text="Precio Venta")
        self.tree.column("codigo", width=150)
        self.tree.column("nombre", width=350)
        self.tree.column("stock", width=80, anchor='center')
        self.tree.column("precio_venta", width=100, anchor='e')
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.button_frame = ttk.Frame(self, style="Content.TFrame")
        self.button_frame.grid(row=1, column=1, padx=10, pady=10, sticky="ns")
        
        self.btn_abm = ttk.Button(self.button_frame, text="ABM Articulo", command=self.abrir_abm_empaquetado, style="Action.TButton")
        self.btn_abm.pack(pady=5, fill='x')
        
        self.btn_etiqueta = ttk.Button(self.button_frame, text="Imprimir Etiqueta", command=self.imprimir_etiqueta, style="Action.TButton")
        self.btn_etiqueta.pack(pady=5, fill='x')

        self.btn_actualizar_stock = ttk.Button(self.button_frame, text="Actualizar Stock", command=self.abrir_ventana_produccion, style="Action.TButton")
        self.btn_actualizar_stock.pack(pady=5, fill='x')

        self.actualizar_lista()

    def actualizar_lista(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        articulos_empaquetado = articulos_db.obtener_articulos_empaquetado()
        for articulo in articulos_empaquetado:
            self.tree.insert("", "end", values=articulo)
    
    def abrir_abm_empaquetado(self):
        abm_window = ABMEmpaquetadoWindow(self)
        self.wait_window(abm_window)
        self.actualizar_lista()

    def imprimir_etiqueta(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un artículo de la lista.")
            return
        valores = self.tree.item(selected_item, "values")
        nombre_articulo = valores[3]
        messagebox.showinfo("Función no implementada", f"La impresión de etiquetas para '{nombre_articulo}' aún no está disponible.")

    # --- MÉTODO MODIFICADO: Ahora abre la nueva ventana de Producción ---
    def abrir_ventana_produccion(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un artículo para producir.")
            return
        articulo_seleccionado = self.tree.item(selected_item, "values")
        VentanaProduccion(self, articulo_seleccionado)