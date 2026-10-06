"""
Dashboard derecho: lista de cotizaciones registradas (con scroll de rueda).
"""
import re
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

from config import BASE_DIR


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

    # Scroll con la rueda del ratón
    def _on_mousewheel(event):
        app.canvas_dash.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(_):
        app.canvas_dash.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_):
        app.canvas_dash.unbind_all("<MouseWheel>")

    app.canvas_dash.bind("<Enter>", _bind_mousewheel)
    app.canvas_dash.bind("<Leave>", _unbind_mousewheel)


def cargar_registros(app):
    """Rellena el dashboard con las cotizaciones del CSV."""
    from core.datos import leer_registros

    for w in app.cards_frame.winfo_children():
        w.destroy()

    registros = leer_registros()
    if not registros:
        tk.Label(app.cards_frame, text="No hay cotizaciones registradas aún.",
                 bg="#0f172a", fg="#64748b", font=("Segoe UI", 11)).pack(anchor="w", pady=20)
        return

    for reg in reversed(registros):
        id_reg, fecha, cliente, domicilio, telefono, concepto, cotizacion, monto, notas = reg[:9]
        ruta_html = reg[9] if len(reg) > 9 else ""
        link_ind = reg[10] if len(reg) > 10 else ""

        card = tk.Frame(app.cards_frame, bg="#1e293b", padx=15, pady=12)
        card.pack(fill=tk.X, pady=6, padx=5)

        top = tk.Frame(card, bg="#1e293b")
        top.pack(fill=tk.X)
        tk.Label(top, text=cliente, bg="#1e293b", fg="#f8fafc",
                 font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        tk.Label(top, text=monto, bg="#1e293b", fg="#34d399",
                 font=("Segoe UI", 11, "bold")).pack(side=tk.RIGHT)

        tk.Label(card, text=f"Concepto: {concepto} | Tel: {telefono} | {fecha}",
                 bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 6))

        if notas:
            tk.Label(card, text=f"📝 {notas[:100]}", bg="#1e293b", fg="#fbbf24",
                     font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(0, 6))

        btn_frame = tk.Frame(card, bg="#1e293b")
        btn_frame.pack(anchor="w", pady=(4, 0))

        tk.Button(btn_frame, text="🌐 Abrir", bg="#0ea5e9", fg="white",
                  font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
                  command=lambda r=ruta_html: abrir_html(app, r)).pack(side=tk.LEFT, padx=(0, 6))

        if link_ind:
            tk.Button(btn_frame, text="📋 Copiar link", bg="#973359", fg="white",
                      font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
                      command=lambda u=link_ind: copiar_al_portapapeles(app, u)).pack(side=tk.LEFT, padx=(0, 6))

        tel_limpio = re.sub(r'\D', '', telefono)
        tk.Button(btn_frame, text="💬 WA", bg="#16a34a", fg="white",
                  font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
                  command=lambda t=tel_limpio: webbrowser.open(f"https://wa.me/{t}")).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(btn_frame, text="🗑️", bg="#ef4444", fg="white",
                  font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
                  command=lambda i=id_reg: app.eliminar_registro(i)).pack(side=tk.LEFT)


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