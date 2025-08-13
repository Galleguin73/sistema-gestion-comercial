import tkinter as tk
from tkinter import ttk, messagebox
from app.database import ventas_db, clientes_db, proveedores_db
from datetime import datetime
from tkcalendar import DateEntry

class ReportesFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Creamos los frames de las pestañas
        self.ventas_periodo_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.ventas_articulo_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.ventas_marca_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.ventas_rubro_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.ventas_subrubro_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.cc_clientes_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.cc_proveedores_tab = ttk.Frame(self.notebook, style="Content.TFrame")

        # Añadimos las pestañas al notebook
        self.notebook.add(self.ventas_periodo_tab, text='Ventas por Período')
        self.notebook.add(self.ventas_articulo_tab, text='Ventas por Artículo')
        self.notebook.add(self.ventas_marca_tab, text='Ventas por Marca')
        self.notebook.add(self.ventas_rubro_tab, text='Ventas por Rubro')
        self.notebook.add(self.ventas_subrubro_tab, text='Ventas por Subrubro')
        self.notebook.add(self.cc_clientes_tab, text='Cta. Cte. Clientes')
        self.notebook.add(self.cc_proveedores_tab, text='Cta. Cte. Proveedores')
        
        # Creamos los widgets para la primera pestaña visible
        self.crear_widgets_ventas_periodo()
        
        # Vinculamos el evento de cambio de pestaña a una nueva función
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        """Se ejecuta cada vez que el usuario cambia de pestaña."""
        selected_tab = self.notebook.index(self.notebook.select())
        
        # Verificamos si la pestaña ya tiene widgets. Si no, los crea.
        # Esto asegura que los widgets (y las consultas a la BD) se creen solo una vez.
        if selected_tab == 1 and not self.ventas_articulo_tab.winfo_children():
            self.crear_widgets_ventas_articulo()
        elif selected_tab == 2 and not self.ventas_marca_tab.winfo_children():
            self.crear_widgets_ventas_marca()
        elif selected_tab == 3 and not self.ventas_rubro_tab.winfo_children():
            self.crear_widgets_ventas_rubro()
        elif selected_tab == 4 and not self.ventas_subrubro_tab.winfo_children():
            self.crear_widgets_ventas_subrubro()
        elif selected_tab == 5 and not self.cc_clientes_tab.winfo_children():
            self.crear_widgets_cc_clientes()
        elif selected_tab == 6 and not self.cc_proveedores_tab.winfo_children():
            self.crear_widgets_cc_proveedores()

    def _crear_widgets_filtro(self, parent_frame, cmd):
        filtros_frame = ttk.LabelFrame(parent_frame, text="Filtros", style="TLabelframe")
        filtros_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Label(filtros_frame, text="Fecha Desde:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        fecha_desde_entry = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12, background='darkblue', foreground='white', borderwidth=2)
        fecha_desde_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filtros_frame, text="Fecha Hasta:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        fecha_hasta_entry = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12, background='darkblue', foreground='white', borderwidth=2)
        fecha_hasta_entry.grid(row=0, column=3, padx=5, pady=5)

        btn_generar = ttk.Button(filtros_frame, text="Generar", command=lambda: cmd(fecha_desde_entry.get(), fecha_hasta_entry.get()), style="Action.TButton")
        btn_generar.grid(row=0, column=4, padx=10, pady=5)
        
        return fecha_desde_entry, fecha_hasta_entry

   
    def crear_widgets_ventas_periodo(self):
        frame = self.ventas_periodo_tab
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.vp_fecha_desde, self.vp_fecha_hasta = self._crear_widgets_filtro(frame, self.generar_reporte_ventas_periodo)
        
        resultados_frame = ttk.Frame(frame, style="Content.TFrame")
        resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        resultados_frame.grid_rowconfigure(0, weight=1)
        resultados_frame.grid_columnconfigure(0, weight=1)

        columnas = ("id", "fecha", "cliente", "comprobante", "total")
        self.tree_ventas_periodo = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_ventas_periodo.heading("id", text="ID Venta")
        self.tree_ventas_periodo.heading("fecha", text="Fecha")
        self.tree_ventas_periodo.heading("cliente", text="Cliente")
        self.tree_ventas_periodo.heading("comprobante", text="Comprobante")
        self.tree_ventas_periodo.heading("total", text="Monto Total")
        self.tree_ventas_periodo.column("id", width=80, anchor="center")
        self.tree_ventas_periodo.column("total", anchor="e")
        self.tree_ventas_periodo.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_periodo.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree_ventas_periodo.configure(yscrollcommand=scrollbar.set)

        total_frame = ttk.Frame(frame, style="Content.TFrame")
        total_frame.grid(row=2, column=0, padx=10, pady=10, sticky="e")
        ttk.Label(total_frame, text="Total Facturado:", font=("Helvetica", 12, "bold"), style="TLabel").pack(side="left")
        self.vp_total_label = ttk.Label(total_frame, text="$ 0.00", font=("Helvetica", 12, "bold"), style="TLabel")
        self.vp_total_label.pack(side="left")

    def generar_reporte_ventas_periodo(self, fecha_desde, fecha_hasta):
        if not fecha_desde or not fecha_hasta:
            messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas.")
            return
        for row in self.tree_ventas_periodo.get_children(): self.tree_ventas_periodo.delete(row)
        ventas = ventas_db.obtener_ventas_por_periodo(fecha_desde, fecha_hasta)
        total_periodo = 0.0
        for venta in ventas:
            try:
                fecha_obj = datetime.strptime(venta[1], '%Y-%m-%d %H:%M:%S.%f')
                fecha_formateada = fecha_obj.strftime('%d/%m/%Y %H:%M')
            except ValueError:
                fecha_formateada = venta[1]
            monto_total = venta[4]
            total_periodo += monto_total
            self.tree_ventas_periodo.insert("", "end", values=(venta[0], fecha_formateada, venta[2], venta[3], f"$ {monto_total:.2f}"))
        self.vp_total_label.config(text=f"$ {total_periodo:.2f}")

    def crear_widgets_ventas_articulo(self):
        frame = self.ventas_articulo_tab
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.va_fecha_desde, self.va_fecha_hasta = self._crear_widgets_filtro(frame, self.generar_reporte_ventas_articulo)
        
        resultados_frame = ttk.Frame(frame, style="Content.TFrame")
        resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        resultados_frame.grid_rowconfigure(0, weight=1)
        resultados_frame.grid_columnconfigure(0, weight=1)

        columnas = ("codigo", "nombre", "marca", "cantidad", "total")
        self.tree_ventas_articulo = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_ventas_articulo.heading("codigo", text="Código")
        self.tree_ventas_articulo.heading("nombre", text="Artículo")
        self.tree_ventas_articulo.heading("marca", text="Marca")
        self.tree_ventas_articulo.heading("cantidad", text="Cant. Vendida")
        self.tree_ventas_articulo.heading("total", text="Total Vendido")
        self.tree_ventas_articulo.column("cantidad", anchor="center")
        self.tree_ventas_articulo.column("total", anchor="e")
        self.tree_ventas_articulo.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_articulo.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree_ventas_articulo.configure(yscrollcommand=scrollbar.set)

    def generar_reporte_ventas_articulo(self, fecha_desde, fecha_hasta):
        if not fecha_desde or not fecha_hasta:
            messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas.")
            return
        for row in self.tree_ventas_articulo.get_children(): self.tree_ventas_articulo.delete(row)
        articulos = ventas_db.reporte_ventas_por_articulo(fecha_desde, fecha_hasta)
        for art in articulos:
            valores = (art[0], art[1], art[2], f"{art[3]:.2f}", f"$ {art[4]:.2f}")
            self.tree_ventas_articulo.insert("", "end", values=valores)

    def crear_widgets_ventas_marca(self):
        frame = self.ventas_marca_tab
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.vm_fecha_desde, self.vm_fecha_hasta = self._crear_widgets_filtro(frame, self.generar_reporte_ventas_marca)

        resultados_frame = ttk.Frame(frame, style="Content.TFrame")
        resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        resultados_frame.grid_rowconfigure(0, weight=1)
        resultados_frame.grid_columnconfigure(0, weight=1)

        columnas = ("marca", "cantidad", "total")
        self.tree_ventas_marca = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_ventas_marca.heading("marca", text="Marca")
        self.tree_ventas_marca.heading("cantidad", text="Cant. Vendida")
        self.tree_ventas_marca.heading("total", text="Total Vendido")
        self.tree_ventas_marca.column("cantidad", anchor="center")
        self.tree_ventas_marca.column("total", anchor="e")
        self.tree_ventas_marca.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_marca.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree_ventas_marca.configure(yscrollcommand=scrollbar.set)

    def generar_reporte_ventas_marca(self, fecha_desde, fecha_hasta):
        if not fecha_desde or not fecha_hasta:
            messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas.")
            return
        for row in self.tree_ventas_marca.get_children(): self.tree_ventas_marca.delete(row)
        marcas = ventas_db.reporte_ventas_por_marca(fecha_desde, fecha_hasta)
        for marca in marcas:
            valores = (marca[0], f"{marca[1]:.2f}", f"$ {marca[2]:.2f}")
            self.tree_ventas_marca.insert("", "end", values=valores)

    def crear_widgets_ventas_rubro(self):
        frame = self.ventas_rubro_tab
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.vr_fecha_desde, self.vr_fecha_hasta = self._crear_widgets_filtro(frame, self.generar_reporte_ventas_rubro)

        resultados_frame = ttk.Frame(frame, style="Content.TFrame")
        resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        resultados_frame.grid_rowconfigure(0, weight=1)
        resultados_frame.grid_columnconfigure(0, weight=1)

        columnas = ("rubro", "cantidad", "total")
        self.tree_ventas_rubro = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_ventas_rubro.heading("rubro", text="Rubro")
        self.tree_ventas_rubro.heading("cantidad", text="Cant. Vendida")
        self.tree_ventas_rubro.heading("total", text="Total Vendido")
        self.tree_ventas_rubro.column("cantidad", anchor="center")
        self.tree_ventas_rubro.column("total", anchor="e")
        self.tree_ventas_rubro.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_rubro.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree_ventas_rubro.configure(yscrollcommand=scrollbar.set)
        
    def generar_reporte_ventas_rubro(self, fecha_desde, fecha_hasta):
        if not fecha_desde or not fecha_hasta:
            messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas.")
            return
        for row in self.tree_ventas_rubro.get_children(): self.tree_ventas_rubro.delete(row)
        rubros = ventas_db.reporte_ventas_por_rubro(fecha_desde, fecha_hasta)
        for rubro in rubros:
            valores = (rubro[0], f"{rubro[1]:.2f}", f"$ {rubro[2]:.2f}")
            self.tree_ventas_rubro.insert("", "end", values=valores)

    def crear_widgets_ventas_subrubro(self):
        frame = self.ventas_subrubro_tab
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.vs_fecha_desde, self.vs_fecha_hasta = self._crear_widgets_filtro(frame, self.generar_reporte_ventas_subrubro)

        resultados_frame = ttk.Frame(frame, style="Content.TFrame")
        resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        resultados_frame.grid_rowconfigure(0, weight=1)
        resultados_frame.grid_columnconfigure(0, weight=1)

        columnas = ("subrubro", "rubro", "cantidad", "total")
        self.tree_ventas_subrubro = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_ventas_subrubro.heading("subrubro", text="Subrubro")
        self.tree_ventas_subrubro.heading("rubro", text="Rubro")
        self.tree_ventas_subrubro.heading("cantidad", text="Cant. Vendida")
        self.tree_ventas_subrubro.heading("total", text="Total Vendido")
        self.tree_ventas_subrubro.column("cantidad", anchor="center")
        self.tree_ventas_subrubro.column("total", anchor="e")
        self.tree_ventas_subrubro.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_subrubro.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree_ventas_subrubro.configure(yscrollcommand=scrollbar.set)

    def generar_reporte_ventas_subrubro(self, fecha_desde, fecha_hasta):
        if not fecha_desde or not fecha_hasta:
            messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas.")
            return
        for row in self.tree_ventas_subrubro.get_children(): self.tree_ventas_subrubro.delete(row)
        subrubros = ventas_db.reporte_ventas_por_subrubro(fecha_desde, fecha_hasta)
        for subrubro in subrubros:
            valores = (subrubro[0], subrubro[1], f"{subrubro[2]:.2f}", f"$ {subrubro[3]:.2f}")
            self.tree_ventas_subrubro.insert("", "end", values=valores)

    def crear_widgets_cc_clientes(self):
        frame = self.cc_clientes_tab
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        filtros_frame = ttk.LabelFrame(frame, text="Filtros", style="TLabelframe")
        filtros_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Label(filtros_frame, text="Seleccionar Cliente:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ccc_cliente_combo = ttk.Combobox(filtros_frame, state="readonly", width=30)
        self.ccc_cliente_combo.grid(row=0, column=1, padx=5, pady=5)
        
        self.clientes_data = clientes_db.obtener_todos_los_clientes_para_reporte()
        self.ccc_cliente_combo['values'] = [c[1] for c in self.clientes_data]
        
        ttk.Label(filtros_frame, text="Desde:").grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")
        self.ccc_fecha_desde = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12)
        self.ccc_fecha_desde.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filtros_frame, text="Hasta:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.ccc_fecha_hasta = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12)
        self.ccc_fecha_hasta.grid(row=0, column=5, padx=5, pady=5)

        btn_generar = ttk.Button(filtros_frame, text="Generar", command=self.generar_reporte_cc_cliente, style="Action.TButton")
        btn_generar.grid(row=0, column=6, padx=10, pady=5)

        resultados_frame = ttk.Frame(frame, style="Content.TFrame")
        resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        resultados_frame.grid_rowconfigure(0, weight=1)
        resultados_frame.grid_columnconfigure(0, weight=1)

        columnas = ("fecha", "tipo", "monto", "saldo")
        self.tree_cc_clientes = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_cc_clientes.heading("fecha", text="Fecha")
        self.tree_cc_clientes.heading("tipo", text="Tipo Movimiento")
        self.tree_cc_clientes.heading("monto", text="Monto")
        self.tree_cc_clientes.heading("saldo", text="Saldo Resultante")
        self.tree_cc_clientes.column("monto", anchor="e")
        self.tree_cc_clientes.column("saldo", anchor="e")
        self.tree_cc_clientes.grid(row=0, column=0, sticky="nsew")

    def generar_reporte_cc_cliente(self):
        cliente_nombre = self.ccc_cliente_combo.get()
        if not cliente_nombre:
            messagebox.showwarning("Dato Faltante", "Por favor, seleccione un cliente.")
            return
        
        cliente_id = next(cid for cid, nombre in self.clientes_data if nombre == cliente_nombre)
        fecha_desde = self.ccc_fecha_desde.get()
        fecha_hasta = self.ccc_fecha_hasta.get()

        for row in self.tree_cc_clientes.get_children(): self.tree_cc_clientes.delete(row)

        movimientos = clientes_db.obtener_cuenta_corriente_cliente(cliente_id, fecha_desde, fecha_hasta)
        for mov in movimientos:
            valores = (mov[0], mov[1], f"$ {mov[2]:.2f}", f"$ {mov[3]:.2f}")
            self.tree_cc_clientes.insert("", "end", values=valores)

    def crear_widgets_cc_proveedores(self):
        frame = self.cc_proveedores_tab
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        filtros_frame = ttk.LabelFrame(frame, text="Filtros", style="TLabelframe")
        filtros_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Label(filtros_frame, text="Seleccionar Proveedor:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ccp_proveedor_combo = ttk.Combobox(filtros_frame, state="readonly", width=30)
        self.ccp_proveedor_combo.grid(row=0, column=1, padx=5, pady=5)
        
        self.proveedores_data = proveedores_db.obtener_todos_los_proveedores_para_reporte()
        self.ccp_proveedor_combo['values'] = [p[1] for p in self.proveedores_data]

        ttk.Label(filtros_frame, text="Desde:").grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")
        self.ccp_fecha_desde = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12)
        self.ccp_fecha_desde.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filtros_frame, text="Hasta:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.ccp_fecha_hasta = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12)
        self.ccp_fecha_hasta.grid(row=0, column=5, padx=5, pady=5)

        btn_generar = ttk.Button(filtros_frame, text="Generar", command=self.generar_reporte_cc_proveedor, style="Action.TButton")
        btn_generar.grid(row=0, column=6, padx=10, pady=5)
        
        resultados_frame = ttk.Frame(frame, style="Content.TFrame")
        resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        resultados_frame.grid_rowconfigure(0, weight=1)
        resultados_frame.grid_columnconfigure(0, weight=1)

        columnas = ("fecha", "tipo", "monto", "saldo")
        self.tree_cc_proveedores = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_cc_proveedores.heading("fecha", text="Fecha")
        self.tree_cc_proveedores.heading("tipo", text="Tipo Movimiento")
        self.tree_cc_proveedores.heading("monto", text="Monto")
        self.tree_cc_proveedores.heading("saldo", text="Saldo Resultante")
        self.tree_cc_proveedores.column("monto", anchor="e")
        self.tree_cc_proveedores.column("saldo", anchor="e")
        self.tree_cc_proveedores.grid(row=0, column=0, sticky="nsew")

    def generar_reporte_cc_proveedor(self):
        proveedor_nombre = self.ccp_proveedor_combo.get()
        if not proveedor_nombre:
            messagebox.showwarning("Dato Faltante", "Por favor, seleccione un proveedor.")
            return
        
        proveedor_id = next(pid for pid, nombre in self.proveedores_data if nombre == proveedor_nombre)
        fecha_desde = self.ccp_fecha_desde.get()
        fecha_hasta = self.ccp_fecha_hasta.get()
        
        for row in self.tree_cc_proveedores.get_children(): self.tree_cc_proveedores.delete(row)

        movimientos = proveedores_db.obtener_cuenta_corriente_proveedor(proveedor_id, fecha_desde, fecha_hasta)
        for mov in movimientos:
            valores = (mov[0], mov[1], f"$ {mov[2]:.2f}", f"$ {mov[3]:.2f}")
            self.tree_cc_proveedores.insert("", "end", values=valores)