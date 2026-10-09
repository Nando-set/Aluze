"""
Panel del catálogo.
Layout: árbol de categorías/modelos (izq) + editor de modelo (der).
Migrado a customtkinter.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import customtkinter as ctk

from config import CARPETA_CATALOGO, BASE_DIR
from core.catalogo_datos import (
    leer_categorias, leer_modelos,
    agregar_modelo, actualizar_modelo, eliminar_modelo,
    buscar_modelo, guardar_imagenes_modelo, guardar_imagen_linea,
    obtener_carpeta_imagenes_modelo
)
from core.imagenes import procesar_imagen


# ============================================================
# COLORES (coherentes con customtkinter tema dark-blue)
# ============================================================
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

# Botones estilo IA
BTN_FG = "#f8fafc"
BTN_TXT = "#334155"
BTN_HOVER = "#e2e8f0"

BTN_PELIGRO_FG = "#f1f5f9"
BTN_PELIGRO_TXT = "#b91c1c"
BTN_PELIGRO_HOVER = "#fee2e2"

# Líneas típicas
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
    panel_izq = ctk.CTkFrame(app.vista_catalogo, fg_color=COLOR_PANEL,
                              width=320, corner_radius=0)
    panel_izq.pack(side=tk.LEFT, fill=tk.Y)
    panel_izq.pack_propagate(False)

    panel_der = ctk.CTkFrame(app.vista_catalogo, fg_color=COLOR_FONDO,
                              corner_radius=0)
    panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # ============================================================
    # ÁRBOL DE CATEGORÍAS / MODELOS
    # ============================================================
    ctk.CTkLabel(panel_izq, text="CATEGORÍAS",
                 text_color=COLOR_TEXTO,
                 font=("Segoe UI", 12, "bold"),
                 anchor="w").pack(fill=tk.X, padx=12, pady=(12, 8))

    # Treeview (customtkinter no tiene, seguimos con ttk estilizado)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Cat.Treeview",
                    background=COLOR_PANEL, foreground=COLOR_TEXTO,
                    fieldbackground=COLOR_PANEL, font=("Segoe UI", 10),
                    rowheight=28, borderwidth=0)
    style.map("Cat.Treeview",
              background=[("selected", COLOR_ROSA)],
              foreground=[("selected", "#ffffff")])

    contenedor_arbol = ctk.CTkFrame(panel_izq, fg_color=COLOR_PANEL, corner_radius=0)
    contenedor_arbol.pack(fill=tk.BOTH, expand=True, padx=10)

    scroll_arbol = ttk.Scrollbar(contenedor_arbol, orient="vertical")
    app.arbol_catalogo = ttk.Treeview(contenedor_arbol, style="Cat.Treeview",
                                       show="tree", yscrollcommand=scroll_arbol.set)
    scroll_arbol.config(command=app.arbol_catalogo.yview)
    app.arbol_catalogo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll_arbol.pack(side=tk.RIGHT, fill=tk.Y)

    app.arbol_catalogo.bind("<<TreeviewSelect>>", lambda e: _al_seleccionar_arbol(app))

    # Botones del panel izquierdo (estilo IA)
    frame_botones_arbol = ctk.CTkFrame(panel_izq, fg_color=COLOR_PANEL, corner_radius=0)
    frame_botones_arbol.pack(fill=tk.X, padx=10, pady=(10, 12))

    ctk.CTkButton(frame_botones_arbol, text="➕  Nuevo modelo",
                  command=app.nuevo_modelo_catalogo,
                  fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                  corner_radius=10, height=34,
                  font=("Segoe UI", 10, "bold")).pack(fill=tk.X, pady=(0, 4))

    ctk.CTkButton(frame_botones_arbol, text="🌐  Generar catálogo",
                  command=app.accion_generar_catalogo,
                  fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                  corner_radius=10, height=34,
                  font=("Segoe UI", 10, "bold")).pack(fill=tk.X, pady=(0, 4))

    ctk.CTkButton(frame_botones_arbol, text="👁️  Ver catálogo",
                  command=app.accion_ver_catalogo,
                  fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                  corner_radius=10, height=34,
                  font=("Segoe UI", 10, "bold")).pack(fill=tk.X)

    # ============================================================
    # EDITOR DE MODELO (columna derecha)
    # ============================================================
    ctk.CTkLabel(panel_der, text="EDITOR DEL MODELO",
                 text_color=COLOR_TEXTO,
                 font=("Segoe UI", 15, "bold"),
                 anchor="w").pack(fill=tk.X, padx=15, pady=(12, 8))

    # ScrollableFrame nativo
    app.editor_frame_catalogo = ctk.CTkScrollableFrame(
        panel_der,
        fg_color=COLOR_FONDO,
        corner_radius=0,
        scrollbar_button_color=COLOR_INPUT,
        scrollbar_button_hover_color="#475569",
    )
    app.editor_frame_catalogo.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    frame_editor = app.editor_frame_catalogo

    # --- Campos del editor ---
    ctk.CTkLabel(frame_editor, text="Nombre del modelo",
                 text_color=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill=tk.X, pady=(6, 3))

    app.var_nombre = tk.StringVar()
    ctk.CTkEntry(frame_editor, textvariable=app.var_nombre,
                 font=("Segoe UI", 11),
                 fg_color=COLOR_INPUT, text_color=COLOR_TEXTO,
                 border_width=0, corner_radius=8, height=36).pack(fill=tk.X)

    ctk.CTkLabel(frame_editor, text="Categoría",
                 text_color=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill=tk.X, pady=(12, 3))

    app.var_categoria = tk.StringVar()
    app.combo_categoria = ctk.CTkComboBox(
        frame_editor,
        variable=app.var_categoria,
        values=[],
        state="readonly",
        font=("Segoe UI", 11),
        fg_color=COLOR_INPUT,
        button_color=COLOR_INPUT,
        button_hover_color="#475569",
        text_color=COLOR_TEXTO,
        border_width=0,
        corner_radius=8,
        height=36,
        dropdown_fg_color=COLOR_PANEL,
        dropdown_text_color=COLOR_TEXTO,
        dropdown_hover_color=COLOR_ROSA,
    )
    app.combo_categoria.pack(fill=tk.X)

    ctk.CTkLabel(frame_editor, text="Descripción breve",
                 text_color=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill=tk.X, pady=(12, 3))

    app.text_descripcion = ctk.CTkTextbox(
        frame_editor,
        height=70,
        font=("Segoe UI", 11),
        fg_color=COLOR_INPUT, text_color=COLOR_TEXTO,
        border_width=0, corner_radius=8,
    )
    app.text_descripcion.pack(fill=tk.X)

    # --- Sección FOTOS ---
    _separador(frame_editor)
    frame_fotos_header = ctk.CTkFrame(frame_editor, fg_color=COLOR_FONDO, corner_radius=0)
    frame_fotos_header.pack(fill=tk.X, pady=(10, 6))

    ctk.CTkLabel(frame_fotos_header, text=f"FOTOS DEL MODELO (máx {MAX_FOTOS})",
                 text_color=COLOR_TEXTO, font=("Segoe UI", 12, "bold"),
                 anchor="w").pack(side=tk.LEFT)

    app.btn_add_foto = ctk.CTkButton(
        frame_fotos_header,
        text="📷  Subir fotos",
        command=lambda: app.subir_fotos_modelo(),
        fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
        corner_radius=10, height=32, width=130,
        font=("Segoe UI", 10, "bold"),
    )
    app.btn_add_foto.pack(side=tk.RIGHT)

    app.fotos_frame = ctk.CTkFrame(frame_editor, fg_color=COLOR_FONDO, corner_radius=0)
    app.fotos_frame.pack(fill=tk.X)

    # --- Sección VIDEO ---
    _separador(frame_editor)
    frame_video_header = ctk.CTkFrame(frame_editor, fg_color=COLOR_FONDO, corner_radius=0)
    frame_video_header.pack(fill=tk.X, pady=(10, 6))

    ctk.CTkLabel(frame_video_header, text="VIDEO DEL MODELO",
                 text_color=COLOR_TEXTO, font=("Segoe UI", 12, "bold"),
                 anchor="w").pack(side=tk.LEFT)

    app.btn_add_video = ctk.CTkButton(
        frame_video_header,
        text="🎥  Subir video",
        command=lambda: app.subir_video_modelo(),
        fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
        corner_radius=10, height=32, width=130,
        font=("Segoe UI", 10, "bold"),
    )
    app.btn_add_video.pack(side=tk.RIGHT)

    app.video_frame = ctk.CTkFrame(frame_editor, fg_color=COLOR_FONDO, corner_radius=0)
    app.video_frame.pack(fill=tk.X)

    # --- Sección LÍNEAS ---
    _separador(frame_editor)
    frame_lineas_header = ctk.CTkFrame(frame_editor, fg_color=COLOR_FONDO, corner_radius=0)
    frame_lineas_header.pack(fill=tk.X, pady=(10, 6))

    ctk.CTkLabel(frame_lineas_header, text="LÍNEAS DISPONIBLES",
                 text_color=COLOR_TEXTO, font=("Segoe UI", 12, "bold"),
                 anchor="w").pack(side=tk.LEFT)

    app.btn_add_linea = ctk.CTkButton(
        frame_lineas_header,
        text="➕  Añadir línea",
        command=lambda: _menu_add_linea(app),
        fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
        corner_radius=10, height=32, width=130,
        font=("Segoe UI", 10, "bold"),
    )
    app.btn_add_linea.pack(side=tk.RIGHT)

    app.lineas_frame = ctk.CTkFrame(frame_editor, fg_color=COLOR_FONDO, corner_radius=0)
    app.lineas_frame.pack(fill=tk.X)

    # --- Botones inferiores ---
    frame_botones_editor = ctk.CTkFrame(frame_editor, fg_color=COLOR_FONDO, corner_radius=0)
    frame_botones_editor.pack(fill=tk.X, pady=(20, 10))

    ctk.CTkButton(frame_botones_editor, text="💾  Guardar modelo",
                  command=app.guardar_modelo_catalogo,
                  fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                  corner_radius=12, height=42,
                  font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

    ctk.CTkButton(frame_botones_editor, text="🗑️  Eliminar",
                  command=app.eliminar_modelo_catalogo,
                  fg_color=BTN_PELIGRO_FG, text_color=BTN_PELIGRO_TXT,
                  hover_color=BTN_PELIGRO_HOVER,
                  corner_radius=12, height=42,
                  font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

    # --- Rellenar combobox categorías ---
    categorias = leer_categorias()
    app.combo_categoria.configure(values=[f"{c['emoji']} {c['nombre']}" for c in categorias])
    app.categorias_cache = categorias

    # --- Cargar árbol ---
    app.modelo_seleccionado_id = None
    app.refrescar_arbol_catalogo()
    _limpiar_editor(app)


# ============================================================
# HELPERS
# ============================================================
def _separador(parent):
    """Línea separadora."""
    ctk.CTkFrame(parent, fg_color=COLOR_INPUT, height=1, corner_radius=0).pack(
        fill=tk.X, pady=(18, 0))


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
    for w in app.fotos_frame.winfo_children():
        w.destroy()

    if not fotos:
        ctk.CTkLabel(app.fotos_frame,
                     text="Sin fotos. Pulsa 'Subir fotos' para empezar.",
                     text_color=COLOR_TEXTO_SEC,
                     font=("Segoe UI", 10, "italic")).pack(anchor="w", pady=6)
        return

    row = ctk.CTkFrame(app.fotos_frame, fg_color=COLOR_FONDO, corner_radius=0)
    row.pack(anchor="w")

    for i, ruta in enumerate(fotos):
        _crear_tarjeta_foto(app, row, i, ruta)


def _crear_tarjeta_foto(app, parent, indice, ruta_relativa):
    card = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=10)
    card.pack(side=tk.LEFT, padx=4, pady=4)

    ruta_completa = BASE_DIR / ruta_relativa
    try:
        from PIL import Image, ImageTk
        img = Image.open(ruta_completa)
        img.thumbnail((100, 100), Image.LANCZOS)
        foto_tk = ImageTk.PhotoImage(img)
        label = tk.Label(card, image=foto_tk, bg=COLOR_PANEL)
        label.image = foto_tk
        label.pack(padx=4, pady=(4, 0))
    except Exception:
        ctk.CTkLabel(card, text="📷", text_color=COLOR_TEXTO,
                     font=("Segoe UI", 30)).pack(padx=8, pady=8)

    ctk.CTkButton(card, text="×",
                  command=lambda i=indice: app.eliminar_foto_modelo(i),
                  fg_color=BTN_PELIGRO_FG, text_color=BTN_PELIGRO_TXT,
                  hover_color=BTN_PELIGRO_HOVER,
                  corner_radius=8, width=28, height=24,
                  font=("Segoe UI", 11, "bold")).pack(pady=(2, 4))


def _renderizar_video(app, video_ruta):
    for w in app.video_frame.winfo_children():
        w.destroy()

    if not video_ruta:
        ctk.CTkLabel(app.video_frame,
                     text="Sin video. Pulsa 'Subir video' para empezar.",
                     text_color=COLOR_TEXTO_SEC,
                     font=("Segoe UI", 10, "italic")).pack(anchor="w", pady=6)
        return

    card = ctk.CTkFrame(app.video_frame, fg_color=COLOR_PANEL, corner_radius=10)
    card.pack(fill=tk.X, pady=4)

    row = ctk.CTkFrame(card, fg_color=COLOR_PANEL, corner_radius=0)
    row.pack(fill=tk.X, padx=12, pady=10)

    ctk.CTkLabel(row, text="🎥", text_color=COLOR_VERDE,
                 font=("Segoe UI", 22)).pack(side=tk.LEFT, padx=(0, 10))

    info_frame = ctk.CTkFrame(row, fg_color=COLOR_PANEL, corner_radius=0)
    info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

    ctk.CTkLabel(info_frame, text="Video cargado",
                 text_color=COLOR_TEXTO,
                 font=("Segoe UI", 11, "bold"),
                 anchor="w").pack(fill=tk.X)

    ctk.CTkLabel(info_frame, text=video_ruta.split("/")[-1],
                 text_color=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 9),
                 anchor="w").pack(fill=tk.X)

    ctk.CTkButton(row, text="🗑️",
                  command=lambda: app.eliminar_video_modelo(),
                  fg_color=BTN_PELIGRO_FG, text_color=BTN_PELIGRO_TXT,
                  hover_color=BTN_PELIGRO_HOVER,
                  corner_radius=8, width=40, height=30,
                  font=("Segoe UI", 11)).pack(side=tk.RIGHT)


def _renderizar_lineas(app, lineas):
    for w in app.lineas_frame.winfo_children():
        w.destroy()

    if not lineas:
        ctk.CTkLabel(app.lineas_frame,
                     text="Sin líneas. Pulsa 'Añadir línea' para empezar.",
                     text_color=COLOR_TEXTO_SEC,
                     font=("Segoe UI", 10, "italic")).pack(anchor="w", pady=6)
        return

    for i, linea in enumerate(lineas):
        _crear_tarjeta_linea(app, i, linea, len(lineas))


def _crear_tarjeta_linea(app, indice, linea, total):
    card = ctk.CTkFrame(app.lineas_frame, fg_color=COLOR_PANEL, corner_radius=10)
    card.pack(fill=tk.X, pady=5)

    # Header: nombre + botones
    header = ctk.CTkFrame(card, fg_color=COLOR_PANEL, corner_radius=0)
    header.pack(fill=tk.X, padx=12, pady=(10, 4))

    ctk.CTkLabel(header, text=f"● {linea.get('nombre', 'Sin nombre')}",
                 text_color=COLOR_TEXTO,
                 font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)

    ctk.CTkButton(header, text="🗑️",
                  command=lambda i=indice: app.eliminar_linea_modelo(i),
                  fg_color=BTN_PELIGRO_FG, text_color=BTN_PELIGRO_TXT,
                  hover_color=BTN_PELIGRO_HOVER,
                  corner_radius=8, width=32, height=28,
                  font=("Segoe UI", 10)).pack(side=tk.RIGHT, padx=(3, 0))

    if indice < total - 1:
        ctk.CTkButton(header, text="↓",
                      command=lambda i=indice: app.mover_linea(i, 1),
                      fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                      corner_radius=8, width=32, height=28,
                      font=("Segoe UI", 12, "bold")).pack(side=tk.RIGHT, padx=(3, 0))

    if indice > 0:
        ctk.CTkButton(header, text="↑",
                      command=lambda i=indice: app.mover_linea(i, -1),
                      fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                      corner_radius=8, width=32, height=28,
                      font=("Segoe UI", 12, "bold")).pack(side=tk.RIGHT, padx=(3, 0))

    # --- Imagen de la línea ---
    ctk.CTkLabel(card, text="Imagen de la línea:",
                 text_color=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill=tk.X, padx=12, pady=(8, 3))

    frame_img_linea = ctk.CTkFrame(card, fg_color=COLOR_PANEL, corner_radius=0)
    frame_img_linea.pack(fill=tk.X, padx=12)

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
            lbl_img.pack(side=tk.LEFT, padx=(0, 8))
        except Exception:
            ctk.CTkLabel(frame_img_linea, text="📷", text_color=COLOR_TEXTO_SEC,
                         font=("Segoe UI", 22)).pack(side=tk.LEFT, padx=(0, 8))

        ctk.CTkButton(frame_img_linea, text="✕ Quitar",
                      command=lambda i=indice: app.eliminar_imagen_linea(i),
                      fg_color=BTN_PELIGRO_FG, text_color=BTN_PELIGRO_TXT,
                      hover_color=BTN_PELIGRO_HOVER,
                      corner_radius=8, height=28, width=80,
                      font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
    else:
        ctk.CTkButton(frame_img_linea, text="📷  Subir imagen",
                      command=lambda i=indice: app.subir_imagen_linea(i),
                      fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                      corner_radius=8, height=28, width=120,
                      font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

    # --- Descripción ---
    ctk.CTkLabel(card, text="Descripción:",
                 text_color=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill=tk.X, padx=12, pady=(8, 3))

    texto_desc = ctk.CTkTextbox(card, height=50,
                                 font=("Segoe UI", 10),
                                 fg_color=COLOR_INPUT, text_color=COLOR_TEXTO,
                                 border_width=0, corner_radius=8)
    texto_desc.pack(fill=tk.X, padx=12)
    texto_desc.insert("1.0", linea.get("descripcion", ""))
    texto_desc.bind("<FocusOut>",
                    lambda e, i=indice, t=texto_desc: app.editar_descripcion_linea(
                        i, t.get("1.0", tk.END).strip()))

    # --- Colores ---
    frame_colores = ctk.CTkFrame(card, fg_color=COLOR_PANEL, corner_radius=0)
    frame_colores.pack(fill=tk.X, padx=12, pady=(8, 10))

    ctk.CTkLabel(frame_colores, text="Colores:",
                 text_color=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

    ctk.CTkButton(frame_colores, text="+ Añadir color",
                  command=lambda i=indice: app.agregar_color_linea(i),
                  fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                  corner_radius=8, height=26, width=110,
                  font=("Segoe UI", 9, "bold")).pack(side=tk.RIGHT)

    colores = linea.get("colores", [])
    if colores:
        chips_frame = ctk.CTkFrame(card, fg_color=COLOR_PANEL, corner_radius=0)
        chips_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
        for j, col in enumerate(colores):
            _crear_chip_color(app, chips_frame, indice, j, col)


def _crear_chip_color(app, parent, indice_linea, indice_color, color):
    chip = ctk.CTkFrame(parent, fg_color=COLOR_INPUT, corner_radius=12)
    chip.pack(side=tk.LEFT, padx=(0, 5), pady=2)

    canvas = tk.Canvas(chip, width=16, height=16, bg=COLOR_INPUT,
                       highlightthickness=0, bd=0)
    canvas.pack(side=tk.LEFT, padx=(6, 4))
    canvas.create_oval(1, 1, 15, 15, fill=color.get("hex", "#FFFFFF"),
                       outline="#64748b", width=1)

    ctk.CTkLabel(chip, text=color.get("nombre", ""),
                 text_color=COLOR_TEXTO,
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 4))

    ctk.CTkButton(chip, text="×",
                  command=lambda i=indice_linea, j=indice_color: app.eliminar_color_linea(i, j),
                  fg_color="transparent", text_color="#f87171",
                  hover_color="#3f1d1d",
                  corner_radius=8, width=22, height=22,
                  font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=(0, 4))


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