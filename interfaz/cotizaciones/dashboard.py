"""
Dashboard derecho: lista de cotizaciones registradas.
Agrupadas por semana de creación, ordenadas por día de la visita pautada.
"""
import re
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from datetime import datetime

from config import BASE_DIR
from core.tarjetas import formatear_fecha_larga


def crear_dashboard(app):
    """Crea el canvas y el frame del dashboard."""
    tk.Label(app.main_panel, text="REGISTRO DE COTIZACIONES",
             bg="#0f172a", fg="#f8fafc",
             font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))

    contenedor = tk.Frame(app.main_panel, bg="#0f172a")
    contenedor.pack(fill=tk.BOTH, expand=True)

    app.canvas_dash = tk.Canvas(contenedor, bg="#0f172a", highlightthickness=0, bd=0)
    app.scrollbar_dash = ttk.Scrollbar(contenedor, orient="vertical", command=app.canvas_dash.yview)
    app.cards_frame = tk.Frame(app.canvas_dash, bg="#0f172a")

    app.cards_frame.bind(
        "<Configure>",
        lambda e: app.canvas_dash.configure(scrollregion=app.canvas_dash.bbox("all"))
    )
    app.canvas_dash.create_window((0, 0), window=app.cards_frame, anchor="nw")
    app.canvas_dash.configure(yscrollcommand=app.scrollbar_dash.set)

    app.canvas_dash.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    app.scrollbar_dash.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_mousewheel(event):
        app.canvas_dash.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(_):
        app.canvas_dash.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_):
        app.canvas_dash.unbind_all("<MouseWheel>")

    app.canvas_dash.bind("<Enter>", _bind_mousewheel)
    app.canvas_dash.bind("<Leave>", _unbind_mousewheel)


