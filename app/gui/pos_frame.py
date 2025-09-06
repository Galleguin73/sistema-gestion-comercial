# Ubicación: app/gui/pos_frame.py (MODIFICADO)

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import articulos_db, clientes_db, config_db, ventas_db
from .clientes_abm import VentanaCliente
from datetime import datetime
import os
from PIL import Image, ImageTk
from app.utils import afip_connector
import webbrowser
from .mixins.centering_mixin import CenteringMixin

# La VentanaDescuento no necesita cambios, la mantenemos como está.
class VentanaDescuento(simpledialog.Dialog):
    def __init__(self, parent, title=None): super().__init__(parent, title=title)
    def body(self, master):
        self.result = None; master.grid_columnconfigure(1, weight=1)
        ttk.Label(master, text="Valor:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.valor_entry = ttk.Entry(master); self.valor_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(master, text="Tipo:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.tipo_var = tk.StringVar(value="$")
        ttk.Radiobutton(master, text="Monto Fijo ($)", variable=self.tipo_var, value="$").grid(row=1, column=1, sticky="w", padx=5)
        ttk.Radiobutton(master, text="Porcentaje (%)", variable=self.tipo_var, value="%").grid(row=2, column=1, sticky="w", padx=5)
        return self.valor_entry
    def apply(self):
        try:
            valor = float(self.valor_entry.get())
            if valor < 0: messagebox.showwarning("Inválido", "El valor no puede ser negativo.", parent=self); return
            self.result = (valor, self.tipo_var.get())
        except (ValueError, TypeError): messagebox.showwarning("Inválido", "Por favor ingrese un valor numérico.", parent=self)


class VentanaPago(tk.Toplevel, CenteringMixin):
    """
    Una ventana modal para gestionar el cobro de una venta con múltiples medios de pago.
    """
    def __init__(self, parent, total_a_pagar, callback_finalizar):
        super().__init__(parent)
        self.parent = parent
        self.total_a_pagar = total_a_pagar
        self.callback_finalizar = callback_finalizar

        # --- Variables para almacenar el resultado ---
        self.confirmado = False
        self.pagos = [] # El resultado final será una lista de diccionarios

        # Obtenemos los medios de pago de la DB para mapear nombres a IDs
        self.medios_de_pago_data = config_db.obtener_medios_de_pago()
        self.medios_de_pago_nombres = [m[1] for m in self.medios_de_pago_data]

        # --- Configuración de la ventana ---
        self.title("Información de Pago")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_cancelar)
        self.transient(parent)
        self.grab_set()

        # --- Creación de los widgets de la interfaz ---
        self._crear_widgets()
        self._actualizar_totales()
        self.center_window()


    def _crear_widgets(self):
        """Crea y posiciona todos los elementos gráficos de la ventana."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill="both")

        # --- Columna Izquierda: Medios de Pago ---
        pagos_frame = ttk.Frame(main_frame)
        pagos_frame.grid(row=0, column=0, sticky="ns", padx=(0, 20))

        self.entries = {}
        for i, medio_nombre in enumerate(self.medios_de_pago_nombres):
            label = ttk.Label(pagos_frame, text=f"{medio_nombre}:", font=("Helvetica", 12))
            label.grid(row=i, column=0, sticky="w", pady=10)
            entry = ttk.Entry(pagos_frame, font=("Helvetica", 12), width=15)
            entry.grid(row=i, column=1, sticky="ew", padx=10)
            entry.bind("<KeyRelease>", self._actualizar_totales)
            self.entries[medio_nombre] = entry

        # --- Columna Derecha: Totales ---
        totales_frame = ttk.Frame(main_frame)
        totales_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)

        style = ttk.Style(self)
        style.configure('Dark.TFrame', background='#000')

        # Contenedor con fondo oscuro
        dark_container = ttk.Frame(totales_frame, style='Dark.TFrame')
        dark_container.pack(fill="both", expand=True)

        ttk.Label(dark_container, text="Total a pagar", font=("Helvetica", 14, "bold"), foreground="#4CAF50", background="#000").pack(pady=(10,0), padx=10)
        self.label_total_a_pagar = ttk.Label(dark_container, text=f"$ {self.total_a_pagar:,.2f}", font=("Helvetica", 22, "bold"), foreground="#FFFFFF", background="#000")
        self.label_total_a_pagar.pack(pady=(0,20), padx=10)

        ttk.Label(dark_container, text="Total pagado", font=("Helvetica", 14, "bold"), foreground="#4CAF50", background="#000").pack(pady=10, padx=10)
        self.label_total_pagado = ttk.Label(dark_container, text="$ 0,00", font=("Helvetica", 22, "bold"), foreground="#FFFFFF", background="#000")
        self.label_total_pagado.pack(pady=(0,20), padx=10)

        ttk.Label(dark_container, text="Saldo", font=("Helvetica", 14, "bold"), foreground="#4CAF50", background="#000").pack(pady=10, padx=10)
        self.label_saldo = ttk.Label(dark_container, text=f"$ -{self.total_a_pagar:,.2f}", font=("Helvetica", 22, "bold"), foreground="#FF5733", background="#000")
        self.label_saldo.pack(padx=10)

        # --- Botones de Acción ---
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=1, column=0, columnspan=2, pady=(20, 0))

        self.btn_confirmar = ttk.Button(botones_frame, text="Confirmar", command=self._on_confirmar, state="disabled", style="Action.TButton")
        self.btn_confirmar.pack(side="left", padx=10)

        self.btn_cancelar = ttk.Button(botones_frame, text="Cancelar", command=self._on_cancelar)
        self.btn_cancelar.pack(side="left", padx=10)

    def _actualizar_totales(self, event=None):
        total_pagado = 0.0
        for medio, entry in self.entries.items():
            try:
                monto_str = entry.get().replace(',', '.')
                if monto_str:
                    total_pagado += float(monto_str)
            except (ValueError, TypeError):
                pass
        
        saldo = self.total_a_pagar - total_pagado

        self.label_total_pagado.config(text=f"$ {total_pagado:,.2f}")
        self.label_saldo.config(text=f"$ {saldo:,.2f}")

        if saldo < 0:
            self.label_saldo.config(foreground="#FF5733") # Rojo
        else:
            self.label_saldo.config(foreground="#FFFFFF")

        if abs(saldo) < 0.001:
            self.btn_confirmar.config(state="normal")
        else:
            self.btn_confirmar.config(state="disabled")

    def _on_confirmar(self):
        pagos_temp = []
        for medio_nombre, entry in self.entries.items():
            try:
                monto = float(entry.get().replace(',', '.'))
                if monto > 0:
                    # Buscamos el ID correspondiente al nombre del medio de pago
                    medio_id = next((mid for mid, nombre in self.medios_de_pago_data if nombre == medio_nombre), None)
                    if medio_id:
                        pagos_temp.append({'medio_pago_id': medio_id, 'monto': monto})
            except (ValueError, TypeError):
                pass
        
        self.pagos = pagos_temp
        self.confirmado = True
        self.callback_finalizar(self.pagos) # Llamamos al callback con los datos
        self.destroy()

    def _on_cancelar(self):
        self.confirmado = False
        self.destroy()

class VentanaSeleccionArticulo(tk.Toplevel, CenteringMixin):
    def __init__(self, parent, callback_agregar):
        super().__init__(parent)
        self.callback_agregar = callback_agregar
        self.articulo_seleccionado = None
        self.sugerencias_actuales = []
        self._after_id = None

        self.title("Buscar y Agregar Artículo")
        self.transient(parent); self.grab_set(); self.geometry("800x600")

        self._crear_estilos()
        self._crear_widgets()
        
        self.center_window()
        self._actualizar_resultados()
        self.search_entry.focus_set()

    def _crear_estilos(self):
        self.style = ttk.Style(self)
        self.style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        self.style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")

    def _crear_widgets(self):
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)

        # --- Sección 1: Búsqueda ---
        search_container = ttk.Frame(self, style="ContentPane.TFrame")
        search_container.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        ttk.Label(search_container, text="BÚSQUEDA", style="SectionTitle.TLabel").pack(fill="x")
        
        search_content = ttk.Frame(search_container, padding=10)
        search_content.pack(fill="x")
        self.search_entry = ttk.Entry(search_content, font=("Helvetica", 14))
        self.search_entry.pack(fill="x", ipady=4)
        self.search_entry.bind("<KeyRelease>", self._on_key_release)
        self.search_entry.bind("<Return>", self._seleccionar_y_agregar)

        # --- Sección 2: Resultados y Vista Previa ---
        results_container = ttk.Frame(self, style="ContentPane.TFrame")
        results_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        results_container.rowconfigure(1, weight=1); results_container.columnconfigure(0, weight=1)
        ttk.Label(results_container, text="RESULTADOS Y VISTA PREVIA", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")

        paned_window = ttk.PanedWindow(results_container, orient=tk.HORIZONTAL)
        paned_window.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        tree_frame = ttk.Frame(paned_window, padding=5); paned_window.add(tree_frame, weight=1)
        tree_frame.rowconfigure(0, weight=1); tree_frame.columnconfigure(0, weight=1)
        
        self.tree_resultados = ttk.Treeview(tree_frame, columns=("id", "nombre"), show="headings")
        self.tree_resultados.heading("nombre", text="Descripción del Artículo")
        self.tree_resultados.column("id", width=0, stretch=tk.NO)
        self.tree_resultados.grid(row=0, column=0, sticky="nsew")
        self.tree_resultados.bind("<<TreeviewSelect>>", self._on_item_selected)
        self.tree_resultados.bind("<Double-1>", self._seleccionar_y_agregar)

        # --- Panel Derecho: Vista Previa y Acciones (MODIFICADO) ---
        preview_frame = ttk.Frame(paned_window, padding=10); paned_window.add(preview_frame, weight=1)
        # Usamos grid para un control preciso
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1) # Fila de la imagen se expande
        
        self.image_label = ttk.Label(preview_frame, text="Escriba para buscar un artículo...", anchor="center")
        self.image_label.grid(row=0, column=0, sticky="nsew", pady=5); self.photo_image = None
        
        self.nombre_label = ttk.Label(preview_frame, text="", font=("Helvetica", 12, "bold"), anchor="center", wraplength=300)
        self.nombre_label.grid(row=1, column=0, sticky="ew", pady=5)
        
        self.precio_label = ttk.Label(preview_frame, text="", font=("Helvetica", 20, "bold"), anchor="center")
        self.precio_label.grid(row=2, column=0, sticky="ew", pady=5)
        
        action_frame = ttk.Frame(preview_frame)
        action_frame.grid(row=3, column=0, pady=10) # Fila para la cantidad
        
        ttk.Label(action_frame, text="Cantidad:", font=("Helvetica", 11)).pack(side="left", padx=(0, 5))
        self.cantidad_entry = ttk.Entry(action_frame, width=8, font=("Helvetica", 14), justify='center')
        self.cantidad_entry.pack(side="left")
        self.cantidad_entry.insert(0, "1")
        self.cantidad_entry.bind("<Return>", self._seleccionar_y_agregar)
        # --- Fin de la sección modificada ---

        self.btn_agregar = ttk.Button(self, text="Agregar al Carrito", command=self._seleccionar_y_agregar, style="Action.TButton", state="disabled")
        self.btn_agregar.grid(row=2, column=0, sticky="ew", padx=10, pady=(5,10), ipady=8)

    def _on_key_release(self, event):
        if event.keysym == "Return": return
        if self._after_id: self.after_cancel(self._after_id)
        self._after_id = self.after(250, self._actualizar_resultados)

    def _actualizar_resultados(self):
        criterio = self.search_entry.get()
        for i in self.tree_resultados.get_children():
            self.tree_resultados.delete(i)
        
        if not criterio:
            self.sugerencias_actuales = []
            self._limpiar_preview()
            self.image_label.config(text="Escriba para buscar un artículo...")
            return

        self.sugerencias_actuales = articulos_db.buscar_articulos_pos(criterio)
        if not self.sugerencias_actuales:
             self.image_label.config(text="No se encontraron artículos...")

        for art in self.sugerencias_actuales:
            self.tree_resultados.insert("", "end", values=(art[0], art[1]), iid=art[0])

    def _on_item_selected(self, event=None):
        selected_item = self.tree_resultados.focus()
        if not selected_item: self._limpiar_preview(); return
        item_id = self.tree_resultados.item(selected_item, "values")[0]
        self.articulo_seleccionado = next((art for art in self.sugerencias_actuales if str(art[0]) == str(item_id)), None)
        if self.articulo_seleccionado:
            try:
                precio = float(self.articulo_seleccionado[2] or 0.0)
            except (ValueError, TypeError):
                precio = 0.0
            nombre = self.articulo_seleccionado[1]
            imagen_path = self.articulo_seleccionado[4]
            self.nombre_label.config(text=nombre)
            self.precio_label.config(text=f"$ {precio:,.2f}")
            self._mostrar_imagen(imagen_path)
            self.btn_agregar.config(state="normal")
            self.cantidad_entry.focus_set()
            self.cantidad_entry.select_range(0, 'end')
        else: self._limpiar_preview()

    def _limpiar_preview(self):
        self.articulo_seleccionado = None
        self.precio_label.config(text="")
        self.nombre_label.config(text="")
        self._mostrar_imagen(None)
        self.btn_agregar.config(state="disabled")

    def _mostrar_imagen(self, filepath):
        if filepath and os.path.exists(filepath):
            try:
                img = Image.open(filepath); img.thumbnail((250, 250)); self.photo_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.photo_image, text="")
            except Exception:
                self.image_label.config(image='', text="Error al cargar imagen"); self.photo_image = None
        else:
            self.image_label.config(image='', text="Sin imagen"); self.photo_image = None

    def _seleccionar_y_agregar(self, event=None):
        if not self.articulo_seleccionado:
            first_item = self.tree_resultados.get_children()
            if first_item:
                self.tree_resultados.focus(first_item[0]); self.tree_resultados.selection_set(first_item[0]); self._on_item_selected()
            else:
                messagebox.showwarning("Sin Resultados", "No hay artículos para agregar.", parent=self); return
        if not self.articulo_seleccionado:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un artículo de la lista.", parent=self); return
        try:
            cantidad = float(self.cantidad_entry.get())
            if cantidad <= 0: raise ValueError()
        except ValueError:
            messagebox.showerror("Cantidad Inválida", "Por favor, ingrese una cantidad numérica positiva.", parent=self); return
        self.callback_agregar(self.articulo_seleccionado, cantidad); self.destroy()



class POSFrame(ttk.Frame):
    def __init__(self, parent, style, main_window, caja_id):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.main_window = main_window
        self.caja_actual_id = caja_id
        
        self.style.configure("Highlight.TButton", font=("Helvetica", 12, "bold"), background="#2ecc71", foreground="white", padding=(10, 15))
        self.style.map("Highlight.TButton", background=[('active', '#27ae60')])

        # NUEVO: Estilo para una Label normal que usaremos como título de sección
        self.style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        
        # NUEVO: Estilo para el borde de los frames de contenido
        self.style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")
        
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=3); self.grid_columnconfigure(1, weight=1)

        # --- Columna Central (Carrito y sus acciones) ---
        middle_column = ttk.Frame(self, style="Content.TFrame")
        middle_column.grid(row=0, column=0, rowspan=2, padx=(10,5), pady=10, sticky="nsew")
        middle_column.grid_rowconfigure(1, weight=1) 
        middle_column.grid_columnconfigure(0, weight=1)

        # --- Sección Datos de Venta ---
        # MODIFICADO: Se usa un Frame contenedor general
        top_frame_container = ttk.Frame(middle_column, style="ContentPane.TFrame")
        top_frame_container.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        top_frame_container.columnconfigure(0, weight=1)
        
        # 1. Título que se expande
        ttk.Label(top_frame_container, text="Datos de Venta", style="SectionTitle.TLabel").pack(fill="x")
        
        # 2. Contenido dentro de su propio Frame
        top_frame = ttk.Frame(top_frame_container, padding=5)
        top_frame.pack(fill="x")
        top_frame.columnconfigure(1, weight=1) 
        top_frame.columnconfigure(3, weight=1)
        
        ttk.Label(top_frame, text="Cliente:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cliente_combo = ttk.Combobox(top_frame)
        self.cliente_combo.grid(row=0, column=1, padx=(0,5), pady=5, sticky="ew")
        self.cliente_combo.bind("<KeyRelease>", self._filtrar_clientes_combobox)
        self.cliente_combo.bind("<<ComboboxSelected>>", self._on_cliente_seleccionado)
        self.add_cliente_btn = ttk.Button(top_frame, text="+", width=3, command=self.crear_nuevo_cliente)
        self.add_cliente_btn.grid(row=0, column=2, pady=5, padx=(0,10))
        ttk.Label(top_frame, text="Fecha:").grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.fecha_label = ttk.Label(top_frame, font=("Helvetica", 10, "bold"))
        self.fecha_label.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.fecha_label.config(text=datetime.now().strftime("%d/%m/%Y"))

        ttk.Label(top_frame, text="Comprobante:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.comprobante_combo = ttk.Combobox(top_frame, state="readonly")
        self.comprobante_combo.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Label(top_frame, text="N° Comp:").grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.nro_comprobante_label = ttk.Label(top_frame, font=("Helvetica", 10, "bold"), text="A asignar")
        self.nro_comprobante_label.grid(row=1, column=4, padx=5, pady=5, sticky="w")

        # --- Sección Carrito de Compras ---
        cart_frame_container = ttk.Frame(middle_column, style="ContentPane.TFrame")
        cart_frame_container.grid(row=1, column=0, sticky="nsew")
        cart_frame_container.rowconfigure(1, weight=1); cart_frame_container.columnconfigure(0, weight=1)

        ttk.Label(cart_frame_container, text="Carrito de Compras", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        
        cart_frame_content = ttk.Frame(cart_frame_container)
        cart_frame_content.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        cart_frame_content.rowconfigure(0, weight=1); cart_frame_content.columnconfigure(0, weight=1)
        
        columnas = ("cant", "desc", "p_unit", "descuento", "subtotal")
        self.tree = ttk.Treeview(cart_frame_content, columns=columnas, show="headings", height=10)
        self.tree.configure(style="Small.Treeview")
        self.tree.heading("cant", text="Cant."); self.tree.heading("desc", text="Descripción"); self.tree.heading("p_unit", text="P. Unit."); self.tree.heading("descuento", text="Desc."); self.tree.heading("subtotal", text="Subtotal")
        self.tree.column("cant", width=70, anchor="center"); self.tree.column("p_unit", width=110, anchor="e"); self.tree.column("descuento", width=90, anchor="e"); self.tree.column("subtotal", width=110, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew"); scrollbar = ttk.Scrollbar(cart_frame_content, orient="vertical", command=self.tree.yview); scrollbar.grid(row=0, column=1, sticky="ns"); self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._mostrar_imagen_seleccionada)

        middle_actions_frame = ttk.Frame(middle_column)
        middle_actions_frame.grid(row=2, column=0, sticky="ew", pady=(10,0))
        middle_actions_frame.columnconfigure(0, weight=1) 
        middle_actions_frame.columnconfigure(1, weight=1)
        middle_actions_frame.rowconfigure(0, weight=1)
        middle_actions_frame.rowconfigure(1, weight=1)

        btn_buscar_articulo = ttk.Button(middle_actions_frame, text="AGREGAR ARTÍCULO", style="Highlight.TButton", command=self.abrir_ventana_seleccion)
        btn_buscar_articulo.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0,5))
        
        ttk.Button(middle_actions_frame, text="Descuento a Ítem", command=self.aplicar_descuento_item).grid(row=0, column=1, sticky="nsew", padx=(5,0), pady=(0, 2))
        ttk.Button(middle_actions_frame, text="Quitar Artículo", command=self.quitar_item_seleccionado).grid(row=1, column=1, sticky="nsew", padx=(5,0), pady=(2, 0))

        # --- Columna Derecha (Resumen y Pago) ---
        right_column = ttk.Frame(self, style="Content.TFrame")
        right_column.grid(row=0, column=1, rowspan=2, padx=(5,10), pady=10, sticky="nsew")
        right_column.grid_rowconfigure(0, weight=1)
        right_column.grid_columnconfigure(0, weight=1)
        
        # --- Sección Imagen del Producto ---
        image_frame_container = ttk.Frame(right_column, style="ContentPane.TFrame")
        image_frame_container.grid(row=0, column=0, sticky="nsew")
        image_frame_container.rowconfigure(1, weight=1); image_frame_container.columnconfigure(0, weight=1)

        ttk.Label(image_frame_container, text="Imagen del Producto", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        
        image_frame_content = ttk.Frame(image_frame_container)
        image_frame_content.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.image_label = ttk.Label(image_frame_content, text="Seleccione un ítem del carrito", anchor="center")
        self.image_label.pack(fill="both", expand=True)
        self.photo_image = None
        
        # --- Sección Resumen y Pago ---
        resumen_frame_container = ttk.Frame(right_column, style="ContentPane.TFrame")
        resumen_frame_container.grid(row=1, column=0, sticky="ew", pady=(10,0))
        resumen_frame_container.columnconfigure(0, weight=1)

        ttk.Label(resumen_frame_container, text="Resumen y Pago", style="SectionTitle.TLabel").pack(fill="x")
        
        total_frame = ttk.Frame(resumen_frame_container, padding=10)
        total_frame.pack(fill="x")
        total_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(total_frame, text="Subtotal:").grid(row=0, column=0, sticky="w"); self.subtotal_label = ttk.Label(total_frame, text="$ 0.00"); self.subtotal_label.grid(row=0, column=1, sticky="e")
        ttk.Label(total_frame, text="Descuentos:").grid(row=1, column=0, sticky="w"); self.descuento_label = ttk.Label(total_frame, text="$ 0.00", foreground="red"); self.descuento_label.grid(row=1, column=1, sticky="e")
        ttk.Label(total_frame, text="TOTAL:", font=("Helvetica", 18, "bold")).grid(row=2, column=0, sticky="w", pady=(5,0)); self.total_label = ttk.Label(total_frame, text="$ 0.00", font=("Helvetica", 18, "bold")); self.total_label.grid(row=2, column=1, sticky="e", pady=(5,0))
        btn_descuento_total = ttk.Button(total_frame, text="Descuento al Total", command=self.aplicar_descuento_total); btn_descuento_total.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10,0))
        ttk.Button(total_frame, text="Finalizar Venta", style="Action.TButton", command=self.abrir_ventana_pago).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(5,0))
        ttk.Button(total_frame, text="Cancelar", style="Action.TButton", command=self.limpiar_venta).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(5,0))
        
        self.limpiar_venta()

    def _cargar_clientes_combobox(self):
        self.lista_completa_clientes = clientes_db.buscar_clientes_pos('')
        clientes_display = [f"{c[1]} ({c[2]})" for c in self.lista_completa_clientes]
        self.cliente_combo['values'] = clientes_display

    def _filtrar_clientes_combobox(self, event=None):
        criterio = self.cliente_combo.get().lower()
        
        if not criterio:
            clientes_display = [f"{c[1]} ({c[2]})" for c in self.lista_completa_clientes]
        else:
            clientes_filtrados = [c for c in self.lista_completa_clientes if criterio in c[1].lower() or criterio in c[2].lower()]
            clientes_display = [f"{c[1]} ({c[2]})" for c in clientes_filtrados]

        self.cliente_combo['values'] = clientes_display
        self.cliente_combo.event_generate('<Down>')

    def _on_cliente_seleccionado(self, event=None):
        seleccion = self.cliente_combo.get()
        cliente_encontrado = None
        for cliente in self.lista_completa_clientes:
            display_str = f"{cliente[1]} ({cliente[2]})"
            if display_str == seleccion:
                cliente_encontrado = cliente
                break
        
        if cliente_encontrado:
            self.seleccionar_cliente(cliente_encontrado)

    def seleccionar_cliente(self, cliente_info):
        self.cliente_actual = cliente_info
        self.cliente_combo.set(self.cliente_actual[1])
        self.actualizar_tipos_comprobante()
        self.cliente_combo.event_generate('<Escape>')

    def _mostrar_imagen_seleccionada(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            self.image_label.config(image='', text="Seleccione un ítem del carrito")
            self.photo_image = None
            return

        item_id = int(selected_item)
        item_data = self.carrito_items.get(item_id)
        
        if item_data and item_data.get('imagen_path') and os.path.exists(item_data['imagen_path']):
            try:
                img = Image.open(item_data['imagen_path'])
                img.thumbnail((250, 250))
                self.photo_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.photo_image, text="")
            except Exception as e:
                self.image_label.config(image='', text="Error al cargar\nla imagen"); self.photo_image = None; print(f"Error mostrando imagen: {e}")
        else:
            self.image_label.config(image='', text="Sin imagen"); self.photo_image = None

    def abrir_ventana_seleccion(self): 
        VentanaSeleccionArticulo(self, callback_agregar=self.agregar_item_al_carrito)

    def agregar_item_al_carrito(self, item_info, cantidad):
        item_id_str, descripcion, precio, unidad, imagen_path = item_info
        item_id = int(item_id_str)
        if item_id in self.carrito_items: self.carrito_items[item_id]['cantidad'] += cantidad
        else: self.carrito_items[item_id] = {'descripcion': descripcion, 'cantidad': cantidad, 'precio_unit': precio, 'unidad': unidad, 'descuento': 0.0, 'imagen_path': imagen_path}
        self.refrescar_venta()
    
    def refrescar_venta(self):
        selected_id = self.tree.focus()
        for row in self.tree.get_children(): self.tree.delete(row)
        subtotal_general = 0.0; descuento_items = 0.0
        for item_id, data in self.carrito_items.items():
            subtotal_bruto = data['cantidad'] * data['precio_unit']; descuento = data.get('descuento', 0.0); subtotal_item_neto = subtotal_bruto - descuento
            subtotal_general += subtotal_bruto; descuento_items += descuento
            vista_cantidad = f"{data['cantidad']:.2f}"
            self.tree.insert("", "end", iid=item_id, values=(vista_cantidad, data['descripcion'], f"${data['precio_unit']:.2f}", f"-$ {descuento:.2f}" if descuento > 0 else "$ 0.00", f"${subtotal_item_neto:.2f}"))
        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id); self.tree.focus(selected_id)
        descuento_total = descuento_items + getattr(self, 'descuento_global', 0.0); total_final = subtotal_general - descuento_total
        self.subtotal_label.config(text=f"$ {subtotal_general:.2f}"); self.descuento_label.config(text=f"-$ {descuento_total:.2f}"); self.total_label.config(text=f"$ {total_final:.2f}")

    def quitar_item_seleccionado(self):
        selected_item = self.tree.focus()
        if not selected_item: messagebox.showwarning("Sin Selección", "Seleccione un ítem del carrito para quitar."); return
        item_id = int(selected_item)
        if item_id in self.carrito_items:
            del self.carrito_items[item_id]
            self.refrescar_venta(); self._mostrar_imagen_seleccionada()
    
    def actualizar_tipos_comprobante(self):
        config_empresa = config_db.obtener_configuracion()
        cond_iva_empresa = config_empresa.get('condicion_iva', 'Monotributo')
        comprobantes_disponibles = []
        if cond_iva_empresa == 'Monotributo':
            comprobantes_disponibles = ["Ticket Factura C", "Factura C", "Remito"]
        elif cond_iva_empresa == 'Responsable Inscripto':
            comprobantes_disponibles = ["Ticket Factura A", "Factura A", "Ticket Factura B", "Factura B", "Remito"]
        self.comprobante_combo['values'] = comprobantes_disponibles
        if comprobantes_disponibles: self.comprobante_combo.set(comprobantes_disponibles[0])
            
    def crear_nuevo_cliente(self): 
        VentanaCliente(self, on_success_callback=self.cliente_creado_exitosamente)

    def cliente_creado_exitosamente(self, cliente_datos):
        self._cargar_clientes_combobox()
        cliente_info = (cliente_datos.get('id'), cliente_datos.get('razon_social'), cliente_datos.get('cuit_dni'))
        if cliente_info[0]:
            self.seleccionar_cliente(cliente_info)

    def limpiar_venta(self):
        self.carrito_items = {}; self.cliente_actual = None; self.descuento_global = 0.0
        self._cargar_clientes_combobox()
        self.cliente_combo.set("Consumidor Final")
        self.actualizar_tipos_comprobante()
        self.refrescar_venta()
        self._mostrar_imagen_seleccionada()

    def abrir_ventana_pago(self):
        if not self.caja_actual_id: messagebox.showerror("Caja Cerrada", "Debe abrir la caja."); return
        if not self.carrito_items: messagebox.showwarning("Carrito Vacío", "No hay artículos en el carrito."); return
        total = float(self.total_label.cget("text").replace("$", "")); 
        
        # --- AQUÍ ESTÁ EL ÚNICO CAMBIO NECESARIO ---
        # La llamada a VentanaPago sigue siendo la misma, ya que reemplazamos la clase.
        # El callback 'self.finalizar_venta' ahora recibirá los datos de la nueva ventana.
        dialogo = VentanaPago(self, total, self.finalizar_venta)
        self.wait_window(dialogo)

    def finalizar_venta(self, pagos):
        # La nueva ventana ya nos pasa la lista de pagos en el formato correcto.
        # No necesitamos hacer nada más aquí.
        total_final = float(self.total_label.cget("text").replace("$", ""))
        cliente_id_a_guardar = self.cliente_actual[0] if self.cliente_actual else None
        
        if not self.cliente_actual or self.cliente_combo.get() == "Consumidor Final":
            consumidor_final = next((c[0] for c in self.lista_completa_clientes if c[1].lower() == 'consumidor final'), None)
            cliente_id_a_guardar = consumidor_final
        
        datos_venta = {
            'cliente_id': cliente_id_a_guardar, 
            'cliente_nombre': self.cliente_combo.get(), 
            'total': total_final, 
            'tipo_comprobante': self.comprobante_combo.get(), 
            'caja_id': self.caja_actual_id, 
            'descuento_total': self.descuento_global,
            'cae': None,
            'vencimiento_cae': None,
            'numero_factura': None
        }

        emitir_factura_fiscal = messagebox.askyesno(
            "Facturación Electrónica",
            "¿Desea emitir una factura fiscal (con CAE de AFIP) para esta venta?",
            parent=self
        )

        if emitir_factura_fiscal:
            datos_para_afip = {
                'total': total_final,
                'cliente_cuit': self.cliente_actual[2] if self.cliente_actual and self.cliente_actual[2] else ""
            }

            if not datos_para_afip['cliente_cuit']:
                messagebox.showerror("Error de Facturación", "Para emitir una factura fiscal, el cliente debe tener un CUIT/DNI cargado.", parent=self)
                return

            print("Solicitando CAE a la AFIP...")
            resultado_afip = afip_connector.solicitar_cae_factura(datos_para_afip)

            if resultado_afip.get("error"):
                messagebox.showerror("Error de AFIP", f"La AFIP rechazó la factura:\n\n{resultado_afip['error']}", parent=self)
                return

            if resultado_afip.get("cae"):
                datos_venta['cae'] = resultado_afip['cae']
                datos_venta['vencimiento_cae'] = resultado_afip['vencimiento']
                datos_venta['numero_factura'] = resultado_afip['numero_factura']
                datos_venta['tipo_comprobante'] = "Factura B"
        
        resultado_db = ventas_db.registrar_venta(datos_venta, self.carrito_items, pagos)
        
        if isinstance(resultado_db, int):
            venta_id = resultado_db
            messagebox.showinfo("Venta Finalizada", "Venta registrada exitosamente.", parent=self)
            
            if messagebox.askyesno("Imprimir Comprobante", "¿Desea imprimir el comprobante de la venta?", parent=self):
                from app.reports import ticket_generator
                try:
                    filepath, msg = ticket_generator.crear_comprobante_venta(venta_id)
                    if filepath:
                        if os.name == 'nt':
                            os.startfile(filepath)
                        else:
                            webbrowser.open(f"file://{os.path.realpath(filepath)}")
                    else:
                        messagebox.showerror("Error de Impresión", msg, parent=self)
                except Exception as e:
                    messagebox.showerror("Error de Impresión", f"No se pudo generar o abrir el comprobante.\nError: {e}", parent=self)
            
            self.limpiar_venta()
        else:
            messagebox.showerror("Error al Guardar", resultado_db, parent=self)

    def aplicar_descuento_item(self):
        selected_item_id = self.tree.focus()
        if not selected_item_id: messagebox.showwarning("Sin Selección", "Seleccione un artículo.", parent=self); return
        item_id = int(selected_item_id)
        if item_id not in self.carrito_items: return
        item_actual = self.carrito_items[item_id]
        subtotal_bruto = item_actual['cantidad'] * item_actual['precio_unit']
        dialogo = VentanaDescuento(self, title="Descuento por Ítem"); resultado = dialogo.result
        if resultado:
            valor, tipo = resultado; monto_descuento = 0.0
            if tipo == '%': monto_descuento = subtotal_bruto * (valor / 100)
            else: monto_descuento = valor
            if monto_descuento > subtotal_bruto: messagebox.showwarning("Inválido", "El descuento no puede ser mayor al subtotal del ítem.", parent=self); return
            self.carrito_items[item_id]['descuento'] = monto_descuento; self.refrescar_venta()
            
    def aplicar_descuento_total(self):
        subtotal_general = sum(data['cantidad'] * data['precio_unit'] for data in self.carrito_items.values())
        descuento_items = sum(data.get('descuento', 0.0) for data in self.carrito_items.values())
        max_descuento = subtotal_general - descuento_items
        dialogo = VentanaDescuento(self, title="Descuento al Total"); resultado = dialogo.result
        if resultado:
            valor, tipo = resultado; monto_descuento = 0.0
            if tipo == '%': monto_descuento = max_descuento * (valor / 100)
            else: monto_descuento = valor
            if monto_descuento > max_descuento: messagebox.showwarning("Inválido", "El descuento no puede ser mayor al total restante.", parent=self); return
            self.descuento_global = monto_descuento; self.refrescar_venta()