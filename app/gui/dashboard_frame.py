# Archivo: app/gui/dashboard_frame.py
import tkinter as tk
from tkinter import ttk
from app.database import ventas_db
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style

        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.grid_rowconfigure((1, 2), weight=1)

        self.kpi1_frame = ttk.LabelFrame(self, text="Ventas del Mes Actual")
        self.kpi1_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.kpi2_frame = ttk.LabelFrame(self, text="Ventas del Día")
        self.kpi2_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.kpi3_frame = ttk.LabelFrame(self, text="Top 10 Productos Más Vendidos (Cant.)")
        self.kpi3_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.kpi4_frame = ttk.LabelFrame(self, text="Top 10 Productos Más Rentables ($)")
        self.kpi4_frame.grid(row=1, column=2, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.kpi5_frame = ttk.LabelFrame(self, text="Ventas Últimos 6 Meses")
        self.kpi5_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.kpi6_frame = ttk.LabelFrame(self, text="Ventas Último Mes (por día)")
        self.kpi6_frame.grid(row=2, column=2, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.popular_kpis()

    def popular_kpis(self):
        # KPI 1: Ventas del Mes
        total_mes = ventas_db.obtener_ventas_mes_actual()
        self.kpi1_frame.grid_columnconfigure(0, weight=1)
        self.kpi1_frame.grid_rowconfigure(0, weight=1)
        ttk.Label(self.kpi1_frame, text=f"$ {total_mes:,.2f}", font=("Helvetica", 22, "bold"), anchor="center").grid(row=0, column=0, sticky="nsew", ipady=20)

        # KPI 2: Ventas del Día
        total_dia = ventas_db.obtener_ventas_dia_actual()
        self.kpi2_frame.grid_columnconfigure(0, weight=1)
        self.kpi2_frame.grid_rowconfigure(0, weight=1)
        ttk.Label(self.kpi2_frame, text=f"$ {total_dia:,.2f}", font=("Helvetica", 22, "bold"), anchor="center").grid(row=0, column=0, sticky="nsew", ipady=20)

        # KPI 3: Top 10 Vendidos
        self._crear_tabla_top_productos(self.kpi3_frame, ventas_db.obtener_top_10_productos_vendidos(), "Cant. Vendida")
        
        # KPI 4: Top 10 Rentables
        self._crear_tabla_top_productos(self.kpi4_frame, ventas_db.obtener_top_10_productos_rentables(), "Ganancia Total ($)")

        # KPI 5: Gráfico 6 Meses
        datos_6_meses = ventas_db.obtener_ventas_ultimos_6_meses()
        self._crear_grafico(self.kpi5_frame, datos_6_meses, "Ventas por Mes", "Mes", "Total ($)")

        # KPI 6: Gráfico 1 Mes por Día
        datos_1_mes = ventas_db.obtener_ventas_ultimo_mes_por_dia()
        self._crear_grafico(self.kpi6_frame, datos_1_mes, "Ventas por Día", "Día", "Total ($)")
        
    def _crear_tabla_top_productos(self, parent_frame, datos, nombre_columna_valor):
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)
        tree = ttk.Treeview(parent_frame, columns=("producto", "valor"), show="headings")
        tree.heading("producto", text="Producto")
        tree.heading("valor", text=nombre_columna_valor)
        tree.column("valor", anchor="e", width=120)
        tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        for prod in datos:
            tree.insert("", "end", values=(prod[0], f"{prod[1]:,.2f}"))

    # --- FUNCIÓN MODIFICADA ---
    def _crear_grafico(self, parent_frame, datos, titulo, xlabel, ylabel):
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)
        
        fig = plt.Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)
        
        if datos:
            etiquetas = [item[0] for item in datos]
            valores = [item[1] for item in datos]
            
            ax.bar(etiquetas, valores, color='#2c3e50')
            ax.set_title(titulo, fontsize=10)
            ax.set_ylabel(ylabel, fontsize=8)
            ax.set_xlabel(xlabel, fontsize=8)
            plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7)

            # --- INICIO DE LA CORRECCIÓN ---
            # Línea de tendencia (solo si hay más de un punto de datos)
            if len(etiquetas) > 1:
                x = np.arange(len(etiquetas))
                try:
                    z = np.polyfit(x, valores, 1)
                    p = np.poly1d(z)
                    ax.plot(x, p(x), "r--", linewidth=1)
                except Exception as e:
                    print(f"No se pudo calcular la línea de tendencia: {e}")
            # --- FIN DE LA CORRECCIÓN ---

        else:
            ax.text(0.5, 0.5, 'Sin datos para el período', ha='center', va='center')

        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)