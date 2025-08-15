# Archivo: app/gui/usuarios_abm.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.database import usuarios_db

class UsuariosFrame(ttk.Frame):
    def __init__(self, parent, style):
        super().__init__(parent, style="Content.TFrame")
        self.style = style

        self.MODULOS = ["Caja", "POS / Venta", "Artículos", "Clientes", "Proveedores", "Compras", "Reportes", "Configuración"]

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=300)
        self.grid_columnconfigure(1, weight=2)

        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        user_list_frame = ttk.LabelFrame(left_frame, text="Usuarios del Sistema")
        user_list_frame.pack(fill="both", expand=True)

        columnas = ("id", "usuario", "rol")
        self.tree_usuarios = ttk.Treeview(user_list_frame, columns=columnas, show="headings")
        self.tree_usuarios.heading("id", text="ID")
        self.tree_usuarios.heading("usuario", text="Nombre de Usuario")
        self.tree_usuarios.heading("rol", text="Rol")
        self.tree_usuarios.column("id", width=40, anchor="center")
        self.tree_usuarios.pack(fill="both", expand=True, side="left")
        
        scrollbar = ttk.Scrollbar(user_list_frame, orient="vertical", command=self.tree_usuarios.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_usuarios.configure(yscrollcommand=scrollbar.set)
        
        self.tree_usuarios.bind("<<TreeviewSelect>>", self.mostrar_permisos_usuario)
        
        user_actions_frame = ttk.Frame(left_frame)
        user_actions_frame.pack(fill="x", pady=10)
        ttk.Button(user_actions_frame, text="Agregar Usuario", command=self.agregar_usuario).pack(side="left", padx=(0,5))
        ttk.Button(user_actions_frame, text="Modificar Contraseña", command=self.modificar_usuario).pack(side="left", padx=5)
        ttk.Button(user_actions_frame, text="Eliminar Usuario", command=self.eliminar_usuario).pack(side="right")

        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.permisos_frame = ttk.LabelFrame(self.right_frame, text="Permisos para el Usuario")
        self.permisos_frame.pack(fill="both", expand=True)
        
        self.permisos_vars = {}
        
        self.cargar_usuarios()

    def cargar_usuarios(self):
        for row in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(row)
        
        usuarios = usuarios_db.obtener_todos_los_usuarios()
        for usuario in usuarios:
            self.tree_usuarios.insert("", "end", values=usuario)
        self.mostrar_permisos_usuario() # Limpia el panel de permisos

    def mostrar_permisos_usuario(self, event=None):
        for widget in self.permisos_frame.winfo_children():
            widget.destroy()

        selected_item = self.tree_usuarios.focus()
        if not selected_item:
            return

        values = self.tree_usuarios.item(selected_item, "values")
        usuario_id, nombre_usuario, rol = values

        if rol == 'admin':
            ttk.Label(self.permisos_frame, text=f"El usuario '{nombre_usuario}' es administrador.\nTiene acceso a todos los módulos.",
                      font=("Helvetica", 10, "italic")).pack(padx=20, pady=20)
            return

        permisos_actuales = usuarios_db.obtener_permisos_usuario(usuario_id)
        
        self.permisos_vars = {}
        for modulo in self.MODULOS:
            var = tk.BooleanVar(value=modulo in permisos_actuales)
            chk = ttk.Checkbutton(self.permisos_frame, text=modulo, variable=var)
            chk.pack(anchor="w", padx=20, pady=2)
            self.permisos_vars[modulo] = var
        
        ttk.Button(self.permisos_frame, text="Guardar Permisos", command=lambda: self.guardar_permisos(usuario_id)).pack(pady=20)

    def guardar_permisos(self, usuario_id):
        permisos_a_guardar = {modulo: var.get() for modulo, var in self.permisos_vars.items()}
        resultado = usuarios_db.guardar_permisos_usuario(usuario_id, permisos_a_guardar)

        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
        else:
            messagebox.showerror("Error", resultado, parent=self)

    def agregar_usuario(self):
        VentanaUsuario(self, callback_exito=self.cargar_usuarios)

    def modificar_usuario(self):
        selected_item = self.tree_usuarios.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Seleccione un usuario para modificar.", parent=self)
            return
        
        values = self.tree_usuarios.item(selected_item, "values")
        usuario_id = values[0]
        
        ventana = VentanaUsuario(self, callback_exito=self.cargar_usuarios, usuario_id=usuario_id)
        # Pre-llenamos los datos para el modo edición
        ventana.user_entry.insert(0, values[1])
        ventana.rol_combo.set(values[2])

    def eliminar_usuario(self):
        selected_item = self.tree_usuarios.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Seleccione un usuario para eliminar.", parent=self)
            return

        values = self.tree_usuarios.item(selected_item, "values")
        usuario_id, nombre_usuario, rol = values

        if rol == 'admin':
            messagebox.showerror("Acción no permitida", "No se puede eliminar al usuario administrador.", parent=self)
            return
            
        if messagebox.askyesno("Confirmar", f"¿Está seguro de que desea eliminar al usuario '{nombre_usuario}'?"):
            resultado = usuarios_db.eliminar_usuario(usuario_id)
            messagebox.showinfo("Resultado", resultado, parent=self)
            self.cargar_usuarios()

class VentanaUsuario(tk.Toplevel):
    def __init__(self, parent, callback_exito, usuario_id=None):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback_exito
        self.usuario_id = usuario_id

        titulo = "Modificar Contraseña" if self.usuario_id else "Agregar Nuevo Usuario"
        self.title(titulo)
        self.geometry("400x250")
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding="10")
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        # Campos del formulario
        ttk.Label(frame, text="Nombre de Usuario:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.user_entry = ttk.Entry(frame)
        self.user_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(frame, text="Contraseña:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.pass_entry = ttk.Entry(frame, show="*")
        self.pass_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(frame, text="Rol:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.rol_combo = ttk.Combobox(frame, values=["vendedor", "admin"], state="readonly")
        self.rol_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        if self.usuario_id: # Modo edición
            self.user_entry.config(state="disabled")
            self.rol_combo.config(state="disabled")
        else: # Modo creación
            self.rol_combo.set("vendedor")

        btn_guardar = ttk.Button(frame, text="Guardar", command=self.guardar)
        btn_guardar.grid(row=3, column=0, columnspan=2, pady=20, sticky="ew")

        self.user_entry.focus_set()

    def guardar(self):
        nombre_usuario = self.user_entry.get()
        clave = self.pass_entry.get()
        rol = self.rol_combo.get()

        if not nombre_usuario or not clave or not rol:
            messagebox.showwarning("Datos Incompletos", "Todos los campos son obligatorios.", parent=self)
            return

        if self.usuario_id:
            # Lógica para modificar contraseña (la añadiremos a usuarios_db.py)
            resultado = usuarios_db.modificar_clave_usuario(self.usuario_id, clave)
        else:
            resultado = usuarios_db.crear_usuario(nombre_usuario, clave, rol)

        if "exitosamente" in resultado:
            messagebox.showinfo("Éxito", resultado, parent=self)
            self.callback() # Llama a la función para refrescar la lista
            self.destroy()
        else:
            messagebox.showerror("Error", resultado, parent=self)
