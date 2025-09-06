import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import caja_db
import json
from .mixins.centering_mixin import CenteringMixin

class VentanaCierreCaja(tk.Toplevel, CenteringMixin):
    def __init__(self, parent, caja_id, monto_inicial, resumen_movimientos, callback_exito):
        super().__init__(parent)
        self.parent = parent
        self.caja_id = caja_id
        self.monto_inicial = monto_inicial
        self.resumen_movimientos = resumen_movimientos
        self.callback = callback_exito

        self.title("Cierre de Caja Detallado")
        
        # --- CAMBIO 3: Se elimina la geometría fija ---
        # self.geometry("600x400")

        self.transient(parent)
        self.grab_set()

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        # Ajustamos el peso de la fila para que la tabla pueda crecer si es necesario
        main_frame.grid_rowconfigure(0, weight=1) 

        # --- Tabla de Cierre ---
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columnas = ("medio_pago", "saldo_esperado", "monto_real", "diferencia")
        self.tree_cierre = ttk.Treeview(tree_frame, columns=columnas, show="headings", height=5) # Altura inicial
        self.tree_cierre.grid(row=0, column=0, sticky="nsew")
        
        self.tree_cierre.heading("medio_pago", text="Medio de Pago")
        self.tree_cierre.heading("saldo_esperado", text="Saldo Esperado")
        self.tree_cierre.heading("monto_real", text="Monto Real Contado")
        self.tree_cierre.heading("diferencia", text="Diferencia")

        self.tree_cierre.column("medio_pago", width=150)
        self.tree_cierre.column("saldo_esperado", anchor="e", width=120)
        self.tree_cierre.column("monto_real", anchor="e", width=150)
        self.tree_cierre.column("diferencia", anchor="e", width=120)

        # --- Botones ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, sticky="e", pady=(10, 0))
        
        ttk.Button(btn_frame, text="Calcular Diferencia (Efectivo)", command=self.calcular_diferencias).pack(side="left", padx=5)
        self.btn_confirmar = ttk.Button(btn_frame, text="Confirmar Cierre de Caja", command=self.confirmar_cierre, state="disabled")
        self.btn_confirmar.pack(side="left", padx=5)

        self.popular_tabla()
        
        # --- CAMBIO 4: Se llama a la función para centrar la ventana ---
        self.center_window()

    def popular_tabla(self):
        """Llena la tabla con los datos del resumen."""
        # Limpiamos la tabla antes de llenarla
        for i in self.tree_cierre.get_children():
            self.tree_cierre.delete(i)
            
        ingresos_efectivo = self.resumen_movimientos.get('Efectivo', {}).get('ingresos', 0.0)
        egresos_efectivo = self.resumen_movimientos.get('Efectivo', {}).get('egresos', 0.0)
        saldo_esperado_efectivo = self.monto_inicial + ingresos_efectivo - egresos_efectivo

        # Agregamos el efectivo primero, con un tag para identificarlo
        self.tree_cierre.insert("", "end", iid="Efectivo", values=("Efectivo", f"{saldo_esperado_efectivo:.2f}", "", ""), tags=('efectivo_row',))

        # Agregamos el resto de los medios de pago
        for medio, totales in sorted(self.resumen_movimientos.items()):
            if medio == 'Efectivo': continue
            neto = totales['ingresos'] - totales['egresos']
            self.tree_cierre.insert("", "end", iid=medio, values=(medio, f"{neto:.2f}", "N/A", "N/A"))

        self.tree_cierre.tag_configure('efectivo_row', font=('Helvetica', 9, 'bold'))
        self.tree_cierre.bind("<Double-1>", self.editar_celda_monto_real)

    def editar_celda_monto_real(self, event):
        """Permite al usuario editar el monto real SÓLO para el efectivo."""
        selected_iid = self.tree_cierre.focus()
        
        if selected_iid != "Efectivo":
            return

        region = self.tree_cierre.identify_region(event.x, event.y)
        if region != "cell": return

        column = self.tree_cierre.identify_column(event.x)
        if column != "#3": return
        
        monto_ingresado = simpledialog.askfloat("Ingresar Monto Real", 
                                                f"Ingrese el monto real para {selected_iid}:",
                                                parent=self)
        if monto_ingresado is not None:
            valores_actuales = list(self.tree_cierre.item(selected_iid, "values"))
            valores_actuales[2] = f"{monto_ingresado:.2f}"
            self.tree_cierre.item(selected_iid, values=tuple(valores_actuales))
            self.btn_confirmar.config(state="disabled")

    def calcular_diferencias(self):
        """Calcula y muestra la diferencia SÓLO para el efectivo."""
        try:
            valores = list(self.tree_cierre.item("Efectivo", "values"))
            esperado = float(valores[1])
            real_str = valores[2]

            if not real_str:
                messagebox.showwarning("Dato Faltante", "Debe ingresar el 'Monto Real' para el Efectivo antes de calcular.", parent=self)
                return

            real = float(real_str)
            diferencia = real - esperado
            valores[3] = f"{diferencia:.2f}"
            self.tree_cierre.item("Efectivo", values=tuple(valores))
            
            self.btn_confirmar.config(state="normal")
        except (ValueError, IndexError):
            messagebox.showerror("Error", "No se pudo calcular la diferencia. Verifique los montos.", parent=self)
            self.btn_confirmar.config(state="disabled")

    def confirmar_cierre(self):
        """Recopila todos los datos, los convierte a JSON y los guarda en la BD."""
        detalle_cierre_list = []
        valores_efectivo = (0, 0, 0)

        for iid in self.tree_cierre.get_children():
            valores = self.tree_cierre.item(iid, "values")
            
            try:
                real = float(valores[2]) if valores[2] != "N/A" else 0.0
                diferencia = float(valores[3]) if valores[3] != "N/A" else 0.0
            except ValueError:
                real = 0.0
                diferencia = 0.0

            detalle = {
                "medio_pago": valores[0],
                "esperado": float(valores[1]),
                "real": real,
                "diferencia": diferencia
            }
            detalle_cierre_list.append(detalle)
            
            if valores[0] == "Efectivo":
                valores_efectivo = (detalle['esperado'], detalle['real'], detalle['diferencia'])
        
        detalle_cierre_json = json.dumps(detalle_cierre_list, indent=4)
        monto_esperado_efectivo, monto_real_efectivo, diferencia_efectivo = valores_efectivo

        resultado = caja_db.cerrar_caja(
            self.caja_id, 
            monto_real_efectivo, 
            monto_esperado_efectivo, 
            diferencia_efectivo,
            detalle_cierre_json
        )
        
        if "exitosamente" in resultado:
            messagebox.showinfo("Caja Cerrada", f"La caja ha sido cerrada.\nDiferencia (Efectivo): ${diferencia_efectivo:.2f}", parent=self.parent)
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)