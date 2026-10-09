"""
Construcción del formulario lateral (sidebar izquierdo).
Layout: logo fijo arriba + campos scrolleables + botones fijos abajo.
Migrado a customtkinter para botones y widgets modernos.
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import webbrowser

from config import LOGO_PNG_CLARO, URL_BASE


# ============================================================
# COLORES DEL TEMA
# ============================================================
COLOR_FONDO = "#1e293b"           # fondo del sidebar
COLOR_TEXTO = "#f8fafc"           # texto principal
COLOR_TEXTO_SEC = "#94a3b8"       # texto secundario (labels)
COLOR_INPUT = "#334155"           # fondo de los inputs
COLOR_ACENTO = "#973359"          # rosa de Aluze

# Botones
BTN_PRINCIPAL_FG = "#f8fafc"
BTN_PRINCIPAL_TXT = "#334155"
BTN_PRINCIPAL_HOVER = "#e2e8f0"

BTN_SECUNDARIO_FG = "#f8fafc"
BTN_SECUNDARIO_TXT = "#334155"
BTN_SECUNDARIO_HOVER = "#e2e8f0"

BTN_PELIGRO_FG = "#f1f5f9"
BTN_PELIGRO_TXT = "#b91c1c"
BTN_PELIGRO_HOVER = "#fee2e2"


def crear_formulario(app):
    """
    Crea el sidebar con:
    - Logo + título fijos arriba.
    - Campos del formulario scrolleables en el centro.
    - Botones de acción fijos abajo.
    """
    # ============================================================
    # CABECERA FIJA (logo + título)
    # ============================================================
    header = ctk.CTkFrame(app.sidebar, fg_color=COLOR_FONDO, corner_radius=0)
    header.pack(side=tk.TOP, fill=tk.X)

    logo_mostrado = False
    if LOGO_PNG_CLARO.exists():
        try:
            app.logo_img = tk.PhotoImage(file=str(LOGO_PNG_CLARO))
            factor = max(1, app.logo_img.width() // 240)
            if factor > 1:
                app.logo_img = app.logo_img.subsample(factor, factor)
            ctk.CTkLabel(header, image=app.logo_img, text="",
                         fg_color=COLOR_FONDO).pack(pady=(0, 6))
            logo_mostrado = True
        except Exception as e:
            print(f"Error cargando PNG claro: {e}")
    if not logo_mostrado:
        ctk.CTkLabel(header, text="LogoAluzeClaro.png no encontrado",
                     text_color="#fbbf24",
                     font=("Segoe UI", 8, "italic")).pack(pady=(0, 6))

    ctk.CTkLabel(header, text="NUEVA COTIZACIÓN",
                 text_color=COLOR_TEXTO,
                 font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))

    # ============================================================
    # PIE FIJO (botones de acción)
    # ============================================================
    footer = ctk.CTkFrame(app.sidebar, fg_color=COLOR_FONDO, corner_radius=0)
    footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0), padx=10)

    # --- Botón principal ---
    btn_generar = ctk.CTkButton(
        footer,
        text="✨  Generar cotización",
        command=app.guardar_cotizacion,
        fg_color=BTN_PRINCIPAL_FG,
        text_color=BTN_PRINCIPAL_TXT,
        hover_color=BTN_PRINCIPAL_HOVER,
        corner_radius=12,
        height=42,
        font=("Segoe UI", 12, "bold"),
    )
    btn_generar.pack(fill=tk.X, pady=(0, 8))

    # --- Fila 1: Panel + Subir ---
    fila1 = ctk.CTkFrame(footer, fg_color=COLOR_FONDO, corner_radius=0)
    fila1.pack(fill=tk.X, pady=(0, 6))
    fila1.columnconfigure(0, weight=1)
    fila1.columnconfigure(1, weight=1)

    btn_panel = ctk.CTkButton(
        fila1,
        text="🌐  Panel",
        command=lambda: webbrowser.open(URL_BASE),
        fg_color=BTN_SECUNDARIO_FG,
        text_color=BTN_SECUNDARIO_TXT,
        hover_color=BTN_SECUNDARIO_HOVER,
        corner_radius=10,
        height=34,
        font=("Segoe UI", 10, "bold"),
    )
    btn_panel.grid(row=0, column=0, sticky="ew", padx=(0, 3))

    btn_subir = ctk.CTkButton(
        fila1,
        text="☁️  Subir",
        command=app.accion_subir_github,
        fg_color=BTN_SECUNDARIO_FG,
        text_color=BTN_SECUNDARIO_TXT,
        hover_color=BTN_SECUNDARIO_HOVER,
        corner_radius=10,
        height=34,
        font=("Segoe UI", 10, "bold"),
    )
    btn_subir.grid(row=0, column=1, sticky="ew", padx=(3, 0))

    # --- Fila 2: Actualizar + Regenerar ---
    fila2 = ctk.CTkFrame(footer, fg_color=COLOR_FONDO, corner_radius=0)
    fila2.pack(fill=tk.X, pady=(0, 6))
    fila2.columnconfigure(0, weight=1)
    fila2.columnconfigure(1, weight=1)

    btn_actualizar = ctk.CTkButton(
        fila2,
        text="🔄  Actualizar",
        command=app.accion_forzar_actualizacion,
        fg_color=BTN_SECUNDARIO_FG,
        text_color=BTN_SECUNDARIO_TXT,
        hover_color=BTN_SECUNDARIO_HOVER,
        corner_radius=10,
        height=34,
        font=("Segoe UI", 10, "bold"),
    )
    btn_actualizar.grid(row=0, column=0, sticky="ew", padx=(0, 3))

    btn_regenerar = ctk.CTkButton(
        fila2,
        text="🔁  Regenerar",
        command=app.regenerar_todas_las_tarjetas,
        fg_color=BTN_SECUNDARIO_FG,
        text_color=BTN_SECUNDARIO_TXT,
        hover_color=BTN_SECUNDARIO_HOVER,
        corner_radius=10,
        height=34,
        font=("Segoe UI", 10, "bold"),
    )
    btn_regenerar.grid(row=0, column=1, sticky="ew", padx=(3, 0))

    # --- Botón peligro ---
    btn_borrar = ctk.CTkButton(
        footer,
        text="🗑️  Borrar todo",
        command=app.borrar_todo,
        fg_color=BTN_PELIGRO_FG,
        text_color=BTN_PELIGRO_TXT,
        hover_color=BTN_PELIGRO_HOVER,
        corner_radius=10,
        height=32,
        font=("Segoe UI", 10, "bold"),
    )
    btn_borrar.pack(fill=tk.X, pady=(0, 4))

    # ============================================================
    # ZONA CENTRAL SCROLLABLE (campos del formulario)
    # ============================================================
    cuerpo = ctk.CTkFrame(app.sidebar, fg_color=COLOR_FONDO, corner_radius=0)
    cuerpo.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(4, 4))

    # ScrollableFrame nativo de customtkinter
    app.form_frame = ctk.CTkScrollableFrame(
        cuerpo,
        fg_color=COLOR_FONDO,
        corner_radius=0,
        scrollbar_button_color="#334155",
        scrollbar_button_hover_color="#475569",
    )
    app.form_frame.pack(fill=tk.BOTH, expand=True, padx=(10, 4))

    # ============================================================
    # HELPERS DE CAMPOS
    # ============================================================
    def crear_label(texto, opcional=False):
        texto_final = texto if not opcional else f"{texto} (opcional)"
        ctk.CTkLabel(
            app.form_frame,
            text=texto_final,
            text_color=COLOR_TEXTO_SEC,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill=tk.X, pady=(10, 3))

    def crear_entry(key):
        ent = ctk.CTkEntry(
            app.form_frame,
            font=("Segoe UI", 11),
            fg_color=COLOR_INPUT,
            text_color=COLOR_TEXTO,
            border_width=0,
            corner_radius=8,
            height=36,
        )
        ent.pack(fill=tk.X)
        app.entries[key] = ent
        return ent

    def crear_text(key, height=3):
        txt = ctk.CTkTextbox(
            app.form_frame,
            height=height * 22,   # aproximar altura de líneas
            font=("Segoe UI", 11),
            fg_color=COLOR_INPUT,
            text_color=COLOR_TEXTO,
            border_width=0,
            corner_radius=8,
        )
        txt.pack(fill=tk.X)
        app.entries[key] = txt
        return txt

    def crear_separador(texto):
        """Separador visual entre secciones."""
        frame_sep = ctk.CTkFrame(app.form_frame, fg_color=COLOR_FONDO, corner_radius=0)
        frame_sep.pack(fill=tk.X, pady=(18, 6))

        ctk.CTkLabel(
            frame_sep,
            text=texto,
            text_color=COLOR_ACENTO,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill=tk.X)

        ctk.CTkFrame(frame_sep, fg_color="#334155", height=1, corner_radius=0).pack(
            fill=tk.X, pady=(3, 0))

    # ============================================================
    # CAMPOS DEL FORMULARIO
    # ============================================================
    app.entries = {}

    # --- Campos principales ---
    crear_label("Nombre del Cliente")
    crear_entry("Nombre del Cliente")

    crear_label("Domicilio")
    crear_entry("Domicilio")

    crear_label("Teléfono Celular")
    crear_entry("Teléfono Celular")

    crear_label("Concepto / Sistema")
    crear_entry("Concepto / Sistema")

    crear_label("Detalles de Cotización")
    crear_text("Detalles de Cotización", height=4)

    crear_label("Monto Aproximado")
    crear_entry("Monto Aproximado")

    # --- VISITA PAUTADA ---
    crear_separador("📅  VISITA PAUTADA (opcional)")

    # Fila: Fecha + Hora en 2 columnas
    frame_fecha = ctk.CTkFrame(app.form_frame, fg_color=COLOR_FONDO, corner_radius=0)
    frame_fecha.pack(fill=tk.X, pady=(4, 2))
    frame_fecha.columnconfigure(0, weight=3)
    frame_fecha.columnconfigure(1, weight=2)

    # Fecha
    frame_fecha_col = ctk.CTkFrame(frame_fecha, fg_color=COLOR_FONDO, corner_radius=0)
    frame_fecha_col.grid(row=0, column=0, sticky="ew", padx=(0, 4))

    ctk.CTkLabel(frame_fecha_col, text="Fecha (dd/mm/aaaa)",
                 text_color=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill=tk.X, pady=(0, 2))

    entry_fecha_pautada = ctk.CTkEntry(
        frame_fecha_col,
        font=("Segoe UI", 11),
        fg_color=COLOR_INPUT,
        text_color=COLOR_TEXTO,
        border_width=0,
        corner_radius=8,
        height=36,
    )
    entry_fecha_pautada.pack(fill=tk.X)
    app.entries["FechaPautada"] = entry_fecha_pautada

    # Hora
    frame_hora_col = ctk.CTkFrame(frame_fecha, fg_color=COLOR_FONDO, corner_radius=0)
    frame_hora_col.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    ctk.CTkLabel(frame_hora_col, text="Hora (HH:MM)",
                 text_color=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill=tk.X, pady=(0, 2))

    entry_hora_pautada = ctk.CTkEntry(
        frame_hora_col,
        font=("Segoe UI", 11),
        fg_color=COLOR_INPUT,
        text_color=COLOR_TEXTO,
        border_width=0,
        corner_radius=8,
        height=36,
    )
    entry_hora_pautada.pack(fill=tk.X)
    app.entries["HoraPautada"] = entry_hora_pautada

    # --- NOTAS ---
    crear_separador("📝  NOTAS")

    crear_label("Notas del cliente")
    crear_text("NotasCliente", height=3)

    crear_label("Notas internas (no se ven en la tarjeta)")
    crear_text("NotasInternas", height=2)

    # --- Checkbox subir auto ---
    app.subir_auto = ctk.BooleanVar(value=True)
    ctk.CTkCheckBox(
        app.form_frame,
        text="☁️  Subir a GitHub al guardar",
        variable=app.subir_auto,
        text_color="#cbd5e1",
        font=("Segoe UI", 10),
        fg_color=COLOR_ACENTO,
        hover_color="#7f2a4a",
        border_color="#64748b",
        corner_radius=6,
    ).pack(anchor="w", pady=(16, 8))