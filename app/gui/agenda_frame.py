# Ubicación: app/gui/agenda_frame.py (Actualizado)

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import obligaciones_db, config_db
from tkcalendar import DateEntry
from datetime import datetime, date
from .mixins.locale_validation_mixin import LocaleValidationMixin
from .mixins.centering_mixin import CenteringMixin

# La clase VentanaObligacion y VentanaRegistrarPago no cambian
class VentanaObligacion(tk.Toplevel, CenteringMixin, LocaleValidationMixin):
    def __init__(self, parent, on_success_callback):
        super().__init__(parent)
        self.withdraw()
        self.parent = parent
        self.on_success_callback = on_success_callback
        self.title("Registrar Nuevo Gasto/Obligación")
        self.geometry("450x380")
        self.transient(parent); self.grab_set()
        frame = ttk.Frame(self, padding="15")
        frame.pack(expand=True, fill="both")
        frame.columnconfigure(1, weight=1)
        self.tipos_data = obligaciones_db.obtener_tipos_de_obligacion()
        tipos_display = [f"{t[1]} ({t[2]})" for t in self.tipos_data]
        self.entries = {}
        ttk.Label(frame, text="Concepto:").grid(row=0, column=0, sticky="w", padx=5, pady=8)
        self.tipo_combo = ttk.Combobox(frame, values=tipos_display, state="readonly")
        self.tipo_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=8)
        ttk.Label(frame, text="Vencimiento:").grid(row=1, column=0, sticky="w", padx=5, pady=8)
        self.entries['fecha_vencimiento'] = DateEntry(frame, date_pattern='dd/mm/yyyy', width=12)
        self.entries['fecha_vencimiento'].grid(row=1, column=1, sticky="w", padx=5, pady=8)
        ttk.Label(frame, text="Período:").grid(row=2, column=0, sticky="w", padx=5, pady=8)
        self.entries['periodo'] = ttk.Entry(frame)
        self.entries['periodo'].grid(row=2, column=1, sticky="ew", padx=5, pady=8)
        self.entries['periodo'].insert(0, datetime.now().strftime('%B %Y'))
        ttk.Label(frame, text="Monto:").grid(row=3, column=0, sticky="w", padx=5, pady=8)
        self.entries['monto_original'] = ttk.Entry(frame)
        self.entries['monto_original'].grid(row=3, column=1, sticky="ew", padx=5, pady=8)
        self._setup_numeric_validation(self.entries['monto_original'])
        ttk.Label(frame, text="Observaciones:").grid(row=4, column=0, sticky="w", padx=5, pady=8)
        self.entries['observaciones'] = ttk.Entry(frame)
        self.entries['observaciones'].grid(row=4, column=1, sticky="ew", padx=5, pady=8)
        btn_guardar = ttk.Button(frame, text="Guardar Obligación", command=self.guardar, style="Action.TButton")
        btn_guardar.grid(row=5, column=0, columnspan=2, pady=15, sticky="ew")
        self.center_window()
        self.deiconify()
    def guardar(self):
        datos = {clave: widget.get() for clave, widget in self.entries.items()}
        tipo_seleccionado = self.tipo_combo.get()
        if not tipo_seleccionado:
            messagebox.showwarning("Dato Faltante", "Debe seleccionar un concepto.", parent=self)
            return
        tipo_id = next((t[0] for t in self.tipos_data if f"{t[1]} ({t[2]})" == tipo_seleccionado), None)
        datos['tipo_obligacion_id'] = tipo_id
        try:
            datos['monto_original'] = self.get_validated_float(self.entries['monto_original'], "Monto")
            datos['fecha_vencimiento'] = self.entries['fecha_vencimiento'].get_date().strftime('%Y-%m-%d')
        except ValueError: return
        resultado = obligaciones_db.registrar_obligacion(datos)
        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            self.on_success_callback()
            self.destroy()
        else: messagebox.showerror("Error", resultado, parent=self)

