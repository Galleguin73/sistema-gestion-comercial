import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from app.database import ventas_db, clientes_db, proveedores_db, compras_db, articulos_db
from datetime import datetime
from tkcalendar import DateEntry
from collections import defaultdict
from app.reports import report_generator, excel_exporter, ticket_generator
import os
import webbrowser

# --- CLASE PARA VER EL DETALLE DE LA VENTA (CORREGIDA) ---
class VentanaVerDetalleVenta(tk.Toplevel):
    def __init__(self, parent, venta_id):
        super().__init__(parent)
        self.title(f"Detalle de Venta ID: {venta_id}")
        self.geometry("750x550")
        self.transient(parent)
        self.grab_set()

        encabezado = ventas_db.obtener_venta_completa_por_id(venta_id)
        detalles = ventas_db.obtener_detalle_venta_completo(venta_id)

        if not encabezado:
            messagebox.showerror("Error", f"No se pudo cargar la venta con ID {venta_id}.", parent=self)
            self.destroy()
            return
            
        header_frame = ttk.LabelFrame(self, text="Datos del Comprobante", padding=10)
        header_frame.pack(padx=10, pady=10, fill="x")
        
        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(3, weight=1)
        
        # --- LÍNEA CORREGIDA ---
        # Leemos la clave 'fecha_venta' que es la correcta según tu base de datos
        fecha_dt = datetime.strptime(encabezado['fecha_venta'], '%Y-%m-%d %H:%M:%S.%f')
        
        ttk.Label(header_frame, text="Fecha:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header_frame, text=fecha_dt.strftime('%d/%m/%Y %H:%M')).grid(row=0, column=1, sticky="w")
        
        ttk.Label(header_frame, text="Cliente:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky="w")
        ttk.Label(header_frame, text=encabezado['cliente_nombre']).grid(row=1, column=1, columnspan=3, sticky="w")
        
        ttk.Label(header_frame, text="Comprobante:", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky="w", padx=(10,0))
        ttk.Label(header_frame, text=encabezado['tipo_comprobante']).grid(row=0, column=3, sticky="w")
        
        ttk.Label(header_frame, text="Estado:", font=("Helvetica", 10, "bold")).grid(row=2, column=0, sticky="w")
        ttk.Label(header_frame, text=encabezado['estado']).grid(row=2, column=1, sticky="w")

        # --- LÍNEA CORREGIDA ---
        # Usamos 'monto_total' que es el nombre correcto en tu DB
        ttk.Label(header_frame, text=f"Total: $ {encabezado['monto_total']:.2f}", font=("Helvetica", 12, "bold")).grid(row=3, column=0, columnspan=4, sticky="w", pady=10)

        items_frame = ttk.LabelFrame(self, text="Artículos Vendidos", padding=10)
        items_frame.pack(padx=10, pady=5, fill="both", expand=True)
        items_frame.rowconfigure(0, weight=1); items_frame.columnconfigure(0, weight=1)
        
        columnas = ("cantidad", "descripcion", "p_unit", "subtotal")
        tree = ttk.Treeview(items_frame, columns=columnas, show="headings")
        tree.heading("cantidad", text="Cantidad"); tree.heading("descripcion", text="Descripción"); tree.heading("p_unit", text="P. Unit."); tree.heading("subtotal", text="Subtotal")
        tree.column("cantidad", anchor="center", width=80); tree.column("p_unit", anchor="e", width=100); tree.column("subtotal", anchor="e", width=100)
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=tree.yview); scrollbar.grid(row=0, column=1, sticky="ns"); tree.configure(yscrollcommand=scrollbar.set)

        for item in detalles:
            # item = (descripcion, cantidad, precio_unitario, subtotal, marca_nombre)
            descripcion_completa = f"{item[4]} - {item[0]}" if item[4] else item[0]
            valores = (f"{item[1]:.2f}", descripcion_completa, f"$ {item[2]:.2f}", f"$ {item[3]:.2f}")
            tree.insert("", "end", values=valores)
            
        ttk.Button(self, text="Cerrar", command=self.destroy, style="Action.TButton").pack(pady=10)


class ReportesFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.ventas_periodo_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.compras_periodo_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.listados_articulos_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.ventas_categorias_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.ventas_articulo_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        self.ventas_marca_tab = ttk.Frame(self.notebook, style="Content.TFrame")
        
        self.notebook.add(self.ventas_periodo_tab, text='Ventas por Período')
        self.notebook.add(self.compras_periodo_tab, text='Compras por Período')
        self.notebook.add(self.listados_articulos_tab, text='Listados de Artículos')
        self.notebook.add(self.ventas_categorias_tab, text='Ventas por Categorías')
        self.notebook.add(self.ventas_articulo_tab, text='Ventas por Artículo')
        self.notebook.add(self.ventas_marca_tab, text='Ventas por Marca')
        
        self.crear_widgets_ventas_periodo()
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        selected_tab_index = self.notebook.index(self.notebook.select())
        tab_widgets_map = {
            1: (self.compras_periodo_tab, self.crear_widgets_compras_periodo),
            2: (self.listados_articulos_tab, self.crear_widgets_listados_articulos),
            3: (self.ventas_categorias_tab, self.crear_widgets_ventas_categorias),
            4: (self.ventas_articulo_tab, self.crear_widgets_ventas_articulo),
            5: (self.ventas_marca_tab, self.crear_widgets_ventas_marca),
        }
        if selected_tab_index in tab_widgets_map:
            tab, creator_func = tab_widgets_map[selected_tab_index]
            if not tab.winfo_children():
                creator_func()

    def _exportar_a_excel(self, exporter_func, initial_filename, *args):
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx",filetypes=[("Archivos de Excel", "*.xlsx")],title=f"Guardar {initial_filename}",initialfile=f"{initial_filename}_{datetime.now().strftime('%Y%m%d')}.xlsx")
        if not filepath: return
        try:
            success, message = exporter_func(filepath, *args)
            if success: messagebox.showinfo("Éxito", message, parent=self)
            else: messagebox.showerror("Error", message, parent=self)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"No se pudo generar el archivo de Excel:\n{e}", parent=self)

    def _crear_widgets_filtro_fechas(self, parent_frame, cmd_generar, cmd_exportar):
        filtros_frame = ttk.LabelFrame(parent_frame, text="Filtros", style="TLabelframe")
        filtros_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(filtros_frame, text="Desde:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        fecha_desde = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12)
        fecha_desde.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(filtros_frame, text="Hasta:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        fecha_hasta = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12)
        fecha_hasta.grid(row=0, column=3, padx=5, pady=5)
        btn_generar = ttk.Button(filtros_frame, text="Generar Vista", command=lambda: cmd_generar(fecha_desde.get(), fecha_hasta.get()), style="Action.TButton")
        btn_generar.grid(row=0, column=4, padx=10, pady=5)
        btn_exportar = ttk.Button(filtros_frame, text="Exportar a Excel", command=lambda: cmd_exportar(fecha_desde.get(), fecha_hasta.get()), style="Action.TButton")
        btn_exportar.grid(row=0, column=5, padx=10, pady=5)
        return fecha_desde, fecha_hasta
    
    def crear_widgets_ventas_periodo(self):
        frame = self.ventas_periodo_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.vp_fecha_desde, self.vp_fecha_hasta = self._crear_widgets_filtro_fechas(frame, self.generar_reporte_ventas_periodo, lambda d, h: self._exportar_a_excel(excel_exporter.exportar_ventas_periodo, "Ventas_por_Periodo", d, h))
        
        resultados_frame = ttk.Frame(frame, style="Content.TFrame")
        resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        columnas = ("id", "fecha", "cliente", "comprobante", "total", "estado")
        self.tree_ventas_periodo = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_ventas_periodo.heading("id", text="ID Venta"); self.tree_ventas_periodo.heading("fecha", text="Fecha"); self.tree_ventas_periodo.heading("cliente", text="Cliente"); self.tree_ventas_periodo.heading("comprobante", text="Comprobante"); self.tree_ventas_periodo.heading("total", text="Monto Total"); self.tree_ventas_periodo.heading("estado", text="Estado")
        self.tree_ventas_periodo.column("id", width=80, anchor="center"); self.tree_ventas_periodo.column("total", anchor="e"); self.tree_ventas_periodo.column("estado", width=100, anchor="center")
        self.tree_ventas_periodo.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_periodo.yview)
        scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_ventas_periodo.configure(yscrollcommand=scrollbar.set)

        acciones_frame = ttk.Frame(frame, style="Content.TFrame")
        acciones_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")
        
        btn_ver_detalle = ttk.Button(acciones_frame, text="Ver Detalle", command=self._ver_detalle_venta, style="Action.TButton")
        btn_ver_detalle.pack(side="left", padx=(0, 5))
        btn_imprimir = ttk.Button(acciones_frame, text="Imprimir Comprobante", command=self._imprimir_comprobante, style="Action.TButton")
        btn_imprimir.pack(side="left", padx=5)
        btn_anular_venta = ttk.Button(acciones_frame, text="Anular Venta", command=self.anular_venta_seleccionada, style="Action.TButton")
        btn_anular_venta.pack(side="left", padx=5)

        total_frame = ttk.Frame(frame, style="Content.TFrame"); total_frame.grid(row=3, column=0, padx=10, pady=10, sticky="e")
        ttk.Label(total_frame, text="Total Facturado:", font=("Helvetica", 12, "bold")).pack(side="left")
        self.vp_total_label = ttk.Label(total_frame, text="$ 0.00", font=("Helvetica", 12, "bold")); self.vp_total_label.pack(side="left")

    def _ver_detalle_venta(self):
        selected_item = self.tree_ventas_periodo.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Por favor, seleccione una venta de la lista.", parent=self); return
        venta_id = self.tree_ventas_periodo.item(selected_item, "values")[0]
        VentanaVerDetalleVenta(self, venta_id)
        
    def _imprimir_comprobante(self):
        selected_item = self.tree_ventas_periodo.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Por favor, seleccione una venta para imprimir.", parent=self); return
        venta_id = self.tree_ventas_periodo.item(selected_item, "values")[0]
        try:
            filepath, msg = ticket_generator.crear_comprobante_venta(venta_id)
            if filepath:
                if os.name == 'nt': os.startfile(filepath)
                else: webbrowser.open(f"file://{os.path.realpath(filepath)}")
            else: messagebox.showerror("Error de Impresión", msg, parent=self)
        except Exception as e:
            messagebox.showerror("Error de Impresión", f"No se pudo generar o abrir el comprobante.\nError: {e}", parent=self)

    def generar_reporte_ventas_periodo(self, fecha_desde, fecha_hasta):
        if not fecha_desde or not fecha_hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas."); return
        for row in self.tree_ventas_periodo.get_children(): self.tree_ventas_periodo.delete(row)
        ventas = ventas_db.obtener_ventas_por_periodo(fecha_desde, fecha_hasta)
        total_periodo = sum(v[4] for v in ventas if v[5] != 'ANULADA')
        for venta in ventas: self.tree_ventas_periodo.insert("", "end", values=venta)
        self.vp_total_label.config(text=f"$ {total_periodo:.2f}")

    def anular_venta_seleccionada(self):
        selected_item = self.tree_ventas_periodo.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Por favor, seleccione una venta para anular.", parent=self); return
        venta_id = self.tree_ventas_periodo.item(selected_item, "values")[0]
        if messagebox.askyesno("Confirmar Anulación", f"¿Está seguro de anular la venta ID {venta_id}?", parent=self):
            resultado = ventas_db.anular_venta(venta_id)
            if "exitosamente" in resultado:
                messagebox.showinfo("Éxito", resultado, parent=self)
                self.generar_reporte_ventas_periodo(self.vp_fecha_desde.get(), self.vp_fecha_hasta.get())
            else: messagebox.showerror("Error", resultado, parent=self)


    # PESTAÑA: COMPRAS POR PERÍODO
    def crear_widgets_compras_periodo(self):
        frame = self.compras_periodo_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.cp_fecha_desde, self.cp_fecha_hasta = self._crear_widgets_filtro_fechas(
            frame, 
            self.generar_reporte_compras_periodo,
            lambda d, h: self._exportar_a_excel(excel_exporter.exportar_compras_periodo, "Compras_por_Periodo", d, h)
        )
        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew"); resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        columnas = ("id", "fecha", "proveedor", "factura", "total", "estado"); self.tree_compras_periodo = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_compras_periodo.heading("id", text="ID Compra"); self.tree_compras_periodo.heading("fecha", text="Fecha"); self.tree_compras_periodo.heading("proveedor", text="Proveedor"); self.tree_compras_periodo.heading("factura", text="N° Factura"); self.tree_compras_periodo.heading("total", text="Monto Total"); self.tree_compras_periodo.heading("estado", text="Estado")
        self.tree_compras_periodo.column("id", width=80, anchor="center"); self.tree_compras_periodo.column("total", anchor="e"); self.tree_compras_periodo.column("estado", width=100, anchor="center")
        self.tree_compras_periodo.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_compras_periodo.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_compras_periodo.configure(yscrollcommand=scrollbar.set)
        acciones_frame = ttk.Frame(frame, style="Content.TFrame"); acciones_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")
        btn_anular_compra = ttk.Button(acciones_frame, text="Anular Compra Seleccionada", command=self.anular_compra_seleccionada, style="Action.TButton"); btn_anular_compra.pack(side="left")

    def generar_reporte_compras_periodo(self, fecha_desde, fecha_hasta):
        if not fecha_desde or not fecha_hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas."); return
        for row in self.tree_compras_periodo.get_children(): self.tree_compras_periodo.delete(row)
        for compra in compras_db.obtener_compras_por_periodo(fecha_desde, fecha_hasta): self.tree_compras_periodo.insert("", "end", values=compra)

    def anular_compra_seleccionada(self):
        selected_item = self.tree_compras_periodo.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Por favor, seleccione una compra para anular.", parent=self); return
        compra_id = self.tree_compras_periodo.item(selected_item, "values")[0]
        if messagebox.askyesno("Confirmar Anulación", f"¿Está seguro de que desea anular la compra ID {compra_id}?", parent=self):
            resultado = compras_db.anular_compra(compra_id)
            messagebox.showinfo("Éxito", resultado, parent=self)
            self.generar_reporte_compras_periodo(self.cp_fecha_desde.get(), self.cp_fecha_hasta.get())

    # PESTAÑA: LISTADOS DE ARTÍCULOS
    def crear_widgets_listados_articulos(self):
        frame = self.listados_articulos_tab
        lf = ttk.LabelFrame(frame, text="Generación de Listados", padding=15)
        lf.pack(fill="x", padx=10, pady=10)
        
        btn_pdf_general = ttk.Button(lf, text="Generar PDF - Listado General de Artículos", command=self.generar_pdf_listado_articulos)
        btn_pdf_general.pack(pady=5, fill='x', padx=10)
        
        btn_excel_general = ttk.Button(lf, text="Exportar a Excel - Listado General de Artículos", command=lambda: self._exportar_a_excel(excel_exporter.exportar_listado_articulos, "Listado_General_Articulos"))
        btn_excel_general.pack(pady=5, fill='x', padx=10)
        
        ttk.Separator(lf, orient='horizontal').pack(fill='x', pady=15, padx=10)

        btn_pdf_repo = ttk.Button(lf, text="Generar PDF - Listado de Reposición", command=self.generar_pdf_listado_reposicion)
        btn_pdf_repo.pack(pady=5, fill='x', padx=10)
        
        btn_excel_repo = ttk.Button(lf, text="Exportar a Excel - Listado de Reposición", command=lambda: self._exportar_a_excel(excel_exporter.exportar_listado_reposicion, "Listado_Reposicion"))
        btn_excel_repo.pack(pady=5, fill='x', padx=10)

    def generar_pdf_listado_articulos(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")], title="Guardar Listado de Artículos", initialfile="Listado_Articulos.pdf")
        if not filepath: return
        success, message = report_generator.generar_listado_articulos(filepath)
        if success: messagebox.showinfo("Éxito", message, parent=self)
        else: messagebox.showerror("Error", message, parent=self)

    def generar_pdf_listado_reposicion(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")], title="Guardar Listado de Reposición", initialfile="Listado_Reposicion.pdf")
        if not filepath: return
        success, message = report_generator.generar_listado_reposicion(filepath)
        if success: messagebox.showinfo("Éxito", message, parent=self)
        else: messagebox.showerror("Error", message, parent=self)
    
    # PESTAÑA: VENTAS POR CATEGORÍAS
    def crear_widgets_ventas_categorias(self):
        frame = self.ventas_categorias_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.vc_fecha_desde, self.vc_fecha_hasta = self._crear_widgets_filtro_fechas(
            frame, 
            self.generar_reporte_ventas_categorias,
            lambda d, h: self._exportar_a_excel(excel_exporter.exportar_ventas_categorias, "Ventas_por_Categoria", d, h)
        )
        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew"); resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        self.tree_ventas_categorias = ttk.Treeview(resultados_frame, columns=("cantidad", "total"), show="tree headings")
        self.tree_ventas_categorias.heading("#0", text="Rubro / Subrubro"); self.tree_ventas_categorias.heading("cantidad", text="Cant. Vendida"); self.tree_ventas_categorias.heading("total", text="Total Vendido (Neto)")
        self.tree_ventas_categorias.column("cantidad", anchor="center", width=120); self.tree_ventas_categorias.column("total", anchor="e", width=150)
        self.tree_ventas_categorias.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_categorias.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_ventas_categorias.configure(yscrollcommand=scrollbar.set)

    def generar_reporte_ventas_categorias(self, fecha_desde, fecha_hasta):
        # ... (código sin cambios)
        if not fecha_desde or not fecha_hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas."); return
        for row in self.tree_ventas_categorias.get_children(): self.tree_ventas_categorias.delete(row)
        datos = ventas_db.reporte_ventas_por_rubro_y_subrubro(fecha_desde, fecha_hasta)
        rubros_data = defaultdict(lambda: {'cantidad': 0, 'total': 0})
        rubro_nodes = {}
        for rubro, subrubro, cantidad, total in datos:
            if rubro not in rubro_nodes:
                rubro_nodes[rubro] = self.tree_ventas_categorias.insert("", "end", text=rubro, open=True)
            rubros_data[rubro]['cantidad'] += cantidad; rubros_data[rubro]['total'] += total
            self.tree_ventas_categorias.insert(rubro_nodes[rubro], "end", text=f"  - {subrubro}", values=(f"{cantidad:.2f}", f"$ {total:.2f}"))
        for rubro, node_id in rubro_nodes.items():
            total_rubro = rubros_data[rubro]
            self.tree_ventas_categorias.item(node_id, values=(f"{total_rubro['cantidad']:.2f}", f"$ {total_rubro['total']:.2f}"))

    # PESTAÑA: VENTAS POR ARTÍCULO
    def crear_widgets_ventas_articulo(self):
        # ... (código de la pestaña, añadiendo la llamada para exportar)
        frame = self.ventas_articulo_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.va_fecha_desde, self.va_fecha_hasta = self._crear_widgets_filtro_fechas(
            frame, 
            self.generar_reporte_ventas_articulo,
            lambda d, h: self._exportar_a_excel(excel_exporter.exportar_ventas_articulo, "Ventas_por_Articulo", d, h)
        )
        # ... (resto de la interfaz de la pestaña sin cambios)
        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew"); resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        columnas = ("codigo", "nombre", "marca", "cantidad", "total"); self.tree_ventas_articulo = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_ventas_articulo.heading("codigo", text="Código"); self.tree_ventas_articulo.heading("nombre", text="Artículo"); self.tree_ventas_articulo.heading("marca", text="Marca"); self.tree_ventas_articulo.heading("cantidad", text="Cant. Vendida"); self.tree_ventas_articulo.heading("total", text="Total Vendido")
        self.tree_ventas_articulo.column("cantidad", anchor="center"); self.tree_ventas_articulo.column("total", anchor="e")
        self.tree_ventas_articulo.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_articulo.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_ventas_articulo.configure(yscrollcommand=scrollbar.set)


    def generar_reporte_ventas_articulo(self, fecha_desde, fecha_hasta):
        # ... (código sin cambios)
        if not fecha_desde or not fecha_hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas."); return
        for row in self.tree_ventas_articulo.get_children(): self.tree_ventas_articulo.delete(row)
        articulos = ventas_db.reporte_ventas_por_articulo(fecha_desde, fecha_hasta)
        for art in articulos:
            valores = (art[0], art[1], art[2], f"{art[3]:.2f}", f"$ {art[4]:.2f}")
            self.tree_ventas_articulo.insert("", "end", values=valores)

    # PESTAÑA: VENTAS POR MARCA
    def crear_widgets_ventas_marca(self):
        # ... (código de la pestaña, añadiendo la llamada para exportar)
        frame = self.ventas_marca_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.vm_fecha_desde, self.vm_fecha_hasta = self._crear_widgets_filtro_fechas(
            frame, 
            self.generar_reporte_ventas_marca,
            lambda d, h: self._exportar_a_excel(excel_exporter.exportar_ventas_marca, "Ventas_por_Marca", d, h)
        )
        # ... (resto de la interfaz de la pestaña sin cambios)
        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew"); resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        columnas = ("marca", "cantidad", "total"); self.tree_ventas_marca = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_ventas_marca.heading("marca", text="Marca"); self.tree_ventas_marca.heading("cantidad", text="Cant. Vendida"); self.tree_ventas_marca.heading("total", text="Total Vendido")
        self.tree_ventas_marca.column("cantidad", anchor="center"); self.tree_ventas_marca.column("total", anchor="e")
        self.tree_ventas_marca.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_marca.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_ventas_marca.configure(yscrollcommand=scrollbar.set)

    def generar_reporte_ventas_marca(self, fecha_desde, fecha_hasta):
        # ... (código sin cambios)
        if not fecha_desde or not fecha_hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas."); return
        for row in self.tree_ventas_marca.get_children(): self.tree_ventas_marca.delete(row)
        marcas = ventas_db.reporte_ventas_por_marca(fecha_desde, fecha_hasta)
        for marca in marcas:
            valores = (marca[0], f"{marca[1]:.2f}", f"$ {marca[2]:.2f}")
            self.tree_ventas_marca.insert("", "end", values=valores)

    # PESTAÑA: CUENTA CORRIENTE CLIENTES
    def crear_widgets_cc_clientes(self):
        frame = self.cc_clientes_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        filtros_frame = ttk.LabelFrame(frame, text="Filtros", style="TLabelframe"); filtros_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(filtros_frame, text="Cliente:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ccc_cliente_combo = ttk.Combobox(filtros_frame, state="readonly", width=30); self.ccc_cliente_combo.grid(row=0, column=1, padx=5, pady=5)
        self.clientes_data = clientes_db.obtener_todos_los_clientes_para_reporte(); self.ccc_cliente_combo['values'] = [c[1] for c in self.clientes_data]
        ttk.Label(filtros_frame, text="Desde:").grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")
        self.ccc_fecha_desde = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12); self.ccc_fecha_desde.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(filtros_frame, text="Hasta:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.ccc_fecha_hasta = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12); self.ccc_fecha_hasta.grid(row=0, column=5, padx=5, pady=5)
        btn_generar = ttk.Button(filtros_frame, text="Generar", command=self.generar_reporte_cc_cliente, style="Action.TButton"); btn_generar.grid(row=0, column=6, padx=10, pady=5)
        btn_exportar = ttk.Button(filtros_frame, text="Exportar a Excel", command=self.exportar_cc_cliente_a_excel, style="Action.TButton"); btn_exportar.grid(row=0, column=7, padx=10, pady=5)
        
        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew"); resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        columnas = ("fecha", "tipo", "monto", "saldo"); self.tree_cc_clientes = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_cc_clientes.heading("fecha", text="Fecha"); self.tree_cc_clientes.heading("tipo", text="Tipo Movimiento"); self.tree_cc_clientes.heading("monto", text="Monto"); self.tree_cc_clientes.heading("saldo", text="Saldo Resultante")
        self.tree_cc_clientes.column("monto", anchor="e"); self.tree_cc_clientes.column("saldo", anchor="e")
        self.tree_cc_clientes.grid(row=0, column=0, sticky="nsew")

    def generar_reporte_cc_cliente(self):
        # ... (código sin cambios)
        cliente_nombre = self.ccc_cliente_combo.get()
        if not cliente_nombre: messagebox.showwarning("Dato Faltante", "Por favor, seleccione un cliente."); return
        cliente_id = next(cid for cid, nombre in self.clientes_data if nombre == cliente_nombre)
        fecha_desde = self.ccc_fecha_desde.get(); fecha_hasta = self.ccc_fecha_hasta.get()
        for row in self.tree_cc_clientes.get_children(): self.tree_cc_clientes.delete(row)
        movimientos = clientes_db.obtener_cuenta_corriente_cliente(cliente_id, fecha_desde, fecha_hasta)
        for mov in movimientos:
            self.tree_cc_clientes.insert("", "end", values=(mov[0], mov[1], f"$ {mov[2]:.2f}", f"$ {mov[3]:.2f}"))

    def exportar_cc_cliente_a_excel(self):
        cliente_nombre = self.ccc_cliente_combo.get()
        if not cliente_nombre: messagebox.showwarning("Dato Faltante", "Por favor, seleccione un cliente."); return
        cliente_id = next(cid for cid, nombre in self.clientes_data if nombre == cliente_nombre)
        self._exportar_a_excel(excel_exporter.exportar_cc_cliente, f"CC_{cliente_nombre.replace(' ', '_')}", cliente_id, self.ccc_fecha_desde.get(), self.ccc_fecha_hasta.get())

    # PESTAÑA: CUENTA CORRIENTE PROVEEDORES
    def crear_widgets_cc_proveedores(self):
        # ... (código de la pestaña, añadiendo el botón de exportar)
        frame = self.cc_proveedores_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        filtros_frame = ttk.LabelFrame(frame, text="Filtros", style="TLabelframe"); filtros_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(filtros_frame, text="Proveedor:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ccp_proveedor_combo = ttk.Combobox(filtros_frame, state="readonly", width=30); self.ccp_proveedor_combo.grid(row=0, column=1, padx=5, pady=5)
        self.proveedores_data = proveedores_db.obtener_todos_los_proveedores_para_reporte(); self.ccp_proveedor_combo['values'] = [p[1] for p in self.proveedores_data]
        ttk.Label(filtros_frame, text="Desde:").grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")
        self.ccp_fecha_desde = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12); self.ccp_fecha_desde.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(filtros_frame, text="Hasta:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.ccp_fecha_hasta = DateEntry(filtros_frame, date_pattern='yyyy-mm-dd', width=12); self.ccp_fecha_hasta.grid(row=0, column=5, padx=5, pady=5)
        btn_generar = ttk.Button(filtros_frame, text="Generar", command=self.generar_reporte_cc_proveedor, style="Action.TButton"); btn_generar.grid(row=0, column=6, padx=10, pady=5)
        btn_exportar = ttk.Button(filtros_frame, text="Exportar a Excel", command=self.exportar_cc_proveedor_a_excel, style="Action.TButton"); btn_exportar.grid(row=0, column=7, padx=10, pady=5)

        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew"); resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        columnas = ("fecha", "tipo", "monto", "saldo"); self.tree_cc_proveedores = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_cc_proveedores.heading("fecha", text="Fecha"); self.tree_cc_proveedores.heading("tipo", text="Tipo Movimiento"); self.tree_cc_proveedores.heading("monto", text="Monto"); self.tree_cc_proveedores.heading("saldo", text="Saldo Resultante")
        self.tree_cc_proveedores.column("monto", anchor="e"); self.tree_cc_proveedores.column("saldo", anchor="e")
        self.tree_cc_proveedores.grid(row=0, column=0, sticky="nsew")

    def generar_reporte_cc_proveedor(self):
        # ... (código sin cambios)
        proveedor_nombre = self.ccp_proveedor_combo.get()
        if not proveedor_nombre: messagebox.showwarning("Dato Faltante", "Por favor, seleccione un proveedor."); return
        proveedor_id = next(pid for pid, nombre in self.proveedores_data if nombre == proveedor_nombre)
        fecha_desde = self.ccp_fecha_desde.get(); fecha_hasta = self.ccp_fecha_hasta.get()
        for row in self.tree_cc_proveedores.get_children(): self.tree_cc_proveedores.delete(row)
        movimientos = proveedores_db.obtener_cuenta_corriente_proveedor(proveedor_id, fecha_desde, fecha_hasta)
        for mov in movimientos:
            self.tree_cc_proveedores.insert("", "end", values=(mov[0], mov[1], f"$ {mov[2]:.2f}", f"$ {mov[3]:.2f}"))

    def exportar_cc_proveedor_a_excel(self):
        proveedor_nombre = self.ccp_proveedor_combo.get()
        if not proveedor_nombre: messagebox.showwarning("Dato Faltante", "Por favor, seleccione un proveedor."); return
        proveedor_id = next(pid for pid, nombre in self.proveedores_data if nombre == proveedor_nombre)
        self._exportar_a_excel(excel_exporter.exportar_cc_proveedor, f"CC_{proveedor_nombre.replace(' ', '_')}", proveedor_id, self.ccp_fecha_desde.get(), self.ccp_fecha_hasta.get())