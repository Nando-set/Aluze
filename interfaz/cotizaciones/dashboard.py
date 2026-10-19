"""
Dashboard derecho: lista de cotizaciones registradas.
Agrupadas por semana de la FECHA PAUTADA (o de creación si no hay).
Todas las semanas colapsadas excepto la actual.
Migrado a customtkinter.
"""
import re
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import webbrowser
from datetime import datetime

from config import BASE_DIR
from core.tarjetas import formatear_fecha_larga, obtener_semana_iso


# ============================================================
# COLORES
# ============================================================
COLOR_FONDO = "#0f172a"
COLOR_PANEL = "#1e293b"
COLOR_INPUT = "#334155"
COLOR_TEXTO = "#f8fafc"
COLOR_TEXTO_SEC = "#94a3b8"
COLOR_ROSA = "#973359"
COLOR_ROSA_HOVER = "#7f2a4a"
COLOR_VERDE = "#34d399"
COLOR_AMARILLO = "#fbbf24"
COLOR_MORADO = "#a78bfa"

# Botones estilo IA
BTN_FG = "#f8fafc"
BTN_TXT = "#334155"
BTN_HOVER = "#e2e8f0"

BTN_PELIGRO_FG = "#f1f5f9"
BTN_PELIGRO_TXT = "#b91c1c"
BTN_PELIGRO_HOVER = "#fee2e2"


# ============================================================
# ESTADO GLOBAL DE SEMANAS COLAPSADAS
# ============================================================
# Diccionario: {clave_semana: bool_abierta}
# Se rellena en cada carga. Por defecto: solo la semana actual abierta.
_semanas_abiertas = {}


def crear_dashboard(app):
    """Crea el canvas y el frame del dashboard."""
    ctk.CTkLabel(app.main_panel, text="REGISTRO DE COTIZACIONES",
                 text_color=COLOR_TEXTO,
                 font=("Segoe UI", 16, "bold"),
                 anchor="w").pack(fill=tk.X, pady=(0, 12))

    # ScrollableFrame nativo de customtkinter
    app.cards_frame = ctk.CTkScrollableFrame(
        app.main_panel,
        fg_color=COLOR_FONDO,
        corner_radius=0,
        scrollbar_button_color=COLOR_INPUT,
        scrollbar_button_hover_color="#475569",
    )
    app.cards_frame.pack(fill=tk.BOTH, expand=True)


