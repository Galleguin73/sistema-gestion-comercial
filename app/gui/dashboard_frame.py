import tkinter as tk
from tkinter import ttk
from app.database import ventas_db, articulos_db, obligaciones_db # Se añade obligaciones_db
from datetime import datetime
from .mixins.locale_validation_mixin import LocaleValidationMixin

# --- FUNCIÓN AUXILIAR PARA FORMATEAR FECHAS ---
def format_db_date(date_str):
    if not date_str:
        return ""
    try:
        return datetime.fromisoformat(date_str.split(' ')[0]).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return date_str

class DashboardFrame(ttk.Frame, LocaleValidationMixin):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style

        # --- Definimos los estilos que usaremos ---
        self.style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        self.style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")
        
        # --- Estructura de la Grilla Original ---
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.grid_rowconfigure(2, weight=1) 

        # --- Sección: Ventas del Mes Actual ---
        kpi1_container = ttk.Frame(self, style="ContentPane.TFrame")
        kpi1_container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        kpi1_container.rowconfigure(1, weight=1); kpi1_container.columnconfigure(0, weight=1)
        ttk.Label(kpi1_container, text="Ventas del Mes Actual", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        self.kpi1_frame = ttk.Frame(kpi1_container)
        self.kpi1_frame.grid(row=1, column=0, sticky="nsew")

        # --- Sección: Ventas del Día ---
        kpi2_container = ttk.Frame(self, style="ContentPane.TFrame")
        kpi2_container.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        kpi2_container.rowconfigure(1, weight=1); kpi2_container.columnconfigure(0, weight=1)
        ttk.Label(kpi2_container, text="Ventas del Día", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        self.kpi2_frame = ttk.Frame(kpi2_container)
        self.kpi2_frame.grid(row=1, column=0, sticky="nsew")
        
        # --- Sección: Alertas de Stock Bajo ---
        kpi_stock_container = ttk.Frame(self, style="ContentPane.TFrame")
        kpi_stock_container.grid(row=0, column=2, columnspan=2, rowspan=2, padx=10, pady=10, sticky="nsew")
        kpi_stock_container.rowconfigure(1, weight=1); kpi_stock_container.columnconfigure(0, weight=1)
        ttk.Label(kpi_stock_container, text="🔥 Alertas de Stock Bajo", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        self.kpi_stock_frame = ttk.Frame(kpi_stock_container)
        self.kpi_stock_frame.grid(row=1, column=0, sticky="nsew")

        # --- Sección: Top 10 Productos Más Vendidos ---
        kpi3_container = ttk.Frame(self, style="ContentPane.TFrame")
        kpi3_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        kpi3_container.rowconfigure(1, weight=1); kpi3_container.columnconfigure(0, weight=1)
        ttk.Label(kpi3_container, text="Top 10 Productos Más Vendidos (Cant.)", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        self.kpi3_frame = ttk.Frame(kpi3_container)
        self.kpi3_frame.grid(row=1, column=0, sticky="nsew")

        # --- Sección: Top 10 Productos Más Rentables ---
        kpi4_container = ttk.Frame(self, style="ContentPane.TFrame")
        kpi4_container.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        kpi4_container.rowconfigure(1, weight=1); kpi4_container.columnconfigure(0, weight=1)
        ttk.Label(kpi4_container, text="Top 10 Productos Más Rentables ($)", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        self.kpi4_frame = ttk.Frame(kpi4_container)
        self.kpi4_frame.grid(row=1, column=0, sticky="nsew")

        # --- Sección: Alertas de Vencimiento de ARTÍCULOS (Restaurada) ---
        kpi_vencimiento_container = ttk.Frame(self, style="ContentPane.TFrame")
        kpi_vencimiento_container.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        kpi_vencimiento_container.rowconfigure(1, weight=1); kpi_vencimiento_container.columnconfigure(0, weight=1)
        ttk.Label(kpi_vencimiento_container, text="📅 Alertas de Vencimiento (Próx. 10 días)", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        self.kpi_vencimiento_frame = ttk.Frame(kpi_vencimiento_container)
        self.kpi_vencimiento_frame.grid(row=1, column=0, sticky="nsew")

        # --- NUEVA SECCIÓN: Agenda de Obligaciones (Reemplaza al gráfico) ---
        kpi6_container = ttk.Frame(self, style="ContentPane.TFrame")
        kpi6_container.grid(row=2, column=2, columnspan=2, padx=10, pady=10, sticky="nsew")
        kpi6_container.rowconfigure(1, weight=1); kpi6_container.columnconfigure(0, weight=1)
        ttk.Label(kpi6_container, text="📅 Agenda: Próximos Vencimientos (7 días)", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        self.kpi6_frame = ttk.Frame(kpi6_container)
        self.kpi6_frame.grid(row=1, column=0, sticky="nsew")

        self.popular_kpis()

    def popular_kpis(self):
        # --- Lógica para popular todos los paneles ---

        # Ventas del Mes y Día
        total_mes = ventas_db.obtener_ventas_mes_actual()
        self.kpi1_frame.grid_columnconfigure(0, weight=1); self.kpi1_frame.grid_rowconfigure(0, weight=1)
        ttk.Label(self.kpi1_frame, text=f"$ {self._format_local_number(total_mes)}", font=("Helvetica", 22, "bold"), anchor="center").grid(row=0, column=0, sticky="nsew", ipady=10)
        total_dia = ventas_db.obtener_ventas_dia_actual()
        self.kpi2_frame.grid_columnconfigure(0, weight=1); self.kpi2_frame.grid_rowconfigure(0, weight=1)
        ttk.Label(self.kpi2_frame, text=f"$ {self._format_local_number(total_dia)}", font=("Helvetica", 22, "bold"), anchor="center").grid(row=0, column=0, sticky="nsew", ipady=10)
        
        # Alertas de Stock Bajo
        self.kpi_stock_frame.grid_rowconfigure(0, weight=1); self.kpi_stock_frame.grid_columnconfigure(0, weight=1)
        self.style.configure("Red.Treeview", background="#f8d7da", fieldbackground="#f8d7da", foreground="#721c24")
        self.style.map('Red.Treeview', background=[('selected', '#f5c6cb')])
        tree_stock = ttk.Treeview(self.kpi_stock_frame, columns=("producto", "actual", "minimo"), show="headings", style="Red.Treeview")
        tree_stock.heading("producto", text="Producto a Reponer"); tree_stock.heading("actual", text="Stock Actual"); tree_stock.heading("minimo", text="Stock Mínimo")
        tree_stock.column("actual", anchor="center", width=80); tree_stock.column("minimo", anchor="center", width=80)
        tree_stock.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        stock_bajo = articulos_db.obtener_articulos_stock_bajo()
        if not stock_bajo:
            tree_stock.insert("", "end", values=("¡Todo en orden!", "-", "-")); tree_stock.configure(style="Treeview")
        else:
            for item in stock_bajo: tree_stock.insert("", "end", values=item)

        # Top Productos
        self._crear_tabla_top_productos(self.kpi3_frame, ventas_db.obtener_top_10_productos_vendidos(), "Cant. Vendida")
        self._crear_tabla_top_productos(self.kpi4_frame, ventas_db.obtener_top_10_productos_rentables(), "Ganancia Total ($)")
        
        # Alertas de Vencimiento de Artículos
        self.kpi_vencimiento_frame.grid_rowconfigure(0, weight=1); self.kpi_vencimiento_frame.grid_columnconfigure(0, weight=1)
        self.style.configure("Yellow.Treeview", background="#fff3cd", fieldbackground="#fff3cd", foreground="#856404")
        self.style.map('Yellow.Treeview', background=[('selected', '#ffeeba')])
        tree_vencimiento = ttk.Treeview(self.kpi_vencimiento_frame, columns=("producto", "fecha_venc", "stock"), show="headings", style="Yellow.Treeview")
        tree_vencimiento.heading("producto", text="Producto a Vencer"); tree_vencimiento.heading("fecha_venc", text="Fecha Venc."); tree_vencimiento.heading("stock", text="Stock Lote")
        tree_vencimiento.column("fecha_venc", anchor="center", width=100); tree_vencimiento.column("stock", anchor="center", width=80)
        tree_vencimiento.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        vencimientos = articulos_db.obtener_articulos_proximos_a_vencer(10)
        if not vencimientos:
            tree_vencimiento.insert("", "end", values=("No hay vencimientos próximos", "-", "-")); tree_vencimiento.configure(style="Treeview")
        else:
            for item in vencimientos:
                nombre, lote, fecha_str, stock = item
                nombre_completo = f"{nombre} (Lote: {lote})"
                fecha_display = format_db_date(fecha_str)
                tree_vencimiento.insert("", "end", values=(nombre_completo, fecha_display, stock))

        # Agenda de Obligaciones
        self.kpi6_frame.grid_rowconfigure(0, weight=1); self.kpi6_frame.grid_columnconfigure(0, weight=1)
        columnas = ("vence", "concepto", "monto")
        tree_agenda = ttk.Treeview(self.kpi6_frame, columns=columnas, show="headings", style="Yellow.Treeview")
        tree_agenda.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        tree_agenda.heading("vence", text="Vence"); tree_agenda.heading("concepto", text="Concepto"); tree_agenda.heading("monto", text="Monto")
        tree_agenda.column("vence", anchor="center", width=90); tree_agenda.column("monto", anchor="e", width=110)
        tree_agenda.tag_configure('VENCE_HOY', foreground='orange', font=("Helvetica", 9, "bold"))
        tree_agenda.tag_configure('VENCIDO', foreground='red', font=("Helvetica", 9, "bold"))
        proximos_vencimientos = obligaciones_db.obtener_obligaciones_proximas(dias=7)
        hoy = datetime.now().date()
        if not proximos_vencimientos:
            tree_agenda.insert("", "end", values=("No hay vencimientos", "próximos", ""))
            tree_agenda.configure(style="Treeview")
        else:
            for vencimiento, concepto, monto in proximos_vencimientos:
                fecha_venc = datetime.strptime(vencimiento, '%Y-%m-%d').date()
                tag = 'VENCE_HOY' if fecha_venc == hoy else ('VENCIDO' if fecha_venc < hoy else '')
                venc_f = fecha_venc.strftime('%d/%m/%Y')
                monto_f = f"$ {self._format_local_number(monto)}"
                tree_agenda.insert("", "end", values=(venc_f, concepto, monto_f), tags=(tag,))
        
    def _crear_tabla_top_productos(self, parent_frame, datos, nombre_columna_valor):
        parent_frame.grid_rowconfigure(0, weight=1); parent_frame.grid_columnconfigure(0, weight=1)
        tree = ttk.Treeview(parent_frame, columns=("producto", "valor"), show="headings")
        tree.heading("producto", text="Producto"); tree.heading("valor", text=nombre_columna_valor)
        tree.column("valor", anchor="e", width=120)
        tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        for prod in datos:
            valor_formateado = self._format_local_number(prod[1])
            if "$" in nombre_columna_valor:
                valor_formateado = f"$ {valor_formateado}"
            tree.insert("", "end", values=(prod[0], valor_formateado))