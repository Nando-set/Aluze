"""
Panel del catálogo.
Layout: árbol de categorías/modelos (izq) + editor de modelo (der).
Fase 2.3.B: con subida de imágenes y video.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from config import CARPETA_CATALOGO, BASE_DIR
from core.catalogo_datos import (
    leer_categorias, leer_modelos,
    agregar_modelo, actualizar_modelo, eliminar_modelo,
    buscar_modelo, guardar_imagenes_modelo, guardar_imagen_linea,
    obtener_carpeta_imagenes_modelo
)
from core.imagenes import procesar_imagen


# Paleta de colores (coherente con el resto de la app)
COLOR_FONDO = "#0f172a"
COLOR_PANEL = "#1e293b"
COLOR_INPUT = "#334155"
COLOR_TEXTO = "#f8fafc"
COLOR_TEXTO_SEC = "#94a3b8"
COLOR_ROSA = "#973359"
COLOR_AZUL = "#0ea5e9"
COLOR_VERDE = "#16a34a"
COLOR_ROJO = "#ef4444"
COLOR_AMARILLO = "#fbbf24"

# Líneas típicas predefinidas
LINEAS_TIPICAS = ["Basic", "Intermedio", "Blackout"]

# Máximo de fotos por modelo
MAX_FOTOS = 3


def construir_panel_catalogo(app):
    """
    Construye el panel del catálogo dentro de `app.vista_catalogo`.
    """
    for w in app.vista_catalogo.winfo_children():
        w.destroy()

    # ============================================================
    # CONTENEDOR PRINCIPAL (2 columnas)
    # ============================================================
    panel_izq = tk.Frame(app.vista_catalogo, bg=COLOR_PANEL, width=320, padx=10, pady=10)
    panel_izq.pack(side=tk.LEFT, fill=tk.Y)
    panel_izq.pack_propagate(False)

    panel_der = tk.Frame(app.vista_catalogo, bg=COLOR_FONDO, padx=15, pady=10)
    panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # ============================================================
    # ÁRBOL DE CATEGORÍAS / MODELOS
    # ============================================================
    tk.Label(panel_izq, text="CATEGORÍAS", bg=COLOR_PANEL, fg=COLOR_TEXTO,
             font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Cat.Treeview",
                    background=COLOR_PANEL, foreground=COLOR_TEXTO,
                    fieldbackground=COLOR_PANEL, font=("Segoe UI", 10),
                    rowheight=26, borderwidth=0)
    style.map("Cat.Treeview",
              background=[("selected", COLOR_ROSA)],
              foreground=[("selected", "#ffffff")])

    contenedor_arbol = tk.Frame(panel_izq, bg=COLOR_PANEL)
    contenedor_arbol.pack(fill=tk.BOTH, expand=True)

    scroll_arbol = ttk.Scrollbar(contenedor_arbol, orient="vertical")
    app.arbol_catalogo = ttk.Treeview(contenedor_arbol, style="Cat.Treeview",
                                       show="tree", yscrollcommand=scroll_arbol.set)
    scroll_arbol.config(command=app.arbol_catalogo.yview)
    app.arbol_catalogo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll_arbol.pack(side=tk.RIGHT, fill=tk.Y)

    app.arbol_catalogo.bind("<<TreeviewSelect>>", lambda e: _al_seleccionar_arbol(app))

    frame_botones_arbol = tk.Frame(panel_izq, bg=COLOR_PANEL)
    frame_botones_arbol.pack(fill=tk.X, pady=(10, 0))
    _crear_boton(frame_botones_arbol, "➕  Nuevo modelo", COLOR_VERDE,
                 app.nuevo_modelo_catalogo).pack(fill=tk.X, pady=(0, 4))
    _crear_boton(frame_botones_arbol, "🌐  Generar catálogo", COLOR_AZUL,
                 app.accion_generar_catalogo).pack(fill=tk.X, pady=(0, 4))
    _crear_boton(frame_botones_arbol, "👁️  Ver catálogo", COLOR_ROSA,
                 app.accion_ver_catalogo).pack(fill=tk.X)

    # ============================================================
    # EDITOR DE MODELO (columna derecha)
    # ============================================================
    tk.Label(panel_der, text="EDITOR DEL MODELO", bg=COLOR_FONDO, fg=COLOR_TEXTO,
             font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))

    canvas_editor = tk.Canvas(panel_der, bg=COLOR_FONDO, highlightthickness=0, bd=0)
    scroll_editor = ttk.Scrollbar(panel_der, orient="vertical", command=canvas_editor.yview)
    frame_editor = tk.Frame(canvas_editor, bg=COLOR_FONDO)
    frame_editor.bind("<Configure>",
                      lambda e: canvas_editor.configure(scrollregion=canvas_editor.bbox("all")))
    canvas_editor.create_window((0, 0), window=frame_editor, anchor="nw")
    canvas_editor.configure(yscrollcommand=scroll_editor.set)
    canvas_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll_editor.pack(side=tk.RIGHT, fill=tk.Y)

    app.editor_frame_catalogo = frame_editor

    # --- Campos del editor ---
    tk.Label(frame_editor, text="Nombre del modelo", bg=COLOR_FONDO, fg=COLOR_TEXTO_SEC,
             font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 2))

    app.var_nombre = tk.StringVar()
    tk.Entry(frame_editor, textvariable=app.var_nombre, font=("Segoe UI", 11),
             bg=COLOR_INPUT, fg=COLOR_TEXTO, insertbackground="white",
             relief=tk.FLAT, borderwidth=0).pack(fill=tk.X, ipady=6)

    tk.Label(frame_editor, text="Categoría", bg=COLOR_FONDO, fg=COLOR_TEXTO_SEC,
             font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(12, 2))

    app.var_categoria = tk.StringVar()
    app.combo_categoria = ttk.Combobox(frame_editor, textvariable=app.var_categoria,
                                        state="readonly", font=("Segoe UI", 10))
    app.combo_categoria.pack(fill=tk.X, ipady=4)

    tk.Label(frame_editor, text="Descripción breve", bg=COLOR_FONDO, fg=COLOR_TEXTO_SEC,
             font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(12, 2))

    app.text_descripcion = tk.Text(frame_editor, height=3, font=("Segoe UI", 10),
                                    bg=COLOR_INPUT, fg=COLOR_TEXTO,
                                    insertbackground="white", relief=tk.FLAT, borderwidth=0)
    app.text_descripcion.pack(fill=tk.X)

    # --- Sección FOTOS DEL MODELO ---
    tk.Frame(frame_editor, bg=COLOR_INPUT, height=1).pack(fill=tk.X, pady=(20, 0))

    frame_fotos_header = tk.Frame(frame_editor, bg=COLOR_FONDO)
    frame_fotos_header.pack(fill=tk.X, pady=(12, 6))

    tk.Label(frame_fotos_header, text=f"FOTOS DEL MODELO (máx {MAX_FOTOS})",
             bg=COLOR_FONDO, fg=COLOR_TEXTO, font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)

    app.btn_add_foto = tk.Button(frame_fotos_header, text="📷  Subir fotos",
                                  bg=COLOR_AZUL, fg="white",
                                  font=("Segoe UI", 9, "bold"),
                                  relief=tk.FLAT, cursor="hand2",
                                  borderwidth=0, highlightthickness=0,
                                  command=lambda: app.subir_fotos_modelo())
    app.btn_add_foto.pack(side=tk.RIGHT)

    # Contenedor donde se dibujan las fotos
    app.fotos_frame = tk.Frame(frame_editor, bg=COLOR_FONDO)
    app.fotos_frame.pack(fill=tk.X)

    # --- Sección VIDEO ---
    tk.Frame(frame_editor, bg=COLOR_INPUT, height=1).pack(fill=tk.X, pady=(20, 0))

    frame_video_header = tk.Frame(frame_editor, bg=COLOR_FONDO)
    frame_video_header.pack(fill=tk.X, pady=(12, 6))

    tk.Label(frame_video_header, text="VIDEO DEL MODELO",
             bg=COLOR_FONDO, fg=COLOR_TEXTO, font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)

    app.btn_add_video = tk.Button(frame_video_header, text="🎥  Subir video",
                                   bg=COLOR_AZUL, fg="white",
                                   font=("Segoe UI", 9, "bold"),
                                   relief=tk.FLAT, cursor="hand2",
                                   borderwidth=0, highlightthickness=0,
                                   command=lambda: app.subir_video_modelo())
    app.btn_add_video.pack(side=tk.RIGHT)

    app.video_frame = tk.Frame(frame_editor, bg=COLOR_FONDO)
    app.video_frame.pack(fill=tk.X)

    # --- Sección LÍNEAS ---
    tk.Frame(frame_editor, bg=COLOR_INPUT, height=1).pack(fill=tk.X, pady=(20, 0))

    frame_lineas_header = tk.Frame(frame_editor, bg=COLOR_FONDO)
    frame_lineas_header.pack(fill=tk.X, pady=(12, 6))

    tk.Label(frame_lineas_header, text="LÍNEAS DISPONIBLES",
             bg=COLOR_FONDO, fg=COLOR_TEXTO, font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)

    app.lineas_frame = tk.Frame(frame_editor, bg=COLOR_FONDO)
    app.lineas_frame.pack(fill=tk.X)

    app.btn_add_linea = tk.Button(frame_lineas_header, text="➕  Añadir línea",
                                   bg=COLOR_VERDE, fg="white",
                                   font=("Segoe UI", 9, "bold"),
                                   relief=tk.FLAT, cursor="hand2",
                                   borderwidth=0, highlightthickness=0,
                                   command=lambda: _menu_add_linea(app))
    app.btn_add_linea.pack(side=tk.RIGHT)

    # --- Botones inferiores ---
    frame_botones_editor = tk.Frame(frame_editor, bg=COLOR_FONDO)
    frame_botones_editor.pack(fill=tk.X, pady=(20, 0))

    _crear_boton(frame_botones_editor, "💾  Guardar modelo", COLOR_ROSA,
                 app.guardar_modelo_catalogo).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
    _crear_boton(frame_botones_editor, "🗑️  Eliminar", COLOR_ROJO,
                 app.eliminar_modelo_catalogo).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

    # --- Rellenar combobox categorías ---
    categorias = leer_categorias()
    app.combo_categoria["values"] = [f"{c['emoji']} {c['nombre']}" for c in categorias]
    app.categorias_cache = categorias

    # --- Cargar árbol ---
    app.modelo_seleccionado_id = None
    app.refrescar_arbol_catalogo()
    _limpiar_editor(app)


# ============================================================
# FUNCIONES DE SOPORTE
# ============================================================
def _crear_boton(parent, texto, color, comando):
    return tk.Button(parent, text=texto, bg=color, fg="white",
                     font=("Segoe UI", 10, "bold"),
                     relief=tk.FLAT, cursor="hand2",
                     activebackground=color, activeforeground="white",
                     borderwidth=0, highlightthickness=0,
                     command=comando)


def _menu_add_linea(app):
    if not app.modelo_seleccionado_id:
        messagebox.showwarning("Aviso",
                                "Primero guarda el modelo antes de añadir líneas.")
        return

    menu = tk.Menu(app.root, tearoff=0, bg=COLOR_PANEL, fg=COLOR_TEXTO,
                   activebackground=COLOR_ROSA, activeforeground="white",
                   font=("Segoe UI", 10))
    for nombre in LINEAS_TIPICAS:
        menu.add_command(label=nombre,
                         command=lambda n=nombre: app.agregar_linea_modelo(n))
    menu.add_separator()
    menu.add_command(label="Personalizada...", command=lambda: _linea_personalizada(app))

    x = app.btn_add_linea.winfo_rootx()
    y = app.btn_add_linea.winfo_rooty() + app.btn_add_linea.winfo_height()
    menu.tk_popup(x, y)


def _linea_personalizada(app):
    from tkinter import simpledialog
    nombre = simpledialog.askstring("Nueva línea",
                                     "Nombre de la línea:",
                                     parent=app.root)
    if nombre and nombre.strip():
        app.agregar_linea_modelo(nombre.strip())


def _al_seleccionar_arbol(app):
    seleccion = app.arbol_catalogo.selection()
    if not seleccion:
        return
    item_id = seleccion[0]
    if item_id.startswith("cat_"):
        return
    if item_id.startswith("mod_"):
        id_modelo = item_id[4:]
        modelo = buscar_modelo(id_modelo)
        if modelo:
            app.modelo_seleccionado_id = id_modelo
            _cargar_modelo_en_editor(app, modelo)


def _cargar_modelo_en_editor(app, modelo):
    """Rellena el editor con los datos del modelo."""
    app.var_nombre.set(modelo.get("nombre", ""))

    cat_id = modelo.get("categoria", "")
    for c in app.categorias_cache:
        if c["id"] == cat_id:
            app.var_categoria.set(f"{c['emoji']} {c['nombre']}")
            break

    app.text_descripcion.delete("1.0", tk.END)
    app.text_descripcion.insert("1.0", modelo.get("descripcion", ""))

    _renderizar_fotos(app, modelo.get("imagenes", []))
    _renderizar_video(app, modelo.get("video"))
    _renderizar_lineas(app, modelo.get("lineas", []))


def _renderizar_fotos(app, fotos):
    """Dibuja las fotos del modelo en el editor."""
    for w in app.fotos_frame.winfo_children():
        w.destroy()

    if not fotos:
        tk.Label(app.fotos_frame,
                 text="Sin fotos. Pulsa 'Subir fotos' para empezar.",
                 bg=COLOR_FONDO, fg=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=6)
        return

    row = tk.Frame(app.fotos_frame, bg=COLOR_FONDO)
    row.pack(anchor="w")

    for i, ruta in enumerate(fotos):
        _crear_tarjeta_foto(app, row, i, ruta)


def _crear_tarjeta_foto(app, parent, indice, ruta_relativa):
    """Dibuja una miniatura de foto con botón eliminar."""
    card = tk.Frame(parent, bg=COLOR_PANEL, padx=4, pady=4)
    card.pack(side=tk.LEFT, padx=4)

    # Cargar la miniatura si existe
    ruta_completa = BASE_DIR / ruta_relativa
    try:
        from PIL import Image, ImageTk
        img = Image.open(ruta_completa)
        img.thumbnail((100, 100), Image.LANCZOS)
        foto_tk = ImageTk.PhotoImage(img)
        label = tk.Label(card, image=foto_tk, bg=COLOR_PANEL)
        label.image = foto_tk  # evita garbage collection
        label.pack()
    except Exception:
        tk.Label(card, text="📷", bg=COLOR_PANEL, fg=COLOR_TEXTO,
                 font=("Segoe UI", 30)).pack()

    # Botón × para eliminar
    tk.Button(card, text="×", bg=COLOR_ROJO, fg="white",
              font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2",
              borderwidth=0, highlightthickness=0, width=2,
              command=lambda i=indice: app.eliminar_foto_modelo(i)).pack(pady=(2, 0))


def _renderizar_video(app, video_ruta):
    """Dibuja el estado del video en el editor."""
    for w in app.video_frame.winfo_children():
        w.destroy()

    if not video_ruta:
        tk.Label(app.video_frame,
                 text="Sin video. Pulsa 'Subir video' para empezar.",
                 bg=COLOR_FONDO, fg=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=6)
        return

    # Contenedor del video cargado
    card = tk.Frame(app.video_frame, bg=COLOR_PANEL, padx=10, pady=8)
    card.pack(fill=tk.X, pady=4)

    # Icono + nombre del archivo
    row = tk.Frame(card, bg=COLOR_PANEL)
    row.pack(fill=tk.X)

    tk.Label(row, text="🎥", bg=COLOR_PANEL, fg=COLOR_VERDE,
             font=("Segoe UI", 20)).pack(side=tk.LEFT, padx=(0, 8))

    info_frame = tk.Frame(row, bg=COLOR_PANEL)
    info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

    tk.Label(info_frame, text="Video cargado",
             bg=COLOR_PANEL, fg=COLOR_TEXTO,
             font=("Segoe UI", 9, "bold")).pack(anchor="w")

    tk.Label(info_frame, text=video_ruta.split("/")[-1],
             bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC,
             font=("Segoe UI", 8)).pack(anchor="w")

    # Botón eliminar
    tk.Button(row, text="🗑️", bg=COLOR_ROJO, fg="white",
              font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
              borderwidth=0, highlightthickness=0,
              command=lambda: app.eliminar_video_modelo()).pack(side=tk.RIGHT)


def _renderizar_lineas(app, lineas):
    """Dibuja las tarjetas de líneas en el editor."""
    for w in app.lineas_frame.winfo_children():
        w.destroy()

    if not lineas:
        tk.Label(app.lineas_frame,
                 text="Sin líneas. Pulsa 'Añadir línea' para empezar.",
                 bg=COLOR_FONDO, fg=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=6)
        return

    for i, linea in enumerate(lineas):
        _crear_tarjeta_linea(app, i, linea, len(lineas))


def _crear_tarjeta_linea(app, indice, linea, total):
    """Dibuja una tarjeta para una línea."""
    card = tk.Frame(app.lineas_frame, bg=COLOR_PANEL, padx=10, pady=8)
    card.pack(fill=tk.X, pady=4)

    # Header: nombre + botones
    header = tk.Frame(card, bg=COLOR_PANEL)
    header.pack(fill=tk.X)

    tk.Label(header, text=f"● {linea.get('nombre', 'Sin nombre')}",
             bg=COLOR_PANEL, fg=COLOR_TEXTO,
             font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

    tk.Button(header, text="🗑️", bg=COLOR_ROJO, fg="white",
              font=("Segoe UI", 8), relief=tk.FLAT, cursor="hand2",
              borderwidth=0, highlightthickness=0,
              command=lambda i=indice: app.eliminar_linea_modelo(i)).pack(side=tk.RIGHT, padx=(2, 0))

    if indice < total - 1:
        tk.Button(header, text="↓", bg=COLOR_INPUT, fg=COLOR_TEXTO,
                  font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2",
                  borderwidth=0, highlightthickness=0, width=2,
                  command=lambda i=indice: app.mover_linea(i, 1)).pack(side=tk.RIGHT, padx=(2, 0))

    if indice > 0:
        tk.Button(header, text="↑", bg=COLOR_INPUT, fg=COLOR_TEXTO,
                  font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2",
                  borderwidth=0, highlightthickness=0, width=2,
                  command=lambda i=indice: app.mover_linea(i, -1)).pack(side=tk.RIGHT, padx=(2, 0))

    # --- Imagen de la línea ---
    tk.Label(card, text="Imagen de la línea:", bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC,
             font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(8, 2))

    frame_img_linea = tk.Frame(card, bg=COLOR_PANEL)
    frame_img_linea.pack(fill=tk.X)

    ruta_img = linea.get("imagen")
    if ruta_img:
        ruta_completa = BASE_DIR / ruta_img
        try:
            from PIL import Image, ImageTk
            img = Image.open(ruta_completa)
            img.thumbnail((80, 80), Image.LANCZOS)
            foto_tk = ImageTk.PhotoImage(img)
            lbl_img = tk.Label(frame_img_linea, image=foto_tk, bg=COLOR_PANEL)
            lbl_img.image = foto_tk
            lbl_img.pack(side=tk.LEFT, padx=(0, 6))
        except Exception:
            tk.Label(frame_img_linea, text="📷", bg=COLOR_PANEL,
                     fg=COLOR_TEXTO_SEC, font=("Segoe UI", 20)).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(frame_img_linea, text="✕ Quitar", bg=COLOR_ROJO, fg="white",
                  font=("Segoe UI", 8), relief=tk.FLAT, cursor="hand2",
                  borderwidth=0, highlightthickness=0,
                  command=lambda i=indice: app.eliminar_imagen_linea(i)).pack(side=tk.LEFT, padx=(0, 6))
    else:
        tk.Button(frame_img_linea, text="📷  Subir imagen",
                  bg=COLOR_AZUL, fg="white", font=("Segoe UI", 8, "bold"),
                  relief=tk.FLAT, cursor="hand2", borderwidth=0, highlightthickness=0,
                  command=lambda i=indice: app.subir_imagen_linea(i)).pack(side=tk.LEFT)

    # --- Descripción de la línea ---
    tk.Label(card, text="Descripción:", bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC,
             font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(8, 2))

    texto_desc = tk.Text(card, height=2, font=("Segoe UI", 9),
                         bg=COLOR_INPUT, fg=COLOR_TEXTO,
                         insertbackground="white", relief=tk.FLAT, borderwidth=0)
    texto_desc.pack(fill=tk.X)
    texto_desc.insert("1.0", linea.get("descripcion", ""))
    texto_desc.bind("<FocusOut>",
                    lambda e, i=indice, t=texto_desc: app.editar_descripcion_linea(
                        i, t.get("1.0", tk.END).strip()))

    # --- Colores ---
    frame_colores = tk.Frame(card, bg=COLOR_PANEL)
    frame_colores.pack(fill=tk.X, pady=(8, 0))

    tk.Label(frame_colores, text="Colores:", bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC,
             font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)

    tk.Button(frame_colores, text="+ Añadir color",
              bg=COLOR_AZUL, fg="white", font=("Segoe UI", 8, "bold"),
              relief=tk.FLAT, cursor="hand2", borderwidth=0, highlightthickness=0,
              command=lambda i=indice: app.agregar_color_linea(i)).pack(side=tk.RIGHT)

    colores = linea.get("colores", [])
    if colores:
        chips_frame = tk.Frame(card, bg=COLOR_PANEL)
        chips_frame.pack(fill=tk.X, pady=(4, 0))
        for j, col in enumerate(colores):
            _crear_chip_color(app, chips_frame, indice, j, col)


def _crear_chip_color(app, parent, indice_linea, indice_color, color):
    chip = tk.Frame(parent, bg=COLOR_INPUT, padx=6, pady=3)
    chip.pack(side=tk.LEFT, padx=(0, 4), pady=2)

    canvas = tk.Canvas(chip, width=16, height=16, bg=COLOR_INPUT,
                       highlightthickness=0, bd=0)
    canvas.pack(side=tk.LEFT)
    canvas.create_oval(1, 1, 15, 15, fill=color.get("hex", "#FFFFFF"),
                       outline="#64748b", width=1)

    tk.Label(chip, text=color.get("nombre", ""), bg=COLOR_INPUT, fg=COLOR_TEXTO,
             font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(4, 6))

    tk.Button(chip, text="×", bg=COLOR_INPUT, fg="#f87171",
              font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
              borderwidth=0, highlightthickness=0,
              command=lambda i=indice_linea, j=indice_color: app.eliminar_color_linea(i, j)
              ).pack(side=tk.LEFT)


def _limpiar_editor(app):
    app.modelo_seleccionado_id = None
    app.var_nombre.set("")
    app.var_categoria.set("")
    app.text_descripcion.delete("1.0", tk.END)
    _renderizar_fotos(app, [])
    _renderizar_video(app, None)
    _renderizar_lineas(app, [])


# ============================================================
# ACCIONES DEL PANEL
# ============================================================
def refrescar_arbol(app):
    arbol = app.arbol_catalogo
    for item in arbol.get_children():
        arbol.delete(item)

    categorias = leer_categorias()
    modelos = leer_modelos()

    for cat in categorias:
        cat_item = arbol.insert("", "end",
                                iid=f"cat_{cat['id']}",
                                text=f"  {cat['emoji']}  {cat['nombre']}",
                                open=True)
        for m in modelos:
            if m.get("categoria") == cat["id"]:
                arbol.insert(cat_item, "end",
                             iid=f"mod_{m['id']}",
                             text=f"    ●  {m['nombre']}")