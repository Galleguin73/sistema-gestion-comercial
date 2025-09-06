import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
from app.database import ventas_db, clientes_db, proveedores_db, compras_db, articulos_db
from datetime import datetime
from tkcalendar import DateEntry
from collections import defaultdict
from app.reports import report_generator, excel_exporter, ticket_generator
import os
import webbrowser
from app.utils import afip_connector
from .mixins.centering_mixin import CenteringMixin
from .clientes_abm import VentanaCliente
from .mixins.locale_validation_mixin import LocaleValidationMixin

def format_db_date(date_str):
    if not date_str: return ""
    try: return datetime.fromisoformat(date_str.split(' ')[0]).strftime('%d/%m/%Y')
    except (ValueError, TypeError): return date_str

class VentanaVerDetalleVenta(tk.Toplevel, CenteringMixin):
    def __init__(self, parent, venta_id):
        super().__init__(parent)
        self.title(f"Detalle de Venta ID: {venta_id}")
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
        
        fecha_dt = datetime.fromisoformat(encabezado['fecha_venta'].split('.')[0])
        
        ttk.Label(header_frame, text="Fecha:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header_frame, text=fecha_dt.strftime('%d/%m/%Y %H:%M')).grid(row=0, column=1, sticky="w")
        
        ttk.Label(header_frame, text="Cliente:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky="w")
        ttk.Label(header_frame, text=encabezado['cliente_nombre']).grid(row=1, column=1, columnspan=3, sticky="w")
        
        comprobante_texto = f"{encabezado['tipo_comprobante']} N°: {encabezado['numero_comprobante'] or encabezado['id']:08d}"
        ttk.Label(header_frame, text="Comprobante:", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky="w", padx=(10,0))
        ttk.Label(header_frame, text=comprobante_texto).grid(row=0, column=3, sticky="w")
        
        ttk.Label(header_frame, text="Estado:", font=("Helvetica", 10, "bold")).grid(row=2, column=0, sticky="w")
        ttk.Label(header_frame, text=encabezado['estado']).grid(row=2, column=1, sticky="w")

        if encabezado.get('cae'):
            ttk.Label(header_frame, text="CAE:", font=("Helvetica", 10, "bold")).grid(row=2, column=2, sticky="w", padx=(10,0))
            ttk.Label(header_frame, text=encabezado['cae']).grid(row=2, column=3, sticky="w")

        total_formateado = LocaleValidationMixin._format_local_number(encabezado['monto_total'])
        ttk.Label(header_frame, text=f"Total: $ {total_formateado}", font=("Helvetica", 12, "bold")).grid(row=3, column=0, columnspan=4, sticky="w", pady=10)

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
            descripcion_completa = f"{item[4]} - {item[0]}" if item[4] else item[0]
            cant_formateada = LocaleValidationMixin._format_local_number(item[1])
            p_unit_formateado = f"$ {LocaleValidationMixin._format_local_number(item[2])}"
            subtotal_formateado = f"$ {LocaleValidationMixin._format_local_number(item[3])}"
            valores = (cant_formateada, descripcion_completa, p_unit_formateado, subtotal_formateado)
            tree.insert("", "end", values=valores)
            
        ttk.Button(self, text="Cerrar", command=self.destroy, style="Action.TButton").pack(pady=10)
        self.center_window()

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

    def _get_fechas_db(self, fecha_desde_entry, fecha_hasta_entry):
        desde = fecha_desde_entry.get_date().strftime('%Y-%m-%d') if fecha_desde_entry.get_date() else None
        hasta = fecha_hasta_entry.get_date().strftime('%Y-%m-%d') if fecha_hasta_entry.get_date() else None
        return desde, hasta

    def _autoajustar_columnas(self, tree):
        for col in tree["displaycolumns"]:
            font_actual = font.Font()
            header_width = font_actual.measure(tree.heading(col)["text"])
            max_width = header_width
            for item in tree.get_children():
                try:
                    col_index = tree["columns"].index(col)
                    cell_value = str(tree.item(item, "values")[col_index])
                    cell_width = font_actual.measure(cell_value)
                    if cell_width > max_width:
                        max_width = cell_width
                except (IndexError, tk.TclError):
                    pass
            tree.column(col, width=max_width + 20, stretch=False)

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
        fecha_desde = DateEntry(filtros_frame, date_pattern='dd/mm/yyyy', width=12)
        fecha_desde.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(filtros_frame, text="Hasta:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        fecha_hasta = DateEntry(filtros_frame, date_pattern='dd/mm/yyyy', width=12)
        fecha_hasta.grid(row=0, column=3, padx=5, pady=5)
        btn_generar = ttk.Button(filtros_frame, text="Generar Vista", command=cmd_generar, style="Action.TButton")
        btn_generar.grid(row=0, column=4, padx=10, pady=5)
        btn_exportar = ttk.Button(filtros_frame, text="Exportar a Excel", command=cmd_exportar, style="Action.TButton")
        btn_exportar.grid(row=0, column=5, padx=10, pady=5)
        return fecha_desde, fecha_hasta
    
    def crear_widgets_ventas_periodo(self):
        frame = self.ventas_periodo_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.vp_fecha_desde, self.vp_fecha_hasta = self._crear_widgets_filtro_fechas(frame, self.generar_reporte_ventas_periodo, self.exportar_ventas_periodo)
        
        resultados_frame = ttk.Frame(frame, style="Content.TFrame")
        resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        
        columnas = ("id", "fecha", "cliente", "comprobante", "total", "estado", "cae")
        self.tree_ventas_periodo = ttk.Treeview(resultados_frame, columns=columnas, show="headings",
                                                displaycolumns=("fecha", "cliente", "comprobante", "total", "estado", "cae"))
        
        self.tree_ventas_periodo.heading("fecha", text="Fecha y Hora")
        self.tree_ventas_periodo.heading("cliente", text="Cliente")
        self.tree_ventas_periodo.heading("comprobante", text="Comprobante")
        self.tree_ventas_periodo.heading("total", text="Monto Total")
        self.tree_ventas_periodo.heading("estado", text="Estado")
        self.tree_ventas_periodo.heading("cae", text="CAE")
        self.tree_ventas_periodo.column("cae", width=140, anchor="center")
        
        self.tree_ventas_periodo.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_periodo.yview)
        scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_ventas_periodo.configure(yscrollcommand=scrollbar.set)
        self.tree_ventas_periodo.bind("<<TreeviewSelect>>", self._actualizar_botones_reporte)

        acciones_frame = ttk.Frame(frame, style="Content.TFrame")
        acciones_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")
        
        btn_ver_detalle = ttk.Button(acciones_frame, text="Ver Detalle", command=self._ver_detalle_venta, style="Action.TButton")
        btn_ver_detalle.pack(side="left", padx=(0, 5))
        self.btn_generar_factura = ttk.Button(acciones_frame, text="Generar Factura AFIP", command=self._generar_factura_afip, style="Action.TButton", state="disabled")
        self.btn_generar_factura.pack(side="left", padx=5)
        btn_imprimir = ttk.Button(acciones_frame, text="Imprimir Comprobante", command=self._imprimir_comprobante, style="Action.TButton")
        btn_imprimir.pack(side="left", padx=5)
        btn_anular_venta = ttk.Button(acciones_frame, text="Anular Venta", command=self.anular_venta_seleccionada, style="Action.TButton")
        btn_anular_venta.pack(side="left", padx=5)

        total_frame = ttk.Frame(frame, style="Content.TFrame"); total_frame.grid(row=3, column=0, padx=10, pady=10, sticky="e")
        ttk.Label(total_frame, text="Total Facturado:", font=("Helvetica", 12, "bold")).pack(side="left")
        self.vp_total_label = ttk.Label(total_frame, text="$ 0,00", font=("Helvetica", 12, "bold")); self.vp_total_label.pack(side="left")

    def exportar_ventas_periodo(self):
        desde, hasta = self._get_fechas_db(self.vp_fecha_desde, self.vp_fecha_hasta)
        if not desde or not hasta:
            messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas para exportar.", parent=self)
            return
        self._exportar_a_excel(excel_exporter.exportar_ventas_periodo, "Ventas_por_Periodo", desde, hasta)

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

    def generar_reporte_ventas_periodo(self):
        fecha_desde, fecha_hasta = self._get_fechas_db(self.vp_fecha_desde, self.vp_fecha_hasta)
        if not fecha_desde or not fecha_hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas."); return
        for row in self.tree_ventas_periodo.get_children(): self.tree_ventas_periodo.delete(row)
        
        ventas = ventas_db.obtener_ventas_por_periodo(fecha_desde, fecha_hasta)
        total_periodo = sum(v[4] for v in ventas if v[5] != 'ANULADA')
        
        for venta in ventas:
            fecha_str = venta[1]
            fecha_formateada = datetime.fromisoformat(fecha_str.split('.')[0]).strftime('%d/%m/%Y %H:%M') if fecha_str else ""
            
            monto_formateado = f"$ {LocaleValidationMixin._format_local_number(venta[4])}"
            
            valores_finales = (venta[0], fecha_formateada, venta[2], venta[3], monto_formateado, venta[5], venta[6] or "")
            self.tree_ventas_periodo.insert("", "end", values=valores_finales)

        self.vp_total_label.config(text=f"$ {LocaleValidationMixin._format_local_number(total_periodo)}")
        self._autoajustar_columnas(self.tree_ventas_periodo)
        self._actualizar_botones_reporte()

    def anular_venta_seleccionada(self):
        selected_item = self.tree_ventas_periodo.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Por favor, seleccione una venta para anular.", parent=self); return
        venta_id = self.tree_ventas_periodo.item(selected_item, "values")[0]
        if messagebox.askyesno("Confirmar Anulación", f"¿Está seguro de anular la venta ID {venta_id}?", parent=self):
            resultado = ventas_db.anular_venta(venta_id)
            if "exitosamente" in resultado:
                messagebox.showinfo("Éxito", resultado, parent=self)
                self.generar_reporte_ventas_periodo()
            else: messagebox.showerror("Error", resultado, parent=self)

    def _actualizar_botones_reporte(self, event=None):
        selected_item = self.tree_ventas_periodo.focus()
        if not selected_item: self.btn_generar_factura.config(state="disabled"); return
        cae = self.tree_ventas_periodo.item(selected_item, "values")[6]
        self.btn_generar_factura.config(state="normal" if not cae else "disabled")
            
    def _generar_factura_afip(self):
        selected_item = self.tree_ventas_periodo.focus()
        if not selected_item: return
        venta_id = self.tree_ventas_periodo.item(selected_item, "values")[0]
        venta_completa = ventas_db.obtener_venta_completa_por_id(venta_id)
        if not venta_completa: messagebox.showerror("Error", "No se pudieron obtener los datos completos de la venta.", parent=self); return

        if not venta_completa.get("cliente_cuit"):
            if messagebox.askyesno("Error de Facturación", f"El cliente '{venta_completa.get('cliente_nombre')}' no tiene CUIT/DNI cargado. ¿Desea abrir la ficha del cliente para agregarlo?", parent=self):
                VentanaCliente(self, cliente_id=venta_completa.get('cliente_id'))
            return

        if messagebox.askyesno("Confirmar Facturación", f"¿Desea solicitar el CAE a la AFIP para la venta N° {venta_id}?"):
            resultado_afip = afip_connector.solicitar_cae_factura({'total': venta_completa['monto_total'], 'cliente_cuit': venta_completa['cliente_cuit']})
            if resultado_afip.get("error"): messagebox.showerror("Error de AFIP", f"La AFIP rechazó la factura:\n\n{resultado_afip['error']}", parent=self); return
            if resultado_afip.get("cae"):
                datos_fiscales = {"cae": resultado_afip['cae'], "vencimiento_cae": resultado_afip['vencimiento'], "numero_factura": resultado_afip['numero_factura'], "tipo_comprobante": "Factura B"}
                resultado_db = ventas_db.actualizar_venta_con_cae(venta_id, datos_fiscales)
                messagebox.showinfo("Éxito", resultado_db, parent=self)
                self.generar_reporte_ventas_periodo()

    def crear_widgets_compras_periodo(self):
        frame = self.compras_periodo_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.cp_fecha_desde, self.cp_fecha_hasta = self._crear_widgets_filtro_fechas(frame, self.generar_reporte_compras_periodo, self.exportar_compras_periodo)
        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew"); resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        columnas = ("id", "fecha", "proveedor", "factura", "total", "estado"); self.tree_compras_periodo = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_compras_periodo.heading("id", text="ID Compra"); self.tree_compras_periodo.heading("fecha", text="Fecha"); self.tree_compras_periodo.heading("proveedor", text="Proveedor"); self.tree_compras_periodo.heading("factura", text="N° Factura"); self.tree_compras_periodo.heading("total", text="Monto Total"); self.tree_compras_periodo.heading("estado", text="Estado")
        self.tree_compras_periodo.column("id", width=80, anchor="center"); self.tree_compras_periodo.column("total", anchor="e"); self.tree_compras_periodo.column("estado", width=100, anchor="center")
        self.tree_compras_periodo.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_compras_periodo.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_compras_periodo.configure(yscrollcommand=scrollbar.set)

    def exportar_compras_periodo(self):
        desde, hasta = self._get_fechas_db(self.cp_fecha_desde, self.cp_fecha_hasta)
        if not desde or not hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas para exportar.", parent=self); return
        self._exportar_a_excel(excel_exporter.exportar_compras_periodo, "Compras_por_Periodo", desde, hasta)

    def generar_reporte_compras_periodo(self):
        fecha_desde, fecha_hasta = self._get_fechas_db(self.cp_fecha_desde, self.cp_fecha_hasta)
        if not fecha_desde or not fecha_hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas."); return
        for row in self.tree_compras_periodo.get_children(): self.tree_compras_periodo.delete(row)
        compras = compras_db.obtener_compras_por_periodo(fecha_desde, fecha_hasta)
        for compra in compras:
            valores = list(compra)
            valores[1] = format_db_date(compra[1])
            valores[4] = f"$ {LocaleValidationMixin._format_local_number(compra[4])}"
            self.tree_compras_periodo.insert("", "end", values=tuple(valores))

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
    
    def crear_widgets_ventas_categorias(self):
        frame = self.ventas_categorias_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.vc_fecha_desde, self.vc_fecha_hasta = self._crear_widgets_filtro_fechas(frame, self.generar_reporte_ventas_categorias, self.exportar_ventas_categorias)
        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew"); resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        self.tree_ventas_categorias = ttk.Treeview(resultados_frame, columns=("cantidad", "total"), show="tree headings")
        self.tree_ventas_categorias.heading("#0", text="Rubro / Subrubro"); self.tree_ventas_categorias.heading("cantidad", text="Cant. Vendida"); self.tree_ventas_categorias.heading("total", text="Total Vendido (Neto)")
        self.tree_ventas_categorias.column("cantidad", anchor="center", width=120); self.tree_ventas_categorias.column("total", anchor="e", width=150)
        self.tree_ventas_categorias.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_categorias.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_ventas_categorias.configure(yscrollcommand=scrollbar.set)

    def exportar_ventas_categorias(self):
        desde, hasta = self._get_fechas_db(self.vc_fecha_desde, self.vc_fecha_hasta)
        if not desde or not hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas para exportar.", parent=self); return
        self._exportar_a_excel(excel_exporter.exportar_ventas_categorias, "Ventas_por_Categoria", desde, hasta)

    def generar_reporte_ventas_categorias(self, fecha_desde, fecha_hasta):
        for row in self.tree_ventas_categorias.get_children(): self.tree_ventas_categorias.delete(row)
        datos = ventas_db.reporte_ventas_por_rubro_y_subrubro(fecha_desde, fecha_hasta)
        rubros_data = defaultdict(lambda: {'cantidad': 0, 'total': 0})
        rubro_nodes = {}
        for rubro, subrubro, cantidad, total in datos:
            if rubro not in rubro_nodes:
                rubro_nodes[rubro] = self.tree_ventas_categorias.insert("", "end", text=rubro, open=True)
            rubros_data[rubro]['cantidad'] += cantidad; rubros_data[rubro]['total'] += total
            cant_formateada = LocaleValidationMixin._format_local_number(cantidad)
            total_formateado = f"$ {LocaleValidationMixin._format_local_number(total)}"
            self.tree_ventas_categorias.insert(rubro_nodes[rubro], "end", text=f"  - {subrubro}", values=(cant_formateada, total_formateado))
        for rubro, node_id in rubro_nodes.items():
            total_rubro = rubros_data[rubro]
            cant_total_formateada = LocaleValidationMixin._format_local_number(total_rubro['cantidad'])
            total_total_formateado = f"$ {LocaleValidationMixin._format_local_number(total_rubro['total'])}"
            self.tree_ventas_categorias.item(node_id, values=(cant_total_formateada, total_total_formateado))

    def crear_widgets_ventas_articulo(self):
        frame = self.ventas_articulo_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.va_fecha_desde, self.va_fecha_hasta = self._crear_widgets_filtro_fechas(frame, self.generar_reporte_ventas_articulo, self.exportar_ventas_articulo)
        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew"); resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        columnas = ("codigo", "nombre", "marca", "cantidad", "total"); self.tree_ventas_articulo = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_ventas_articulo.heading("codigo", text="Código"); self.tree_ventas_articulo.heading("nombre", text="Artículo"); self.tree_ventas_articulo.heading("marca", text="Marca"); self.tree_ventas_articulo.heading("cantidad", text="Cant. Vendida"); self.tree_ventas_articulo.heading("total", text="Total Vendido")
        self.tree_ventas_articulo.column("cantidad", anchor="center"); self.tree_ventas_articulo.column("total", anchor="e")
        self.tree_ventas_articulo.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_articulo.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_ventas_articulo.configure(yscrollcommand=scrollbar.set)

    def exportar_ventas_articulo(self):
        desde, hasta = self._get_fechas_db(self.va_fecha_desde, self.va_fecha_hasta)
        if not desde or not hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas para exportar.", parent=self); return
        self._exportar_a_excel(excel_exporter.exportar_ventas_articulo, "Ventas_por_Articulo", desde, hasta)

    def generar_reporte_ventas_articulo(self):
        fecha_desde, fecha_hasta = self._get_fechas_db(self.va_fecha_desde, self.va_fecha_hasta)
        if not fecha_desde or not fecha_hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas."); return
        for row in self.tree_ventas_articulo.get_children(): self.tree_ventas_articulo.delete(row)
        articulos = ventas_db.reporte_ventas_por_articulo(fecha_desde, fecha_hasta)
        for art in articulos:
            cant_formateada = LocaleValidationMixin._format_local_number(art[3])
            total_formateado = f"$ {LocaleValidationMixin._format_local_number(art[4])}"
            valores = (art[0], art[1], art[2], cant_formateada, total_formateado)
            self.tree_ventas_articulo.insert("", "end", values=valores)

    def crear_widgets_ventas_marca(self):
        frame = self.ventas_marca_tab
        frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.vm_fecha_desde, self.vm_fecha_hasta = self._crear_widgets_filtro_fechas(frame, self.generar_reporte_ventas_marca, self.exportar_ventas_marca)
        resultados_frame = ttk.Frame(frame, style="Content.TFrame"); resultados_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew"); resultados_frame.grid_rowconfigure(0, weight=1); resultados_frame.grid_columnconfigure(0, weight=1)
        columnas = ("marca", "cantidad", "total"); self.tree_ventas_marca = ttk.Treeview(resultados_frame, columns=columnas, show="headings")
        self.tree_ventas_marca.heading("marca", text="Marca"); self.tree_ventas_marca.heading("cantidad", text="Cant. Vendida"); self.tree_ventas_marca.heading("total", text="Total Vendido")
        self.tree_ventas_marca.column("cantidad", anchor="center"); self.tree_ventas_marca.column("total", anchor="e")
        self.tree_ventas_marca.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree_ventas_marca.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree_ventas_marca.configure(yscrollcommand=scrollbar.set)

    def exportar_ventas_marca(self):
        desde, hasta = self._get_fechas_db(self.vm_fecha_desde, self.vm_fecha_hasta)
        if not desde or not hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas para exportar.", parent=self); return
        self._exportar_a_excel(excel_exporter.exportar_ventas_marca, "Ventas_por_Marca", desde, hasta)

    def generar_reporte_ventas_marca(self):
        fecha_desde, fecha_hasta = self._get_fechas_db(self.vm_fecha_desde, self.vm_fecha_hasta)
        if not fecha_desde or not fecha_hasta: messagebox.showwarning("Datos Incompletos", "Por favor, ingrese ambas fechas."); return
        for row in self.tree_ventas_marca.get_children(): self.tree_ventas_marca.delete(row)
        marcas = ventas_db.reporte_ventas_por_marca(fecha_desde, fecha_hasta)
        for marca in marcas:
            cant_formateada = LocaleValidationMixin._format_local_number(marca[1])
            total_formateado = f"$ {LocaleValidationMixin._format_local_number(marca[2])}"
            valores = (marca[0], cant_formateada, total_formateado)
            self.tree_ventas_marca.insert("", "end", values=valores)