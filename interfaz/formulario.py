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
        """Botón grande, ocupa todo el ancho."""
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
        """Dos botones en columnas, uno al lado del otro."""
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

    # --- Botón principal ---
    boton_principal(footer, "✨  Generar cotización", "#973359",
                    app.guardar_cotizacion)

    # --- Fila 1: Panel + Subir ---
    boton_par(footer,
              ["🌐  Panel", "☁️  Subir"],
              ["#0ea5e9", "#16a34a"],
              [lambda: webbrowser.open(URL_BASE), app.accion_subir_github])

    # --- Fila 2: Actualizar + Regenerar ---
    boton_par(footer,
              ["🔄  Actualizar", "🔁  Regenerar"],
              ["#7c3aed", "#0891b2"],
              [app.accion_forzar_actualizacion, app.regenerar_todas_las_tarjetas])

    # --- Botón borrar todo (pequeño, rojo tenue) ---
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

    # Scroll con la rueda del ratón
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
    campos = [
        ("Nombre del Cliente", "entry"),
        ("Domicilio", "entry"),
        ("Teléfono Celular", "entry"),
        ("Concepto / Sistema", "entry"),
        ("Detalles de Cotización", "text"),
        ("Monto Aproximado", "entry"),
        ("Notas / Citas / Observaciones", "text"),
    ]
    for label_text, tipo in campos:
        tk.Label(app.form_frame, text=label_text, bg="#1e293b",
                 fg="#94a3b8", font=("Segoe UI", 9, "bold")).pack(
                     anchor="w", pady=(8, 2), fill=tk.X)
        if tipo == "entry":
            ent = tk.Entry(app.form_frame, font=("Segoe UI", 10), bg="#334155",
                           fg="#f8fafc", insertbackground="white",
                           relief=tk.FLAT, borderwidth=0, highlightthickness=0)
            ent.pack(fill=tk.X, ipady=5)
            app.entries[label_text] = ent
        else:
            txt = tk.Text(app.form_frame, height=4, font=("Segoe UI", 10),
                          bg="#334155", fg="#f8fafc", insertbackground="white",
                          relief=tk.FLAT, borderwidth=0, highlightthickness=0)
            txt.pack(fill=tk.X)
            app.entries[label_text] = txt

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
    """Añade efecto hover a un botón (aclarando u oscureciendo el color)."""
    if hover is None:
        hover = _aclarar_color(color_normal)
    boton.bind("<Enter>", lambda e: boton.configure(bg=hover))
    boton.bind("<Leave>", lambda e: boton.configure(bg=color_normal))


def _aclarar_color(hex_color, factor=1.15):
    """Devuelve una versión más clara del color hex dado."""
    hex_color = hex_color.lstrip("#")
    r = min(255, int(int(hex_color[0:2], 16) * factor))
    g = min(255, int(int(hex_color[2:4], 16) * factor))
    b = min(255, int(int(hex_color[4:6], 16) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"