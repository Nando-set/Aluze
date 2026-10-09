"""
Construcción del formulario lateral (sidebar izquierdo).
Layout: logo fijo arriba + campos scrolleables + botones fijos abajo.
"""
import tkinter as tk
from tkinter import ttk
import webbrowser

from config import LOGO_PNG_CLARO, URL_BASE


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
    header = tk.Frame(app.sidebar, bg="#1e293b")
    header.pack(side=tk.TOP, fill=tk.X)

    logo_mostrado = False
    if LOGO_PNG_CLARO.exists():
        try:
            app.logo_img = tk.PhotoImage(file=str(LOGO_PNG_CLARO))
            factor = max(1, app.logo_img.width() // 240)
            if factor > 1:
                app.logo_img = app.logo_img.subsample(factor, factor)
            tk.Label(header, image=app.logo_img, bg="#1e293b").pack(pady=(0, 6))
            logo_mostrado = True
        except Exception as e:
            print(f"Error cargando PNG claro: {e}")
    if not logo_mostrado:
        tk.Label(header, text="LogoAluzeClaro.png no encontrado",
                 bg="#1e293b", fg="#fbbf24",
                 font=("Segoe UI", 8, "italic")).pack(pady=(0, 6))

    tk.Label(header, text="NUEVA COTIZACIÓN", bg="#1e293b",
             fg="#f8fafc", font=("Segoe UI", 12, "bold")).pack(pady=(0, 8))

    # ============================================================
    # PIE FIJO (botones de acción)
    # ============================================================
    footer = tk.Frame(app.sidebar, bg="#1e293b")
    footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))

    def boton_principal(parent, texto, color, comando):
        btn = tk.Button(parent, text=texto, bg=color, fg="white",
                        font=("Segoe UI", 10, "bold"),
                        relief=tk.FLAT, cursor="hand2",
                        activebackground=color, activeforeground="white",
                        borderwidth=0, highlightthickness=0,
                        command=comando)
        btn.pack(fill=tk.X, pady=(0, 6), ipady=9)
        _aplicar_hover(btn, color)
        return btn

    def boton_par(parent, texto, color, comando):
        row = tk.Frame(parent, bg="#1e293b")
        row.pack(fill=tk.X, pady=(0, 6))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        btn1 = tk.Button(row, text=texto[0], bg=color[0], fg="white",
                         font=("Segoe UI", 9, "bold"),
                         relief=tk.FLAT, cursor="hand2",
                         activebackground=color[0], activeforeground="white",
                         borderwidth=0, highlightthickness=0,
                         command=comando[0])
        btn1.grid(row=0, column=0, sticky="ew", padx=(0, 3), ipady=8)
        _aplicar_hover(btn1, color[0])

        btn2 = tk.Button(row, text=texto[1], bg=color[1], fg="white",
                         font=("Segoe UI", 9, "bold"),
                         relief=tk.FLAT, cursor="hand2",
                         activebackground=color[1], activeforeground="white",
                         borderwidth=0, highlightthickness=0,
                         command=comando[1])
        btn2.grid(row=0, column=1, sticky="ew", padx=(3, 0), ipady=8)
        _aplicar_hover(btn2, color[1])
        return btn1, btn2

    boton_principal(footer, "✨  Generar cotización", "#973359",
                    app.guardar_cotizacion)

    boton_par(footer,
              ["🌐  Panel", "☁️  Subir"],
              ["#0ea5e9", "#16a34a"],
              [lambda: webbrowser.open(URL_BASE), app.accion_subir_github])

    boton_par(footer,
              ["🔄  Actualizar", "🔁  Regenerar"],
              ["#7c3aed", "#0891b2"],
              [app.accion_forzar_actualizacion, app.regenerar_todas_las_tarjetas])

    btn_borrar = tk.Button(footer, text="🗑️  Borrar todo",
                           bg="#7f1d1d", fg="#fecaca",
                           font=("Segoe UI", 9, "bold"),
                           relief=tk.FLAT, cursor="hand2",
                           activebackground="#991b1b", activeforeground="#fee2e2",
                           borderwidth=0, highlightthickness=0,
                           command=app.borrar_todo)
    btn_borrar.pack(fill=tk.X, ipady=6)
    _aplicar_hover(btn_borrar, "#7f1d1d", hover="#991b1b")

    # ============================================================
    # ZONA CENTRAL SCROLLABLE (campos del formulario)
    # ============================================================
    cuerpo = tk.Frame(app.sidebar, bg="#1e293b")
    cuerpo.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(4, 4))

    canvas = tk.Canvas(cuerpo, bg="#1e293b", highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(cuerpo, orient="vertical", command=canvas.yview)
    app.form_frame = tk.Frame(canvas, bg="#1e293b")

    app.form_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=app.form_frame, anchor="nw", width=400)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(_):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_):
        canvas.unbind_all("<MouseWheel>")

    canvas.bind("<Enter>", _bind_mousewheel)
    canvas.bind("<Leave>", _unbind_mousewheel)

    # ============================================================
    # CAMPOS DEL FORMULARIO
    # ============================================================
    app.entries = {}

    def crear_label(texto, opcional=False):
        texto_final = texto if not opcional else f"{texto} (opcional)"
        tk.Label(app.form_frame, text=texto_final, bg="#1e293b",
                 fg="#94a3b8", font=("Segoe UI", 9, "bold")).pack(
                     anchor="w", pady=(10, 2), fill=tk.X)

    def crear_entry(key, placeholder=""):
        ent = tk.Entry(app.form_frame, font=("Segoe UI", 10), bg="#334155",
                       fg="#f8fafc", insertbackground="white",
                       relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        ent.pack(fill=tk.X, ipady=5)
        app.entries[key] = ent
        return ent

    def crear_text(key, height=3):
        txt = tk.Text(app.form_frame, height=height, font=("Segoe UI", 10),
                      bg="#334155", fg="#f8fafc", insertbackground="white",
                      relief=tk.FLAT, borderwidth=0, highlightthickness=0)
        txt.pack(fill=tk.X)
        app.entries[key] = txt
        return txt

    def crear_separador(texto):
        """Separador visual entre secciones."""
        frame_sep = tk.Frame(app.form_frame, bg="#1e293b")
        frame_sep.pack(fill=tk.X, pady=(14, 4))
        tk.Label(frame_sep, text=texto, bg="#1e293b", fg="#973359",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Frame(frame_sep, bg="#334155", height=1).pack(fill=tk.X, pady=(2, 0))

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
    crear_separador("📅 VISITA PAUTADA (opcional)")

    # Fila: Fecha + Hora en 2 columnas
    frame_fecha = tk.Frame(app.form_frame, bg="#1e293b")
    frame_fecha.pack(fill=tk.X, pady=(4, 2))
    frame_fecha.columnconfigure(0, weight=3)
    frame_fecha.columnconfigure(1, weight=2)

    # Fecha
    frame_fecha_col = tk.Frame(frame_fecha, bg="#1e293b")
    frame_fecha_col.grid(row=0, column=0, sticky="ew", padx=(0, 4))
    tk.Label(frame_fecha_col, text="Fecha (dd/mm/aaaa)", bg="#1e293b",
             fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 2))
    entry_fecha_pautada = tk.Entry(frame_fecha_col, font=("Segoe UI", 10),
                                    bg="#334155", fg="#f8fafc",
                                    insertbackground="white",
                                    relief=tk.FLAT, borderwidth=0, highlightthickness=0)
    entry_fecha_pautada.pack(fill=tk.X, ipady=5)
    app.entries["FechaPautada"] = entry_fecha_pautada

    # Hora
    frame_hora_col = tk.Frame(frame_fecha, bg="#1e293b")
    frame_hora_col.grid(row=0, column=1, sticky="ew", padx=(4, 0))
    tk.Label(frame_hora_col, text="Hora (HH:MM)", bg="#1e293b",
             fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 2))
    entry_hora_pautada = tk.Entry(frame_hora_col, font=("Segoe UI", 10),
                                   bg="#334155", fg="#f8fafc",
                                   insertbackground="white",
                                   relief=tk.FLAT, borderwidth=0, highlightthickness=0)
    entry_hora_pautada.pack(fill=tk.X, ipady=5)
    app.entries["HoraPautada"] = entry_hora_pautada

    # --- NOTAS ---
    crear_separador("📝 NOTAS")

    crear_label("Notas del cliente")
    crear_text("NotasCliente", height=3)

    crear_label("Notas internas (no se ven en la tarjeta)")
    crear_text("NotasInternas", height=2)

    # Checkbox subir auto
    app.subir_auto = tk.BooleanVar(value=True)
    tk.Checkbutton(app.form_frame, text="☁️  Subir a GitHub al guardar",
                   variable=app.subir_auto, bg="#1e293b", fg="#cbd5e1",
                   selectcolor="#334155", activebackground="#1e293b",
                   activeforeground="#f8fafc", font=("Segoe UI", 9),
                   cursor="hand2", borderwidth=0, highlightthickness=0).pack(
                       anchor="w", pady=(14, 6))


# ============================================================
# UTILIDAD: hover para botones
# ============================================================
def _aplicar_hover(boton, color_normal, hover=None):
    if hover is None:
        hover = _aclarar_color(color_normal)
    boton.bind("<Enter>", lambda e: boton.configure(bg=hover))
    boton.bind("<Leave>", lambda e: boton.configure(bg=color_normal))


def _aclarar_color(hex_color, factor=1.15):
    hex_color = hex_color.lstrip("#")
    r = min(255, int(int(hex_color[0:2], 16) * factor))
    g = min(255, int(int(hex_color[2:4], 16) * factor))
    b = min(255, int(int(hex_color[4:6], 16) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"