import tkinter as tk
from tkinter import ttk, messagebox, TclError, filedialog
from app.database import articulos_db
from .mixins.pricing_mixin import PricingLogicMixin
from PIL import Image, ImageTk
import os

class VentanaAjusteStock(tk.Toplevel):
    def __init__(self, parent, articulo):
        super().__init__(parent)
        self.parent = parent
        stock_valor = str(articulo[4]).split()[0]
        
        self.articulo_id = articulo[0]
        self.nombre_articulo = f"{articulo[3]} ({articulo[2]})"

        self.title("Ajuste de Stock")
        self.geometry("450x300")
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding="10")
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Artículo:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(frame, text=self.nombre_articulo).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(frame, text="Stock Actual:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(frame, text=stock_valor).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(frame, text="Tipo de Ajuste:").grid(row=2, column=0, sticky="w", padx=5, pady=10)
        self.tipo_ajuste_combo = ttk.Combobox(frame, values=["Ingreso Extraordinario", "Egreso por Vencimiento"], state="readonly")
        self.tipo_ajuste_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=10)
        
        ttk.Label(frame, text="Cantidad:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.cantidad_entry = ttk.Entry(frame)
        self.cantidad_entry.grid(row=3, column=1, sticky="ew", padx=5)

        ttk.Label(frame, text="Concepto/Motivo:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.concepto_entry = ttk.Entry(frame)
        self.concepto_entry.grid(row=4, column=1, sticky="ew", padx=5)
        
        btn_confirmar = ttk.Button(frame, text="Confirmar Ajuste", command=self.confirmar_ajuste)
        btn_confirmar.grid(row=5, column=0, columnspan=2, pady=20, padx=5, sticky="ew")

        self.tipo_ajuste_combo.focus_set()

    def confirmar_ajuste(self):
        tipo_seleccionado = self.tipo_ajuste_combo.get()
        concepto = self.concepto_entry.get()
        
        if not tipo_seleccionado:
            messagebox.showwarning("Dato Faltante", "Debe seleccionar un tipo de ajuste.", parent=self)
            return

        try:
            cantidad = float(self.cantidad_entry.get())
            if cantidad <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Dato Inválido", "La cantidad debe ser un número positivo.", parent=self)
            return

        tipo_ajuste_db = 'INGRESO' if "Ingreso" in tipo_seleccionado else 'EGRESO'
        
        if not concepto:
            concepto = tipo_seleccionado

        resultado = articulos_db.realizar_ajuste_stock(self.articulo_id, tipo_ajuste_db, cantidad, concepto)

        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self.parent)
            self.parent.actualizar_lista()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

class VentanaNuevaMarca(tk.Toplevel):
    # ... (Esta clase no cambia, la dejamos como está)
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Agregar Nueva Marca")
        self.geometry("300x150")
        self.transient(parent)
        self.grab_set()
        self.frame = ttk.Frame(self, padding="10")
        self.frame.pack(fill='both', expand=True)
        ttk.Label(self.frame, text="Nombre de la Marca:").pack(pady=5)
        self.nombre_entry = ttk.Entry(self.frame, width=40)
        self.nombre_entry.pack(pady=5)
        self.nombre_entry.focus_set()
        ttk.Button(self.frame, text="Guardar Marca", command=self.guardar, style="Action.TButton").pack(pady=10)
    def guardar(self):
        nombre = self.nombre_entry.get()
        if not nombre:
            messagebox.showwarning("Campo Vacío", "El nombre no puede estar vacío.", parent=self)
            return
        resultado = articulos_db.agregar_marca(nombre)
        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            if hasattr(self.parent, 'refrescar_marcas'):
                self.parent.refrescar_marcas()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)


