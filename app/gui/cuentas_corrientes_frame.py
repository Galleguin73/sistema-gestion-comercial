# Archivo: app/gui/cuentas_corrientes_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
from app.database import clientes_db, proveedores_db
from .clientes_abm import ClientesFrame as ClientesABM
from .proveedores_abm import ProveedoresFrame as ProveedoresABM

class CuentasCorrientesFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestaña 1: Cuentas por Cobrar (Clientes)
        self.clientes_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(self.clientes_tab, text='Cuentas por Cobrar (Clientes)')
        self.crear_widgets_clientes()
        
        # Pestaña 2: Cuentas por Pagar (Proveedores)
        self.proveedores_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.notebook.add(self.proveedores_tab, text='Cuentas por Pagar (Proveedores)')
        self.crear_widgets_proveedores()
        
    def crear_widgets_clientes(self):
        frame = self.clientes_tab
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        tree_frame = ttk.LabelFrame(frame, text="Clientes con Saldo Pendiente", style="TLabelframe")
        tree_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        columnas = ("id", "nombre", "saldo")
        self.tree_clientes = ttk.Treeview(tree_frame, columns=columnas, show="headings")
        self.tree_clientes.heading("id", text="ID")
        self.tree_clientes.heading("nombre", text="Cliente")
        self.tree_clientes.heading("saldo", text="Saldo")
        self.tree_clientes.column("id", width=50, anchor="center")
        self.tree_clientes.column("saldo", anchor="e")
        self.tree_clientes.grid(row=0, column=0, sticky="nsew")
        
        # Lógica para refrescar la lista de clientes
        self.refrescar_clientes()
    
    def refrescar_clientes(self):
        for row in self.tree_clientes.get_children():
            self.tree_clientes.delete(row)
        
        clientes = clientes_db.obtener_clientes_con_saldo()
        for cliente in clientes:
            id_cliente, nombre, saldo = cliente
            valores = (id_cliente, nombre, f"$ {saldo:,.2f}")
            self.tree_clientes.insert("", "end", values=valores)

    def crear_widgets_proveedores(self):
        frame = self.proveedores_tab
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        tree_frame = ttk.LabelFrame(frame, text="Proveedores con Saldo Pendiente", style="TLabelframe")
        tree_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        columnas = ("id", "nombre", "saldo")
        self.tree_proveedores = ttk.Treeview(tree_frame, columns=columnas, show="headings")
        self.tree_proveedores.heading("id", text="ID")
        self.tree_proveedores.heading("nombre", text="Proveedor")
        self.tree_proveedores.heading("saldo", text="Saldo")
        self.tree_proveedores.column("id", width=50, anchor="center")
        self.tree_proveedores.column("saldo", anchor="e")
        self.tree_proveedores.grid(row=0, column=0, sticky="nsew")
        
        self.refrescar_proveedores()
        
    def refrescar_proveedores(self):
        for row in self.tree_proveedores.get_children():
            self.tree_proveedores.delete(row)
            
        proveedores = proveedores_db.obtener_proveedores_con_saldo()
        for proveedor in proveedores:
            id_prov, nombre, saldo = proveedor
            valores = (id_prov, nombre, f"$ {saldo:,.2f}")
            self.tree_proveedores.insert("", "end", values=valores)