def cargar_registros(app):
    """
    Rellena el dashboard con las cotizaciones del CSV.
    Agrupa por semana de la FECHA PAUTADA (o de creación si no hay).
    """
    from core.datos import leer_registros

    # Limpiar el frame
    for w in app.cards_frame.winfo_children():
        w.destroy()

    registros = leer_registros()
    if not registros:
        ctk.CTkLabel(app.cards_frame,
                     text="No hay cotizaciones registradas aún.",
                     text_color="#64748b",
                     font=("Segoe UI", 12)).pack(anchor="w", pady=20)
        return

    # --- Clave de la semana actual (para saber cuál dejar abierta) ---
    year_actual, week_actual, _, _ = obtener_semana_iso()
    clave_actual = f"{year_actual}-Semana-{week_actual:02d}"

    # --- Agrupar por semana de la fecha pautada (o de creación si no hay) ---
    semanas = {}
    for reg in registros:
        fecha_pautada = reg[8].strip() if len(reg) > 8 else ""

        # Decidir qué fecha usar para agrupar
        if fecha_pautada:
            try:
                fecha_para_agrupar = datetime.strptime(fecha_pautada, "%d/%m/%Y")
            except Exception:
                # Fecha mal formada → usar fecha de creación
                try:
                    fecha_para_agrupar = datetime.strptime(reg[1], "%d/%m/%Y %H:%M")
                except Exception:
                    fecha_para_agrupar = datetime.now()
        else:
            # Sin fecha pautada → usar fecha de creación
            try:
                fecha_para_agrupar = datetime.strptime(reg[1], "%d/%m/%Y %H:%M")
            except Exception:
                fecha_para_agrupar = datetime.now()

        year, week, lunes, domingo = obtener_semana_iso(fecha_para_agrupar)
        clave = f"{year}-Semana-{week:02d}"

        semanas.setdefault(clave, {
            "lunes": lunes,
            "domingo": domingo,
            "registros": []
        })["registros"].append(reg)

    # --- Asegurar que la semana actual está abierta por defecto ---
    global _semanas_abiertas
    for clave in semanas.keys():
        if clave not in _semanas_abiertas:
            # Por defecto: solo la semana actual abierta
            _semanas_abiertas[clave] = (clave == clave_actual)

    # --- Dibujar cada semana (de más reciente a más antigua) ---
    for clave in sorted(semanas.keys(), reverse=True):
        info = semanas[clave]
        cantidad = len(info["registros"])
        es_actual = (clave == clave_actual)
        abierta = _semanas_abiertas.get(clave, es_actual)

        # --- Encabezado de la semana (pulsable) ---
        header_sem = ctk.CTkFrame(
            app.cards_frame,
            fg_color=COLOR_PANEL if es_actual else "#162032",
            corner_radius=10,
            cursor="hand2",
        )
        header_sem.pack(fill=tk.X, pady=(10, 4))

        # Contenido del header (pulsable)
        inner_header = ctk.CTkFrame(header_sem, fg_color="transparent", corner_radius=0)
        inner_header.pack(fill=tk.X, padx=12, pady=8)

        # Icono de estado (▶ colapsada / ▼ abierta)
        icono = "▼" if abierta else "▶"

        ctk.CTkLabel(
            inner_header,
            text=icono,
            text_color=COLOR_AMARILLO,
            font=("Segoe UI", 12, "bold"),
            width=20,
        ).pack(side=tk.LEFT)

        # Título de la semana
        lunes_str = info["lunes"].strftime("%d/%m/%Y")
        domingo_str = info["domingo"].strftime("%d/%m/%Y")

        titulo = f"📅 {clave}"
        if es_actual:
            titulo += "  ·  ACTUAL"
        titulo += f"   ({lunes_str} → {domingo_str})"

        ctk.CTkLabel(
            inner_header,
            text=titulo,
            text_color=COLOR_AMARILLO if es_actual else COLOR_TEXTO,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(side=tk.LEFT, padx=(4, 0))

        # Badge con cantidad
        ctk.CTkLabel(
            inner_header,
            text=f"{cantidad} cotización{'es' if cantidad != 1 else ''}",
            text_color="#cbd5e1",
            fg_color=COLOR_INPUT,
            font=("Segoe UI", 9, "bold"),
            corner_radius=10,
            padx=10, pady=4,
        ).pack(side=tk.RIGHT)

        # --- Contenedor de contenido (solo visible si está abierta) ---
        contenido_sem = ctk.CTkFrame(app.cards_frame, fg_color=COLOR_FONDO, corner_radius=0)

        # Rellenar contenido
        grupos_dias = _agrupar_por_dia(info["registros"])
        for grupo in grupos_dias:
            # Encabezado del día
            header_dia = ctk.CTkFrame(contenido_sem, fg_color=COLOR_FONDO, corner_radius=0)
            header_dia.pack(fill=tk.X, pady=(8, 4), padx=(24, 0))

            ctk.CTkLabel(header_dia, text=grupo["encabezado"],
                         text_color=COLOR_ROSA,
                         font=("Segoe UI", 11, "bold"),
                         anchor="w").pack(fill=tk.X)

            # Tarjetas del día
            for reg in grupo["registros"]:
                _dibujar_tarjeta(app, reg, contenido_sem)

        # Mostrar u ocultar según el estado
        if abierta:
            contenido_sem.pack(fill=tk.X, padx=0, pady=(0, 8))

        # --- Bind del click para colapsar/expandir ---
        def _toggle(event, clave=clave):
            _toggle_semana(app, clave)

        # Hacer clicables el header y todos sus hijos
        for widget in [header_sem, inner_header]:
            widget.bind("<Button-1>", _toggle)
        for child in inner_header.winfo_children():
            child.bind("<Button-1>", _toggle)


def _toggle_semana(app, clave):
    """Cambia el estado abierto/colapsado de una semana y recarga."""
    global _semanas_abiertas
    _semanas_abiertas[clave] = not _semanas_abiertas.get(clave, False)
    cargar_registros(app)


# ============================================================
# AGRUPAR POR DÍA
# ============================================================
def _agrupar_por_dia(registros):
    """Agrupa los registros de una semana por día de la fecha pautada."""
    sin_fecha = []
    con_fecha = {}

    for reg in registros:
        fecha_pautada = reg[8].strip() if len(reg) > 8 else ""
        if not fecha_pautada:
            sin_fecha.append(reg)
            continue
        try:
            fp_dt = datetime.strptime(fecha_pautada, "%d/%m/%Y")
            clave_dia = fp_dt.strftime("%Y-%m-%d")
            con_fecha.setdefault(clave_dia, {
                "fecha_dt": fp_dt,
                "registros": []
            })["registros"].append(reg)
        except Exception:
            sin_fecha.append(reg)

    grupos = []
    for clave in sorted(con_fecha.keys()):
        info = con_fecha[clave]
        fecha_dt = info["fecha_dt"]
        encabezado = f"📆 {formatear_fecha_larga(fecha_dt.strftime('%d/%m/%Y'))}"

        regs_dia = sorted(
            info["registros"],
            key=lambda r: r[9].strip() if len(r) > 9 and r[9].strip() else "99:99"
        )
        grupos.append({
            "encabezado": encabezado,
            "registros": regs_dia
        })

    if sin_fecha:
        grupos.append({
            "encabezado": "📅 Sin fecha pautada",
            "registros": sin_fecha
        })

    return grupos


# ============================================================
# DIBUJAR TARJETA
# ============================================================
def _dibujar_tarjeta(app, reg, parent):
    """Dibuja una tarjeta de cotización en el dashboard."""
    id_reg = reg[0] if len(reg) > 0 else ""
    fecha = reg[1] if len(reg) > 1 else ""
    cliente = reg[2] if len(reg) > 2 else ""
    domicilio = reg[3] if len(reg) > 3 else ""
    telefono = reg[4] if len(reg) > 4 else ""
    concepto = reg[5] if len(reg) > 5 else ""
    cotizacion = reg[6] if len(reg) > 6 else ""
    monto = reg[7] if len(reg) > 7 else ""
    fecha_pautada = reg[8].strip() if len(reg) > 8 else ""
    hora_pautada = reg[9].strip() if len(reg) > 9 else ""
    notas_cliente = reg[10] if len(reg) > 10 else ""
    notas_internas = reg[11] if len(reg) > 11 else ""
    ruta_html = reg[12] if len(reg) > 12 else ""
    link_ind = reg[13] if len(reg) > 13 else ""

    card = ctk.CTkFrame(parent, fg_color=COLOR_PANEL, corner_radius=12)
    card.pack(fill=tk.X, pady=6, padx=(24, 4))

    # Contenido interno con padding
    inner = ctk.CTkFrame(card, fg_color=COLOR_PANEL, corner_radius=0)
    inner.pack(fill=tk.X, padx=16, pady=14)

    # --- Fila 1: Cliente + Monto ---
    top = ctk.CTkFrame(inner, fg_color=COLOR_PANEL, corner_radius=0)
    top.pack(fill=tk.X)

    ctk.CTkLabel(top, text=cliente,
                 text_color=COLOR_TEXTO,
                 font=("Segoe UI", 13, "bold"),
                 anchor="w").pack(side=tk.LEFT)

    ctk.CTkLabel(top, text=monto,
                 text_color=COLOR_VERDE,
                 font=("Segoe UI", 13, "bold"),
                 anchor="e").pack(side=tk.RIGHT)

    # --- Fila 2: Fecha pautada destacada ---
    if fecha_pautada:
        fecha_larga = formatear_fecha_larga(fecha_pautada)
        texto_fecha = f"📅  {fecha_larga}"
        if hora_pautada:
            texto_fecha += f" · {hora_pautada}"

        frame_fecha = ctk.CTkFrame(inner, fg_color=COLOR_ROSA, corner_radius=8)
        frame_fecha.pack(fill=tk.X, pady=(8, 6))

        ctk.CTkLabel(frame_fecha, text=texto_fecha,
                     text_color="#ffffff",
                     font=("Segoe UI", 11, "bold"),
                     anchor="w").pack(fill=tk.X, padx=12, pady=6)

    # --- Fila 3: Detalles ---
    ctk.CTkLabel(inner,
                 text=f"📦  {concepto}   ·   📞  {telefono}   ·   🗓️  {fecha}",
                 text_color=COLOR_TEXTO_SEC,
                 font=("Segoe UI", 10),
                 anchor="w").pack(fill=tk.X, pady=(2, 4))

    # --- Notas del cliente ---
    if notas_cliente:
        ctk.CTkLabel(inner,
                     text=f"📝  {notas_cliente[:100]}{'...' if len(notas_cliente) > 100 else ''}",
                     text_color=COLOR_AMARILLO,
                     font=("Segoe UI", 10, "italic"),
                     anchor="w",
                     wraplength=600,
                     justify="left").pack(fill=tk.X, pady=(2, 2))

    # --- Notas internas ---
    if notas_internas:
        ctk.CTkLabel(inner,
                     text=f"🔒  {notas_internas[:100]}{'...' if len(notas_internas) > 100 else ''}",
                     text_color=COLOR_MORADO,
                     font=("Segoe UI", 10, "italic"),
                     anchor="w",
                     wraplength=600,
                     justify="left").pack(fill=tk.X, pady=(2, 4))

    # --- Botones ---
    btn_frame = ctk.CTkFrame(inner, fg_color=COLOR_PANEL, corner_radius=0)
    btn_frame.pack(fill=tk.X, pady=(8, 0))

    ctk.CTkButton(btn_frame, text="✏️  Editar",
                  command=lambda i=id_reg: app.editar_cotizacion(i),
                  fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                  corner_radius=8, height=30, width=90,
                  font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 4))

    ctk.CTkButton(btn_frame, text="🌐  Abrir",
                  command=lambda r=ruta_html: abrir_html(app, r),
                  fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                  corner_radius=8, height=30, width=90,
                  font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 4))

    if link_ind:
        ctk.CTkButton(btn_frame, text="📋  Link",
                      command=lambda u=link_ind: copiar_al_portapapeles(app, u),
                      fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                      corner_radius=8, height=30, width=80,
                      font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 4))

    tel_limpio = re.sub(r'\D', '', telefono)
    ctk.CTkButton(btn_frame, text="💬  WA",
                  command=lambda t=tel_limpio: webbrowser.open(f"https://wa.me/{t}"),
                  fg_color=BTN_FG, text_color=BTN_TXT, hover_color=BTN_HOVER,
                  corner_radius=8, height=30, width=70,
                  font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 4))

    ctk.CTkButton(btn_frame, text="🗑️",
                  command=lambda i=id_reg: app.eliminar_registro(i),
                  fg_color=BTN_PELIGRO_FG, text_color=BTN_PELIGRO_TXT,
                  hover_color=BTN_PELIGRO_HOVER,
                  corner_radius=8, height=30, width=40,
                  font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)


# ============================================================
# ACCIONES AUXILIARES
# ============================================================
def abrir_html(app, ruta_relativa):
    if not ruta_relativa:
        messagebox.showwarning("Aviso", "Este registro no tiene HTML asociado.")
        return
    ruta = BASE_DIR / ruta_relativa
    if ruta.exists():
        webbrowser.open(ruta.as_uri())
    else:
        messagebox.showerror("Error", f"No se encontró:\n{ruta}")


def copiar_al_portapapeles(app, texto):
    app.root.clipboard_clear()
    app.root.clipboard_append(texto)
    messagebox.showinfo("Copiado", "Link copiado al portapapeles.")