def cargar_registros(app):
    """Rellena el dashboard con las cotizaciones del CSV, agrupadas por semana y día."""
    from core.datos import leer_registros
    from core.tarjetas import obtener_semana_iso

    for w in app.cards_frame.winfo_children():
        w.destroy()

    registros = leer_registros()
    if not registros:
        tk.Label(app.cards_frame, text="No hay cotizaciones registradas aún.",
                 bg="#0f172a", fg="#64748b", font=("Segoe UI", 11)).pack(anchor="w", pady=20)
        return

    # --- Agrupar por semana ISO (fecha de creación) ---
    semanas = {}
    for reg in registros:
        try:
            fecha_dt = datetime.strptime(reg[1], "%d/%m/%Y %H:%M")
        except Exception:
            fecha_dt = datetime.now()
        year, week, lunes, domingo = obtener_semana_iso(fecha_dt)
        clave = f"{year}-Semana-{week:02d}"
        semanas.setdefault(clave, {
            "lunes": lunes,
            "domingo": domingo,
            "registros": []
        })["registros"].append(reg)

    # --- Dibujar cada semana ---
    for clave in sorted(semanas.keys(), reverse=True):
        info = semanas[clave]
        lunes_str = info["lunes"].strftime("%d/%m/%Y")
        domingo_str = info["domingo"].strftime("%d/%m/%Y")
        cantidad = len(info["registros"])

        # Encabezado de la semana
        header_sem = tk.Frame(app.cards_frame, bg="#0f172a")
        header_sem.pack(fill=tk.X, pady=(14, 6), padx=5)

        tk.Label(header_sem, text=f"📅 {clave}",
                 bg="#0f172a", fg="#fbbf24",
                 font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)

        tk.Label(header_sem, text=f"({lunes_str} → {domingo_str})",
                 bg="#0f172a", fg="#64748b",
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(10, 0))

        tk.Label(header_sem, text=f"{cantidad} cotización{'es' if cantidad != 1 else ''}",
                 bg="#1e293b", fg="#cbd5e1",
                 font=("Segoe UI", 8, "bold"),
                 padx=8, pady=2).pack(side=tk.RIGHT)

        # --- Agrupar por día de la fecha pautada ---
        grupos_dias = _agrupar_por_dia(info["registros"])

        for grupo in grupos_dias:
            # Encabezado del día
            header_dia = tk.Frame(app.cards_frame, bg="#0f172a")
            header_dia.pack(fill=tk.X, pady=(8, 4), padx=5)

            tk.Label(header_dia, text=grupo["encabezado"],
                     bg="#0f172a", fg="#973359",
                     font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

            # Tarjetas del día
            for reg in grupo["registros"]:
                _dibujar_tarjeta(app, reg)


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

        # Ordenar por hora pautada
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
def _dibujar_tarjeta(app, reg):
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

    card = tk.Frame(app.cards_frame, bg="#1e293b", padx=15, pady=12)
    card.pack(fill=tk.X, pady=6, padx=5)

    # --- Fila 1: Cliente + Monto ---
    top = tk.Frame(card, bg="#1e293b")
    top.pack(fill=tk.X)

    tk.Label(top, text=cliente, bg="#1e293b", fg="#f8fafc",
             font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
    tk.Label(top, text=monto, bg="#1e293b", fg="#34d399",
             font=("Segoe UI", 11, "bold")).pack(side=tk.RIGHT)

    # --- Fila 2: Fecha pautada destacada (si existe) ---
    if fecha_pautada:
        fecha_larga = formatear_fecha_larga(fecha_pautada)
        texto_fecha = f"📅 {fecha_larga}"
        if hora_pautada:
            texto_fecha += f" · {hora_pautada}"

        frame_fecha = tk.Frame(card, bg="#973359", padx=8, pady=4)
        frame_fecha.pack(fill=tk.X, pady=(6, 4))
        tk.Label(frame_fecha, text=texto_fecha, bg="#973359", fg="#ffffff",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")

    # --- Fila 3: Detalles ---
    tk.Label(card, text=f"📦 {concepto} | 📞 {telefono} | 🗓️ Creada: {fecha}",
             bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 4))

    # --- Notas del cliente ---
    if notas_cliente:
        tk.Label(card, text=f"📝 {notas_cliente[:100]}{'...' if len(notas_cliente) > 100 else ''}",
                 bg="#1e293b", fg="#fbbf24",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(0, 4))

    # --- Notas internas (color distinto) ---
    if notas_internas:
        tk.Label(card, text=f"🔒 {notas_internas[:100]}{'...' if len(notas_internas) > 100 else ''}",
                 bg="#1e293b", fg="#a78bfa",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(0, 6))

    # --- Botones ---
    btn_frame = tk.Frame(card, bg="#1e293b")
    btn_frame.pack(anchor="w", pady=(4, 0))

    # Editar
    tk.Button(btn_frame, text="✏️ Editar", bg="#7c3aed", fg="white",
              font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
              command=lambda i=id_reg: app.editar_cotizacion(i)).pack(side=tk.LEFT, padx=(0, 6))

    # Abrir
    tk.Button(btn_frame, text="🌐 Abrir", bg="#0ea5e9", fg="white",
              font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
              command=lambda r=ruta_html: abrir_html(app, r)).pack(side=tk.LEFT, padx=(0, 6))

    # Copiar link
    if link_ind:
        tk.Button(btn_frame, text="📋 Link", bg="#973359", fg="white",
                  font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
                  command=lambda u=link_ind: copiar_al_portapapeles(app, u)).pack(side=tk.LEFT, padx=(0, 6))

    # WhatsApp
    tel_limpio = re.sub(r'\D', '', telefono)
    tk.Button(btn_frame, text="💬 WA", bg="#16a34a", fg="white",
              font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
              command=lambda t=tel_limpio: webbrowser.open(f"https://wa.me/{t}")).pack(side=tk.LEFT, padx=(0, 6))

    # Eliminar
    tk.Button(btn_frame, text="🗑️", bg="#ef4444", fg="white",
              font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
              command=lambda i=id_reg: app.eliminar_registro(i)).pack(side=tk.LEFT)


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