class VentanaArticulo(tk.Toplevel, PricingLogicMixin):
    def __init__(self, parent, articulo_id=None):
        super().__init__(parent)
        PricingLogicMixin.__init__(self)
        self.parent = parent
        self.articulo_id = articulo_id
        self.imagen_path = None # <-- NUEVO: Para guardar la ruta de la imagen

        titulo = "Editar Artículo" if self.articulo_id else "Agregar Nuevo Artículo"
        self.title(titulo)
        # --- Aumentamos el tamaño de la ventana para dar espacio a la imagen ---
        self.geometry("950x370")
        self.transient(parent)
        self.grab_set()

        # --- Creamos un frame principal y lo dividimos en dos columnas ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        main_frame.grid_columnconfigure(0, weight=2) # Columna de datos más ancha
        main_frame.grid_columnconfigure(1, weight=1) # Columna de imagen
        main_frame.grid_rowconfigure(0, weight=1)

        # Frame izquierdo para los campos de datos
        self.form_frame = ttk.Frame(main_frame)
        self.form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.form_frame.grid_columnconfigure(1, weight=1)
        self.form_frame.grid_columnconfigure(3, weight=1)
        
        # --- NUEVO: Frame derecho para la imagen ---
        image_frame = ttk.Labelframe(main_frame, text="Imagen del Producto")
        image_frame.grid(row=0, column=1, sticky="nsew")
        image_frame.rowconfigure(0, weight=1)
        image_frame.columnconfigure(0, weight=1)

        self.image_label = ttk.Label(image_frame, text="Sin imagen", anchor="center")
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        btn_select_image = ttk.Button(image_frame, text="Seleccionar Imagen", command=self._seleccionar_imagen)
        btn_select_image.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # --- Llenado del formulario (ahora en self.form_frame) ---
        self.entries = {}
        row_num = 0
        
        # ... (Definición de widgets de Nombre, Código, Marca, Rubro, Subrubro, etc. sin cambios) ...
        # ... La única diferencia es que su padre ahora es self.form_frame ...
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
        self.marca_combo = ttk.Combobox(marca_frame, state="readonly")
        self.entries['marca_id'] = self.marca_combo
        self.marca_combo.grid(row=0, column=0, sticky="ew")
        self.add_marca_btn = ttk.Button(marca_frame, text="+", width=2, command=self.abrir_ventana_nueva_marca)
        self.add_marca_btn.grid(row=0, column=1, padx=(5,0))
        row_num += 1
        ttk.Label(self.form_frame, text="Rubro:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.rubro_combo = ttk.Combobox(self.form_frame, state="readonly")
        self.rubro_combo.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(self.form_frame, text="Subrubro:").grid(row=row_num, column=2, padx=5, pady=5, sticky="w")
        self.subrubro_combo = ttk.Combobox(self.form_frame, state="readonly")
        self.entries['subrubro_id'] = self.subrubro_combo
        self.subrubro_combo.grid(row=row_num, column=3, padx=5, pady=5, sticky="ew")
        row_num += 1
        ttk.Label(self.form_frame, text="Unidad de Medida:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['unidad_de_medida'] = ttk.Combobox(self.form_frame, values=["Un.", "Kg."], state="readonly")
        self.entries['unidad_de_medida'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(self.form_frame, text="Stock Mínimo (Alerta):").grid(row=row_num, column=2, padx=5, pady=5, sticky="w")
        self.entries['stock_minimo'] = ttk.Entry(self.form_frame)
        self.entries['stock_minimo'].grid(row=row_num, column=3, padx=5, pady=5, sticky="ew")
        row_num += 1
        ttk.Label(self.form_frame, text="Stock Actual:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.entries['stock'] = ttk.Entry(self.form_frame)
        self.entries['stock'].grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        row_num += 1
        ttk.Separator(self.form_frame, orient='horizontal').grid(row=row_num, column=0, columnspan=4, sticky='ew', pady=10)
        row_num += 1
        ttk.Label(self.form_frame, text="Precio de Costo:").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.costo_entry = ttk.Entry(self.form_frame)
        self.entries['precio_costo'] = self.costo_entry
        self.costo_entry.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(self.form_frame, text="IVA (%):").grid(row=row_num, column=2, padx=5, pady=5, sticky="w")
        self.iva_combo = ttk.Combobox(self.form_frame, values=["0", "10.5", "21"], state="readonly")
        self.entries['iva'] = self.iva_combo
        self.iva_combo.grid(row=row_num, column=3, padx=5, pady=5, sticky="ew")
        row_num += 1
        ttk.Label(self.form_frame, text="Utilidad (%):").grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        self.utilidad_entry = ttk.Entry(self.form_frame)
        self.entries['utilidad'] = self.utilidad_entry
        self.utilidad_entry.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(self.form_frame, text="Precio de Venta:").grid(row=row_num, column=2, padx=5, pady=5, sticky="w")
        self.venta_entry = ttk.Entry(self.form_frame)
        self.entries['precio_venta'] = self.venta_entry
        self.venta_entry.grid(row=row_num, column=3, padx=5, pady=5, sticky="ew")
        row_num += 1
        
        self.save_btn = ttk.Button(self.form_frame, text="Guardar", command=self.guardar)
        self.save_btn.grid(row=row_num, column=0, columnspan=4, pady=15, padx=5, sticky="ew")

        self.cargar_comboboxes()
        self.bind_pricing_events()
        self.rubro_combo.bind("<<ComboboxSelected>>", self.actualizar_subrubros)

        if self.articulo_id:
            self.cargar_datos_articulo()
        else:
            self.entries['unidad_de_medida'].set("Un.")
            self.iva_combo.set("21")
            self.entries['stock'].insert(0, "0.0")
            self.entries['stock_minimo'].insert(0, "0.0")

    # --- NUEVOS MÉTODOS PARA MANEJAR LA IMAGEN ---
    def _seleccionar_imagen(self):
        # Abrir diálogo para seleccionar archivo
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
                # Redimensionar para la vista previa
                img.thumbnail((250, 250))
                self.photo_image = ImageTk.PhotoImage(img) # Guardar referencia
                self.image_label.config(image=self.photo_image, text="")
            except Exception as e:
                self.image_label.config(image=None, text="Error al\ncargar imagen")
                print(f"Error cargando imagen: {e}")
        else:
            self.image_label.config(image=None, text="Sin imagen")
            self.imagen_path = None
    
    # ... (el resto de los métodos como abrir_ventana_nueva_marca, cargar_comboboxes, etc., no cambian)
    def abrir_ventana_nueva_marca(self): VentanaNuevaMarca(self)
    def refrescar_marcas(self): self.cargar_comboboxes()
    def cargar_comboboxes(self):
        self.marcas_data = articulos_db.obtener_marcas()
        self.marca_combo['values'] = [m[1] for m in self.marcas_data]
        self.rubros_data = articulos_db.obtener_rubros()
        self.rubro_combo['values'] = [r[1] for r in self.rubros_data]
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

        for clave, entry in self.entries.items():
            valor = articulo_dict.get(clave)
            if valor is not None:
                if isinstance(entry, ttk.Combobox):
                    # No insertar en combobox, usar set()
                    pass
                else:
                    entry.delete(0, tk.END)
                    entry.insert(0, str(valor))
        
        # Seteamos los valores de los combobox
        self.entries['unidad_de_medida'].set(articulo_dict.get('unidad_de_medida', 'Un.'))
        self.entries['iva'].set(articulo_dict.get('iva', '21'))
        
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

        # --- NUEVO: Cargar y mostrar la imagen del artículo ---
        self.imagen_path = articulo_dict.get('imagen_path')
        self._mostrar_imagen(self.imagen_path)

    def guardar(self):
        datos = {clave: entry.get() for clave, entry in self.entries.items() if entry.get()}
        
        if not datos.get("nombre"):
            messagebox.showwarning("Campo Vacío", "El nombre del producto es obligatorio.", parent=self)
            return
        
        try:
            marca_nombre = self.marca_combo.get()
            datos['marca_id'] = next((mid for mid, nombre in self.marcas_data if nombre == marca_nombre), None)
            subrubro_nombre = self.subrubro_combo.get()
            if subrubro_nombre:
                datos['subrubro_id'] = next((sid for sid, nombre in self.subrubros_data if nombre == subrubro_nombre), None) if hasattr(self, 'subrubros_data') else None
        except Exception as e:
            messagebox.showerror("Error de Datos", f"Por favor, seleccione valores válidos. Error: {e}", parent=self)
            return

        # --- NUEVO: Añadimos la ruta de la imagen a los datos a guardar ---
        datos['imagen_path'] = self.imagen_path

        if self.articulo_id:
            datos['id'] = self.articulo_id
            resultado = articulos_db.modificar_articulo(datos)
        else:
            resultado = articulos_db.agregar_articulo(datos)
        
        if "correctamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            self.parent.actualizar_lista()
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)

class ArticulosFrame(ttk.Frame):
    # ... (Esta clase no tiene cambios)
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        filtros_frame = ttk.Frame(self, style="Content.TFrame")
        filtros_frame.grid(row=0, column=0, padx=10, pady=(10,0), sticky="ew")
        ttk.Label(filtros_frame, text="Buscar:").pack(side="left", padx=(0,5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda name, index, mode: self.actualizar_lista())
        search_entry = ttk.Entry(filtros_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", fill="x", expand=True)
        self.ver_inactivos_var = tk.BooleanVar()
        self.check_inactivos = ttk.Checkbutton(filtros_frame, text="Ver inactivos", variable=self.ver_inactivos_var, command=self.actualizar_lista)
        self.check_inactivos.pack(side="left", padx=10)
        self.tree_frame = ttk.Frame(self, style="Content.TFrame")
        self.tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        columnas = ("id", "codigo", "marca", "nombre", "stock", "precio_venta", "estado")
        self.tree = ttk.Treeview(self.tree_frame, columns=columnas, show="headings")
        self.tree.heading("codigo", text="Código")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("precio_venta", text="Precio Venta")
        self.tree.heading("estado", text="Estado")
        self.tree.column("id", width=0, stretch=tk.NO)
        self.tree.column("codigo", width=150)
        self.tree.column("marca", width=120)
        self.tree.column("nombre", width=300)
        self.tree.column("stock", width=100, anchor='center')
        self.tree.column("precio_venta", width=100, anchor='e')
        self.tree.column("estado", width=80, anchor='center')
        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind("<Double-1>", self.abrir_ventana_edicion)
        self.tree.bind("<<TreeviewSelect>>", self.actualizar_botones_estado)
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.button_frame = ttk.Frame(self, style="Content.TFrame")
        self.button_frame.grid(row=1, column=1, padx=10, pady=10, sticky="ns")
        self.add_btn = ttk.Button(self.button_frame, text="Agregar Nuevo", command=self.abrir_ventana_creacion, style="Action.TButton")
        self.add_btn.pack(pady=5, fill='x')
        self.update_btn = ttk.Button(self.button_frame, text="Modificar", command=self.abrir_ventana_edicion, style="Action.TButton")
        self.update_btn.pack(pady=5, fill='x')
        self.btn_toggle_estado = ttk.Button(self.button_frame, text="Desactivar", style="Action.TButton")
        self.btn_toggle_estado.pack(pady=5, fill='x')
        self.btn_ajuste_stock = ttk.Button(self.button_frame, text="Ajuste de Stock", command=self.abrir_ventana_ajuste_stock, style="Action.TButton")
        self.btn_ajuste_stock.pack(pady=5, fill='x')
        self.actualizar_lista()
    def actualizar_lista(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        ver_inactivos = self.ver_inactivos_var.get()
        criterio = self.search_var.get()
        articulos = articulos_db.obtener_articulos(criterio=criterio, incluir_inactivos=ver_inactivos)
        for articulo in articulos:
            id_art, codigo, marca, nombre, stock, precio, estado, unidad = articulo
            unidad_str = unidad if unidad else "Un."
            stock_formateado = f"{stock} {unidad_str}"
            valores_para_mostrar = (id_art, codigo, marca, nombre, stock_formateado, precio, estado)
            self.tree.insert("", "end", values=valores_para_mostrar)
        self.actualizar_botones_estado()
    def actualizar_botones_estado(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            self.btn_toggle_estado.config(state="disabled")
            return
        self.btn_toggle_estado.config(state="normal")
        values = self.tree.item(selected_item, "values")
        if not values: return
        estado = values[6]
        if estado == 'Activo':
            self.btn_toggle_estado.config(text="Desactivar", command=self.desactivar_articulo_seleccionado)
        else:
            self.btn_toggle_estado.config(text="Reactivar", command=self.reactivar_articulo_seleccionado)
    def abrir_ventana_creacion(self):
        VentanaArticulo(self)
    def abrir_ventana_edicion(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un artículo de la lista.")
            return
        articulo_id = self.tree.item(selected_item, "values")[0]
        VentanaArticulo(self, articulo_id=articulo_id)
    def desactivar_articulo_seleccionado(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        articulo_id = self.tree.item(selected_item, "values")[0]
        nombre_articulo = self.tree.item(selected_item, "values")[3]
        if messagebox.askyesno("Confirmar", f"¿Está seguro de que desea desactivar el artículo '{nombre_articulo}'?"):
            resultado = articulos_db.desactivar_articulo(articulo_id)
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista()
    def reactivar_articulo_seleccionado(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        articulo_id = self.tree.item(selected_item, "values")[0]
        nombre_articulo = self.tree.item(selected_item, "values")[3]
        if messagebox.askyesno("Confirmar", f"¿Está seguro de que desea reactivar el artículo '{nombre_articulo}'?"):
            resultado = articulos_db.reactivar_articulo(articulo_id)
            messagebox.showinfo("Resultado", resultado)
            self.actualizar_lista()
    def abrir_ventana_ajuste_stock(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Seleccione un artículo para realizar un ajuste de stock.")
            return
        articulo_seleccionado = self.tree.item(selected_item, "values")
        VentanaAjusteStock(self, articulo_seleccionado)