class VentanaRegistrarPago(tk.Toplevel, LocaleValidationMixin, CenteringMixin):
    def __init__(self, parent, on_success_callback, obligacion_data, caja_id):
        super().__init__(parent)
        self.withdraw()
        self.parent = parent
        self.on_success_callback = on_success_callback
        self.obligacion_id, self.concepto, self.monto_a_pagar = obligacion_data
        self.caja_id = caja_id
        self.pagos = []
        self.title(f"Registrar Pago: {self.concepto}")
        self.transient(parent); self.grab_set()
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill="both")
        ttk.Label(main_frame, text=f"Total a Pagar: $ {self._format_local_number(self.monto_a_pagar)}", font=("Helvetica", 12, "bold")).pack(pady=10)
        pago_frame = ttk.Frame(main_frame)
        pago_frame.pack(fill="x", pady=5)
        pago_frame.columnconfigure(1, weight=1)
        ttk.Label(pago_frame, text="Monto:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.monto_entry = ttk.Entry(pago_frame)
        self.monto_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.monto_entry.insert(0, self._format_local_number(self.monto_a_pagar))
        ttk.Label(pago_frame, text="Medio de Pago:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.medio_pago_combo = ttk.Combobox(pago_frame, state="readonly")
        self.medio_pago_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.medios_pago_data = config_db.obtener_medios_de_pago()
        self.medio_pago_combo['values'] = [m[1] for m in self.medios_pago_data]
        if self.medio_pago_combo['values']: self.medio_pago_combo.current(0)
        ttk.Button(self, text="Confirmar Pago", command=self.confirmar_pago, style="Action.TButton").pack(pady=20, fill="x")
        self.center_window()
        self.deiconify()
    def confirmar_pago(self):
        try:
            monto = self.get_validated_float(self.monto_entry, "Monto")
            if monto <= 0: raise ValueError("El monto debe ser positivo.")
            medio_pago_nombre = self.medio_pago_combo.get()
            if not medio_pago_nombre:
                messagebox.showwarning("Dato Faltante", "Debe seleccionar un medio de pago.", parent=self); return
            medio_pago_id = next((mid for mid, nombre in self.medios_pago_data if nombre == medio_pago_nombre), None)
            self.pagos.append({'medio_pago_id': medio_pago_id, 'monto': monto})
            resultado = obligaciones_db.registrar_pago_obligacion(self.obligacion_id, self.caja_id, date.today(), self.pagos)
            if "exitosamente" in resultado:
                messagebox.showinfo("Éxito", resultado, parent=self)
                self.on_success_callback(); self.destroy()
            else: messagebox.showerror("Error", resultado, parent=self)
        except ValueError: return

class AgendaFrame(ttk.Frame, LocaleValidationMixin):
    def __init__(self, parent, style, main_window):
        super().__init__(parent, style="Content.TFrame")
        self.main_window = main_window

        filtros_frame = ttk.LabelFrame(self, text="Filtros y Acciones", padding=10)
        filtros_frame.pack(padx=10, pady=10, fill="x")
        # ... (código de filtros sin cambios) ...
        ttk.Label(filtros_frame, text="Desde:").pack(side="left", padx=5)
        self.fecha_desde = DateEntry(filtros_frame, date_pattern='dd/mm/yyyy', width=12)
        self.fecha_desde.pack(side="left", padx=5)
        ttk.Label(filtros_frame, text="Hasta:").pack(side="left", padx=5)
        self.fecha_hasta = DateEntry(filtros_frame, date_pattern='dd/mm/yyyy', width=12)
        self.fecha_hasta.pack(side="left", padx=5)
        ttk.Label(filtros_frame, text="Estado:").pack(side="left", padx=5)
        self.estado_combo = ttk.Combobox(filtros_frame, values=["Todas", "PENDIENTE", "PAGADA"], state="readonly")
        self.estado_combo.pack(side="left", padx=5)
        self.estado_combo.set("PENDIENTE")
        ttk.Button(filtros_frame, text="Filtrar", command=self.actualizar_lista).pack(side="left", padx=10)
        acciones_frame = ttk.Frame(filtros_frame)
        acciones_frame.pack(side="right")
        ttk.Button(acciones_frame, text="Registrar Gasto", command=self._registrar_gasto, style="Action.TButton").pack(side="left", padx=2)
        ttk.Button(acciones_frame, text="Registrar Pago", command=self._registrar_pago, style="Action.TButton").pack(side="left", padx=2)
        ttk.Button(acciones_frame, text="Eliminar", command=self._eliminar_obligacion, style="Action.TButton").pack(side="left", padx=2)

        tree_container = ttk.Frame(self)
        tree_container.pack(padx=10, pady=5, fill="both", expand=True)
        tree_container.rowconfigure(0, weight=1); tree_container.columnconfigure(0, weight=1)

        columnas = ("id", "vencimiento", "periodo", "concepto", "categoria", "monto", "estado")
        self.tree = ttk.Treeview(tree_container, columns=columnas, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")
        # ... (código de configuración del treeview sin cambios) ...
        self.tree.heading("vencimiento", text="Vencimiento"); self.tree.heading("periodo", text="Período")
        self.tree.heading("concepto", text="Concepto"); self.tree.heading("categoria", text="Categoría")
        self.tree.heading("monto", text="Monto"); self.tree.heading("estado", text="Estado")
        self.tree.column("id", width=0, stretch=tk.NO)
        self.tree.column("vencimiento", width=100, anchor="center")
        self.tree.column("monto", width=120, anchor="e")
        self.tree.column("estado", width=100, anchor="center")
        self.tree.tag_configure('PENDIENTE', foreground='red'); self.tree.tag_configure('PAGADA', foreground='green'); self.tree.tag_configure('ANULADA', foreground='gray')
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns"); self.tree.configure(yscrollcommand=scrollbar.set)
        
        # --- NUEVO PANEL DE TOTALES ---
        totals_frame = ttk.LabelFrame(self, text="Resumen del Período Filtrado", padding=10)
        totals_frame.pack(padx=10, pady=10, fill="x")
        totals_frame.columnconfigure((1, 3, 5), weight=1)

        ttk.Label(totals_frame, text="Total Pendiente:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        self.total_pendiente_label = ttk.Label(totals_frame, text="$ 0,00", foreground="red", font=("Helvetica", 10))
        self.total_pendiente_label.grid(row=0, column=1, sticky="w")
        
        ttk.Label(totals_frame, text="Total Pagado:", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky="w", padx=5)
        self.total_pagado_label = ttk.Label(totals_frame, text="$ 0,00", foreground="green", font=("Helvetica", 10))
        self.total_pagado_label.grid(row=0, column=3, sticky="w")

        ttk.Label(totals_frame, text="Registros:", font=("Helvetica", 10, "bold")).grid(row=0, column=4, sticky="w", padx=5)
        self.cantidad_label = ttk.Label(totals_frame, text="0", font=("Helvetica", 10))
        self.cantidad_label.grid(row=0, column=5, sticky="w")
        
        self.actualizar_lista()

    def actualizar_lista(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        
        filtros = {
            "fecha_desde": self.fecha_desde.get_date().strftime('%Y-%m-%d'),
            "fecha_hasta": self.fecha_hasta.get_date().strftime('%Y-%m-%d'),
            "estado": self.estado_combo.get()
        }
        
        obligaciones = obligaciones_db.obtener_obligaciones(filtros)
        
        # --- NUEVA LÓGICA DE CÁLCULO DE TOTALES ---
        total_pendiente = 0.0
        total_pagado = 0.0
        
        for ob in obligaciones:
            (ob_id, venc, periodo, concepto, cat, monto, estado) = ob
            venc_f = datetime.strptime(venc, '%Y-%m-%d').strftime('%d/%m/%Y')
            monto_f = f"$ {self._format_local_number(monto)}"
            
            self.tree.insert("", "end", iid=ob_id, values=(ob_id, venc_f, periodo, concepto, cat, monto_f, estado), tags=(estado,))

            if estado == 'PENDIENTE':
                total_pendiente += monto
            elif estado == 'PAGADA':
                total_pagado += monto
        
        # Actualizamos las etiquetas de totales
        self.total_pendiente_label.config(text=f"$ {self._format_local_number(total_pendiente)}")
        self.total_pagado_label.config(text=f"$ {self._format_local_number(total_pagado)}")
        self.cantidad_label.config(text=str(len(obligaciones)))

    def _registrar_gasto(self):
        VentanaObligacion(self, on_success_callback=self.actualizar_lista)

    def _registrar_pago(self):
        if not self.main_window.caja_actual_id:
            messagebox.showerror("Caja Cerrada", "Debe abrir la caja para registrar un pago.")
            return
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una obligación de la lista.")
            return
        obligacion = obligaciones_db.obtener_obligacion_por_id(int(selected_item))
        if not obligacion or obligacion[6] != 'PENDIENTE':
            messagebox.showwarning("Estado Inválido", "Solo se pueden pagar obligaciones en estado 'PENDIENTE'.")
            return
        obligacion_data = (obligacion[0], obligacion[3], obligacion[5])
        VentanaRegistrarPago(self, self.actualizar_lista, obligacion_data, self.main_window.caja_actual_id)
        
    def _eliminar_obligacion(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una obligación para eliminar.")
            return
        if messagebox.askyesno("Confirmar Eliminación", "Esta acción borrará el registro permanentemente. ¿Está seguro?", parent=self):
            resultado = obligaciones_db.eliminar_obligacion(int(selected_item))
            if "exitosamente" in resultado:
                messagebox.showinfo("Éxito", resultado)
                self.actualizar_lista()
            else: messagebox.showerror("Error", resultado)