import tkinter as tk
from tkinter import ttk, messagebox, TclError, filedialog
from app.database import articulos_db
from app.gui.mixins.pricing_mixin import PricingLogicMixin
from app.gui.mixins.locale_validation_mixin import LocaleValidationMixin
from PIL import Image, ImageTk
import os
from tkcalendar import DateEntry
from datetime import datetime
from .mixins.centering_mixin import CenteringMixin

class VentanaAjusteStock(tk.Toplevel, CenteringMixin):
    # Esta ventana la crearemos en el siguiente paso.
    # Por ahora la dejamos como estaba o vacía.
    pass

class VentanaNuevaMarca(tk.Toplevel, CenteringMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.parent = parent
        self.title("Agregar Nueva Marca")
        self.transient(parent)
        self.frame = ttk.Frame(self, padding="10")
        self.frame.pack(fill='both', expand=True)
        ttk.Label(self.frame, text="Nombre de la Marca:").pack(pady=5)
        self.nombre_entry = ttk.Entry(self.frame, width=40)
        self.nombre_entry.pack(pady=5)
        self.nombre_entry.focus_set()
        ttk.Button(self.frame, text="Guardar Marca", command=self.guardar, style="Action.TButton").pack(pady=10)
        self.center_window()
        self.deiconify()
        self.grab_set()

    def guardar(self):
        nombre = self.nombre_entry.get()
        if not nombre:
            messagebox.showwarning("Campo Vacío", "El nombre no puede estar vacío.", parent=self); return
        resultado = articulos_db.agregar_marca(nombre)
        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            if hasattr(self.parent, 'refrescar_marcas'): self.parent.refrescar_marcas()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

class VentanaArticulo(tk.Toplevel, PricingLogicMixin, LocaleValidationMixin):
    def __init__(self, parent, articulo_id=None):
        super().__init__(parent)
        
        self.withdraw()
        self.parent = parent
        PricingLogicMixin.__init__(self)
        self.articulo_id = articulo_id
        self.imagen_path = None
        self._after_id = None

        titulo = "Editar Artículo" if self.articulo_id else "Agregar Nuevo Artículo"
        self.title(titulo)
        self.transient(parent)
        
        self.geometry("1100x700") # Aumentamos un poco el alto

        style = ttk.Style(self)
        style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        self.form_frame = ttk.Frame(main_frame)
        self.form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.form_frame.grid_columnconfigure(1, weight=1)
        self.form_frame.grid_columnconfigure(3, weight=1)
        
        image_container = ttk.Frame(main_frame, style="ContentPane.TFrame")
        image_container.grid(row=0, column=1, sticky="nsew")
        image_container.rowconfigure(1, weight=1); image_container.columnconfigure(0, weight=1)
        ttk.Label(image_container, text="Imagen del Producto", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        image_frame = ttk.Frame(image_container)
        image_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        image_frame.rowconfigure(0, weight=1); image_frame.columnconfigure(0, weight=1)

        self.image_label = ttk.Label(image_frame, text="Sin imagen", anchor="center")
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        btn_select_image = ttk.Button(image_frame, text="Seleccionar Imagen", command=self._seleccionar_imagen)
        btn_select_image.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        self.entries = {}
        row_num = 0
        
        # --- CAMPOS GENERALES (Siempre visibles) ---
        ttk.Label(self.form_frame, text="Nombre/Producto:").grid(row=row_num, column=0, columnspan=1, padx=5, pady=5, sticky="w")
        self.entries['nombre'] = ttk.Entry(self.form_frame)
        self.entries['nombre'].grid(row=row_num, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        row_num += 1
        
        ttk.Label(self.form_frame, text="Código de Barras:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['codigo_barras'] = ttk.Entry(self.form_frame)
        self.entries['codigo_barras'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.form_frame, text="Marca:").grid(row=row_num, column=2, padx=5, pady=5, sticky="w")
        marca_frame = ttk.Frame(self.form_frame)
        marca_frame.grid(row=row_num, column=3, padx=5, pady=5, sticky="ew")
        marca_frame.columnconfigure(0, weight=1)
        self.marca_combo = ttk.Combobox(marca_frame)
        self.marca_combo.grid(row=0, column=0, sticky="ew")
        self.marca_combo.bind("<KeyRelease>", self._iniciar_filtro_marcas)
        self.add_marca_btn = ttk.Button(marca_frame, text="+", width=2, command=self.abrir_ventana_nueva_marca)
        self.add_marca_btn.grid(row=0, column=1, padx=(5,0))
        row_num += 1
        
        ttk.Label(self.form_frame, text="Rubro:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.rubro_combo = ttk.Combobox(self.form_frame, state="readonly")
        self.rubro_combo.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.form_frame, text="Subrubro:").grid(row=row_num, column=2, padx=5, pady=5, sticky="w")
        self.subrubro_combo = ttk.Combobox(self.form_frame, state="readonly")
        self.subrubro_combo.grid(row=row_num, column=3, padx=5, pady=5, sticky="ew")
        row_num += 1
        
        ttk.Label(self.form_frame, text="Unidad de Medida:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['unidad_de_medida'] = ttk.Combobox(self.form_frame, values=["Un.", "Kg."], state="readonly")
        self.entries['unidad_de_medida'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.form_frame, text="Stock Mínimo (Alerta):").grid(row=row_num, column=2, padx=5, pady=5, sticky="w")
        self.entries['stock_minimo'] = ttk.Entry(self.form_frame)
        self.entries['stock_minimo'].grid(row=row_num, column=3, padx=5, pady=5, sticky="ew")
        row_num += 1
        
        # --- SECCIÓN DE LOTE INICIAL (Solo para artículos NUEVOS) ---
        self.lote_inicial_frame = ttk.Frame(self.form_frame)
        self.lote_inicial_frame.grid(row=row_num, column=0, columnspan=4, sticky="ew")
        self.lote_inicial_frame.columnconfigure(1, weight=1)
        self.lote_inicial_frame.columnconfigure(3, weight=1)

        ttk.Label(self.lote_inicial_frame, text="Stock Actual (Inicial):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entries['stock'] = ttk.Entry(self.lote_inicial_frame)
        self.entries['stock'].grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.lote_inicial_frame, text="Lote (Inicial):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entries['lote'] = ttk.Entry(self.lote_inicial_frame)
        self.entries['lote'].grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        ttk.Label(self.lote_inicial_frame, text="Fecha de Vencimiento (Inicial):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.fecha_vencimiento_entry = DateEntry(self.lote_inicial_frame, date_pattern='dd/mm/yyyy', width=12, toplevel_parent=self)
        self.fecha_vencimiento_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.fecha_vencimiento_entry.set_date(None)
        
        # --- SECCIÓN DE LISTA DE LOTES (Solo para artículos EXISTENTES) ---
        self.lotes_existentes_frame = ttk.LabelFrame(self.form_frame, text="Lotes de Stock", style="TLabelframe", padding=5)
        self.lotes_existentes_frame.grid(row=row_num, column=0, columnspan=4, sticky="nsew")
        self.lotes_existentes_frame.grid_rowconfigure(0, weight=1)
        self.lotes_existentes_frame.grid_columnconfigure(0, weight=1)
        self.form_frame.grid_rowconfigure(row_num, weight=1) # Hacemos que esta fila se expanda

        columnas_lotes = ("lote", "cantidad", "vencimiento", "ingreso")
        self.tree_lotes = ttk.Treeview(self.lotes_existentes_frame, columns=columnas_lotes, show="headings", height=5)
        self.tree_lotes.grid(row=0, column=0, sticky="nsew")
        
        self.tree_lotes.heading("lote", text="Lote")
        self.tree_lotes.heading("cantidad", text="Cantidad")
        self.tree_lotes.heading("vencimiento", text="Vencimiento")
        self.tree_lotes.heading("ingreso", text="Fecha Ingreso")
        self.tree_lotes.column("lote", width=150)
        self.tree_lotes.column("cantidad", width=100, anchor="e")
        self.tree_lotes.column("vencimiento", width=120, anchor="center")
        self.tree_lotes.column("ingreso", width=120, anchor="center")

        lotes_scrollbar = ttk.Scrollbar(self.lotes_existentes_frame, orient="vertical", command=self.tree_lotes.yview)
        lotes_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree_lotes.configure(yscrollcommand=lotes_scrollbar.set)
        
        row_num += 1

        # --- SECCIÓN DE PRECIOS (Siempre visible) ---
        ttk.Separator(self.form_frame, orient='horizontal').grid(row=row_num, column=0, columnspan=4, sticky='ew', pady=10)
        row_num += 1
        
        precios_frame = ttk.Frame(self.form_frame)
        precios_frame.grid(row=row_num, column=0, columnspan=4, sticky="ew")
        precios_frame.columnconfigure(1, weight=1)
        precios_frame.columnconfigure(3, weight=1)

        ttk.Label(precios_frame, text="Precio de Costo:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.costo_entry = ttk.Entry(precios_frame)
        self.entries['precio_costo'] = self.costo_entry
        self.costo_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(precios_frame, text="IVA (%):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.iva_combo = ttk.Combobox(precios_frame, values=["0", "10.5", "21"], state="readonly")
        self.entries['iva'] = self.iva_combo
        self.iva_combo.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        ttk.Label(precios_frame, text="Utilidad (%):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.utilidad_entry = ttk.Entry(precios_frame)
        self.entries['utilidad'] = self.utilidad_entry
        self.utilidad_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(precios_frame, text="Precio de Venta:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.venta_entry = ttk.Entry(precios_frame)
        self.entries['precio_venta'] = self.venta_entry
        self.venta_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        row_num += 1
        
        self.save_btn = ttk.Button(self.form_frame, text="Guardar", command=self.guardar, style="Action.TButton")
        self.save_btn.grid(row=row_num, column=0, columnspan=4, pady=15, padx=5, sticky="ew")

        # --- CONFIGURACIÓN FINAL ---
        self._setup_numeric_validation(self.entries['stock_minimo'])
        self._setup_numeric_validation(self.entries['stock'])
        self._setup_numeric_validation(self.costo_entry)
        self._setup_numeric_validation(self.utilidad_entry)
        self._setup_numeric_validation(self.venta_entry)

        self.cargar_comboboxes()
        self.bind_pricing_events() # Llama al método del mixin
        self.rubro_combo.bind("<<ComboboxSelected>>", self.actualizar_subrubros)

        if self.articulo_id:
            self.lote_inicial_frame.grid_forget() # Ocultamos los campos de lote inicial
            self.cargar_datos_articulo()
        else:
            self.lotes_existentes_frame.grid_forget() # Ocultamos la tabla de lotes
            self.entries['unidad_de_medida'].set("Un.")
            self.iva_combo.set("21")
            self.entries['stock'].insert(0, self._format_local_number(0))
            self.entries['stock_minimo'].insert(0, self._format_local_number(0))
        
        self.deiconify()
        self.grab_set()

    # --- INICIO DE MÉTODOS DE LÓGICA Y EVENTOS ---

    def _redondear_a_multiplo(self, precio, multiplo):
        """Redondea un precio al múltiplo más cercano (ej: 50 o 100)."""
        if multiplo == 0:
            return precio
        return round(precio / multiplo) * multiplo

    def _calcular_desde_costo_utilidad(self, event=None):
        """SOBRESCRITO: Reemplaza la lógica del mixin para añadir el redondeo."""
        try:
            costo = self._parse_local_number(self.costo_entry.get()) or 0.0
            iva_porc = float(self.iva_combo.get() or "0")
            util_porc = self._parse_local_number(self.utilidad_entry.get()) or 0.0
            
            costo_con_iva = costo * (1 + iva_porc / 100)
            precio_venta_raw = costo_con_iva * (1 + util_porc / 100)

            rubro_nombre = self.rubro_combo.get()
            multiplo = 50 if rubro_nombre == "GRANEL" else 100
            precio_final = self._redondear_a_multiplo(precio_venta_raw, multiplo)
            
            self.venta_entry.delete(0, tk.END)
            self.venta_entry.insert(0, self._format_local_number(precio_final))

            if costo_con_iva > 0:
                utilidad_real = ((precio_final / costo_con_iva) - 1) * 100
                self.utilidad_entry.delete(0, tk.END)
                self.utilidad_entry.insert(0, self._format_local_number(utilidad_real))
        except (ValueError, TclError):
            pass
    
    def _iniciar_filtro_marcas(self, event):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(300, self._filtrar_marcas_combobox)

    def _filtrar_marcas_combobox(self, event=None):
        criterio = self.marca_combo.get().lower()
        if not hasattr(self, 'marcas_data'): return
        if not criterio:
            marcas_filtradas = [m[1] for m in self.marcas_data]
        else:
            marcas_filtradas = [m[1] for m in self.marcas_data if criterio in m[1].lower()]
        
        seleccion_actual = self.marca_combo.get()
        self.marca_combo['values'] = marcas_filtradas
        
        if seleccion_actual in marcas_filtradas:
            self.marca_combo.set(seleccion_actual)
        
        if criterio and marcas_filtradas:
             self.marca_combo.event_generate('<Down>')

    def refrescar_marcas(self):
        valor_actual = self.marca_combo.get()
        self.cargar_comboboxes()
        self.marca_combo.set(valor_actual)

    def cargar_comboboxes(self):
        self.marcas_data = articulos_db.obtener_marcas()
        self.marca_combo['values'] = [m[1] for m in self.marcas_data]
        self.rubros_data = articulos_db.obtener_rubros()
        self.rubro_combo['values'] = [r[1] for r in self.rubros_data]

    def _seleccionar_imagen(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar imagen de producto",
            filetypes=(("Archivos de imagen", "*.jpg *.jpeg *.png *.gif"), ("Todos los archivos", "*.*"))
        )
        if filepath:
            self.imagen_path = filepath
            self._mostrar_imagen(filepath)

    def _mostrar_imagen(self, filepath):
        if filepath and os.path.exists(filepath):
            try:
                img = Image.open(filepath)
                img.thumbnail((250, 250))
                self.photo_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.photo_image, text="")
            except Exception as e:
                self.image_label.config(image=None, text="Error al\ncargar imagen")
                print(f"Error cargando imagen: {e}")
        else:
            self.image_label.config(image=None, text="Sin imagen")
            self.imagen_path = None
    
    def abrir_ventana_nueva_marca(self):
        VentanaNuevaMarca(self)

    def actualizar_subrubros(self, event=None):
        rubro_nombre = self.rubro_combo.get()
        rubro_id = next((rid for rid, nombre in self.rubros_data if nombre == rubro_nombre), None)
        if rubro_id:
            self.subrubros_data = articulos_db.obtener_subrubros_por_rubro(rubro_id)
            self.subrubro_combo['values'] = [s[1] for s in self.subrubros_data]
            self.subrubro_combo.set('')

    def cargar_datos_articulo(self):
        articulo = articulos_db.obtener_articulo_por_id(self.articulo_id)
        if not articulo:
            messagebox.showerror("Error", "No se pudo encontrar el artículo.", parent=self)
            self.destroy()
            return
            
        columnas = articulos_db.get_articulo_column_names()
        articulo_dict = dict(zip(columnas, articulo))

        self.entries['nombre'].insert(0, articulo_dict.get('nombre', ''))
        self.entries['codigo_barras'].insert(0, articulo_dict.get('codigo_barras', ''))
        self.entries['stock_minimo'].insert(0, self._format_local_number(articulo_dict.get('stock_minimo', 0.0)))
        self.costo_entry.insert(0, self._format_local_number(articulo_dict.get('precio_costo', 0.0)))
        self.utilidad_entry.insert(0, self._format_local_number(articulo_dict.get('utilidad', 0.0)))
        self.venta_entry.insert(0, self._format_local_number(articulo_dict.get('precio_venta', 0.0)))
        
        unidad_guardada = articulo_dict.get('unidad_de_medida')
        if unidad_guardada and unidad_guardada in self.entries['unidad_de_medida']['values']:
            self.entries['unidad_de_medida'].set(unidad_guardada)
        else:
            self.entries['unidad_de_medida'].set("Un.")

        self.entries['iva'].set(str(articulo_dict.get('iva', '21')))
        
        marca_nombre = next((m[1] for m in self.marcas_data if m[0] == articulo_dict.get('marca_id')), "")
        self.marca_combo.set(marca_nombre)
        
        subrubro_id = articulo_dict.get('subrubro_id')
        if subrubro_id:
            rubro_info = articulos_db.obtener_rubro_de_subrubro(subrubro_id)
            if rubro_info:
                rubro_id, rubro_nombre = rubro_info
                self.rubro_combo.set(rubro_nombre)
                self.actualizar_subrubros()
                subrubro_nombre = next((s[1] for s in self.subrubros_data if s[0] == subrubro_id), "")
                self.subrubro_combo.set(subrubro_nombre)

        self.imagen_path = articulo_dict.get('imagen_path')
        self._mostrar_imagen(self.imagen_path)
        
        # --- Llenar la tabla de lotes ---
        for i in self.tree_lotes.get_children(): self.tree_lotes.delete(i) # Limpiamos la tabla
        lotes = articulos_db.obtener_lotes_por_articulo(self.articulo_id)
        for lote in lotes:
            (lote_id, nombre_lote, cantidad, vencimiento, ingreso, activo) = lote
            
            # Formateamos los datos para que se vean bien
            cant_formateada = self._format_local_number(cantidad)
            venc_formateado = datetime.strptime(vencimiento, '%Y-%m-%d').strftime('%d/%m/%Y') if vencimiento else "N/A"
            ing_formateado = datetime.fromisoformat(ingreso).strftime('%d/%m/%Y')
            
            self.tree_lotes.insert("", "end", values=(nombre_lote or "S/N", cant_formateada, venc_formateado, ing_formateado))
        
    def guardar(self):
        datos = {}
        try:
            codigo_barras = self.entries['codigo_barras'].get().strip()
            datos['codigo_barras'] = codigo_barras if codigo_barras else None
            
            datos['nombre'] = self.entries['nombre'].get()
            datos['unidad_de_medida'] = self.entries['unidad_de_medida'].get()
            datos['iva'] = self.get_validated_float(self.entries['iva'], "IVA")
            
            datos['stock_minimo'] = self.get_validated_float(self.entries['stock_minimo'], "Stock Mínimo")
            datos['precio_costo'] = self.get_validated_float(self.costo_entry, "Precio de Costo")
            datos['utilidad'] = self.get_validated_float(self.utilidad_entry, "Utilidad")
            datos['precio_venta'] = self.get_validated_float(self.venta_entry, "Precio de Venta")
            
            if not self.articulo_id:
                datos['stock'] = self.get_validated_float(self.entries['stock'], "Stock Actual")
                datos['lote'] = self.entries['lote'].get()
                fecha_vencimiento_str = self.fecha_vencimiento_entry.get()
                if fecha_vencimiento_str:
                    try:
                        fecha_obj = datetime.strptime(fecha_vencimiento_str, '%d/%m/%Y')
                        datos['fecha_vencimiento'] = fecha_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        messagebox.showerror("Error de Fecha", "El formato de fecha es incorrecto.", parent=self); return
                else:
                    datos['fecha_vencimiento'] = None
            
        except ValueError:
            return

        marca_nombre = self.marca_combo.get()
        datos['marca_id'] = next((mid for mid, nombre in self.marcas_data if nombre == marca_nombre), None)
        subrubro_nombre = self.subrubro_combo.get()
        if subrubro_nombre and hasattr(self, 'subrubros_data'):
            datos['subrubro_id'] = next((sid for sid, nombre in self.subrubros_data if nombre == subrubro_nombre), None)

        if not datos.get("nombre"):
            messagebox.showwarning("Campo Vacío", "El nombre del producto es obligatorio.", parent=self)
            return
        
        datos['imagen_path'] = self.imagen_path

        if self.articulo_id:
            datos['id'] = self.articulo_id
            resultado = articulos_db.modificar_articulo(datos)
        else:
            resultado = articulos_db.agregar_articulo(datos)
        
        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            if hasattr(self.parent, 'actualizar_lista'):
                self.parent.actualizar_lista()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

# --- CLASE PRINCIPAL DEL FRAME ---
class ArticulosFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.style.configure("SectionTitle.TLabel", background="#4a4a4a", foreground="white", font=("Helvetica", 11, "bold"), padding=5, anchor="center")
        self.style.configure("ContentPane.TFrame", background="white", borderwidth=1, relief="solid", bordercolor="#cccccc")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, minsize=250)

        filtros_frame = ttk.Frame(self, style="Content.TFrame")
        filtros_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=(10,0), sticky="ew")
        
        ttk.Label(filtros_frame, text="Buscar:").pack(side="left", padx=(0,5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda name, index, mode: self.actualizar_lista())
        search_entry = ttk.Entry(filtros_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", fill="x", expand=True)
        
        self.ver_inactivos_var = tk.BooleanVar()
        self.check_inactivos = ttk.Checkbutton(filtros_frame, text="Ver inactivos", variable=self.ver_inactivos_var, command=self.actualizar_lista)
        self.check_inactivos.pack(side="left", padx=10)

        tree_container = ttk.Frame(self, style="ContentPane.TFrame")
        tree_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        tree_container.rowconfigure(1, weight=1)
        tree_container.columnconfigure(0, weight=1)

        ttk.Label(tree_container, text="Listado de Artículos", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        self.tree_frame = ttk.Frame(tree_container, padding=5)
        self.tree_frame.grid(row=1, column=0, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        
        columnas = ("id", "codigo", "marca", "nombre", "stock", "precio_venta", "estado", "unidad", "imagen_path")
        self.tree = ttk.Treeview(self.tree_frame, columns=columnas, show="headings")
        self.tree.configure(displaycolumns=("codigo", "marca", "nombre", "stock", "precio_venta", "estado"))
        self.tree.heading("codigo", text="Código"); self.tree.heading("marca", text="Marca"); self.tree.heading("nombre", text="Nombre"); self.tree.heading("stock", text="Stock"); self.tree.heading("precio_venta", text="Precio Venta"); self.tree.heading("estado", text="Estado")
        self.tree.column("codigo", width=150); self.tree.column("marca", width=120); self.tree.column("nombre", width=300); self.tree.column("stock", width=100, anchor='center'); self.tree.column("precio_venta", width=100, anchor='e'); self.tree.column("estado", width=80, anchor='center')
        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind("<Double-1>", self.abrir_ventana_edicion)
        self.tree.bind("<<TreeviewSelect>>", self.on_item_selected)
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        right_column_frame = ttk.Frame(self, style="Content.TFrame")
        right_column_frame.grid(row=1, column=1, padx=(0, 10), pady=10, sticky="nsew")
        right_column_frame.grid_rowconfigure(1, weight=1)
        right_column_frame.grid_columnconfigure(0, weight=1)
        self.button_frame = ttk.Frame(right_column_frame, style="Content.TFrame")
        self.button_frame.grid(row=0, column=0, sticky="ew")
        self.add_btn = ttk.Button(self.button_frame, text="Agregar Nuevo", command=self.abrir_ventana_creacion, style="Action.TButton"); self.add_btn.pack(pady=5, fill='x')
        self.update_btn = ttk.Button(self.button_frame, text="Modificar", command=self.abrir_ventana_edicion, style="Action.TButton"); self.update_btn.pack(pady=5, fill='x')
        self.btn_toggle_estado = ttk.Button(self.button_frame, text="Desactivar", style="Action.TButton"); self.btn_toggle_estado.pack(pady=5, fill='x')
        self.btn_ajuste_stock = ttk.Button(self.button_frame, text="Ajuste de Stock", command=self.abrir_ventana_ajuste_stock, style="Action.TButton"); self.btn_ajuste_stock.pack(pady=5, fill='x')
        
        image_preview_container = ttk.Frame(right_column_frame, style="ContentPane.TFrame")
        image_preview_container.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        image_preview_container.grid_rowconfigure(1, weight=1); image_preview_container.grid_columnconfigure(0, weight=1)
        ttk.Label(image_preview_container, text="Vista Previa", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="ew")
        self.image_preview_frame = ttk.Frame(image_preview_container, padding=5)
        self.image_preview_frame.grid(row=1, column=0, sticky="nsew")
        self.image_preview_frame.grid_rowconfigure(0, weight=1); self.image_preview_frame.grid_columnconfigure(0, weight=1)
        
        self.image_label = ttk.Label(self.image_preview_frame, text="Seleccione un artículo", anchor="center")
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.photo_image = None

        self.actualizar_lista()

    def _mostrar_imagen(self, filepath):
        if filepath and os.path.exists(filepath):
            try:
                img = Image.open(filepath); img.thumbnail((200, 200)); self.photo_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.photo_image, text="")
            except Exception as e:
                self.image_label.config(image='', text="Error al\ncargar imagen"); self.photo_image = None; print(f"Error cargando imagen de vista previa: {e}")
        else:
            self.image_label.config(image='', text="Sin imagen"); self.photo_image = None

    def actualizar_lista(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        ver_inactivos = self.ver_inactivos_var.get(); criterio = self.search_var.get()
        articulos = articulos_db.obtener_articulos(criterio=criterio, incluir_inactivos=ver_inactivos)
        for articulo in articulos:
            id_art, codigo, marca, nombre, stock, precio, estado, unidad, imagen_path = articulo
            precio_formateado = f"$ {LocaleValidationMixin._format_local_number(precio or 0.0)}"
            stock_formateado = f"{LocaleValidationMixin._format_local_number(stock or 0.0)} {unidad or 'Un.'}"
            valores_completos = (id_art, codigo, marca, nombre, stock_formateado, precio_formateado, estado, unidad, imagen_path)
            self.tree.insert("", "end", values=valores_completos)
        self.on_item_selected()

    def on_item_selected(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            self.btn_toggle_estado.config(state="disabled"); self._mostrar_imagen(None); return
        self.btn_toggle_estado.config(state="normal")
        values = self.tree.item(selected_item, "values")
        if not values: return
        estado = values[6]
        if estado == 'Activo':
            self.btn_toggle_estado.config(text="Desactivar", command=self.desactivar_articulo_seleccionado)
        else:
            self.btn_toggle_estado.config(text="Reactivar", command=self.reactivar_articulo_seleccionado)
        imagen_path = values[8]
        self._mostrar_imagen(imagen_path)

    def abrir_ventana_creacion(self):
        VentanaArticulo(self)

    def abrir_ventana_edicion(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un artículo de la lista."); return
        articulo_id = self.tree.item(selected_item, "values")[0]
        VentanaArticulo(self, articulo_id=articulo_id)

    def desactivar_articulo_seleccionado(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        articulo_id = self.tree.item(selected_item, "values")[0]
        nombre_articulo = self.tree.item(selected_item, "values")[3]
        if messagebox.askyesno("Confirmar", f"¿Está seguro de que desea desactivar el artículo '{nombre_articulo}'?"):
            resultado = articulos_db.desactivar_articulo(articulo_id)
            messagebox.showinfo("Resultado", resultado); self.actualizar_lista()

    def reactivar_articulo_seleccionado(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        articulo_id = self.tree.item(selected_item, "values")[0]
        nombre_articulo = self.tree.item(selected_item, "values")[3]
        if messagebox.askyesno("Confirmar", f"¿Está seguro de que desea reactivar el artículo '{nombre_articulo}'?"):
            resultado = articulos_db.reactivar_articulo(articulo_id)
            messagebox.showinfo("Resultado", resultado); self.actualizar_lista()

    def abrir_ventana_ajuste_stock(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Seleccione un artículo para realizar un ajuste de stock."); return
        articulo_seleccionado = self.tree.item(selected_item, "values")
        VentanaAjusteStock(self, articulo_seleccionado)