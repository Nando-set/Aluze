"""
Ventana emergente que muestra los links generados tras guardar una cotización.
"""
import tkinter as tk
from tkinter import messagebox
import webbrowser


class VentanaLinks(tk.Toplevel):
    def __init__(self, parent, link_individual, link_panel):
        super().__init__(parent)
        self.title("🔗 Links de la cotización")
        self.configure(bg="#1e293b")
        self.geometry("520x280")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text="✅ Cotización subida", bg="#1e293b", fg="#34d399",
                 font=("Segoe UI", 13, "bold")).pack(pady=(18, 4))
        tk.Label(self, text="Comparte estos links:", bg="#1e293b", fg="#94a3b8",
                 font=("Segoe UI", 10)).pack(pady=(0, 14))

        self._crear_bloque("🔗 Link individual (esta cotización)", link_individual)
        self._crear_bloque("📋 Link del panel completo (para tu jefe)", link_panel)

        tk.Label(self, text="⏱️ GitHub Pages tarda 30-60 seg en actualizar.",
                 bg="#1e293b", fg="#fbbf24", font=("Segoe UI", 8, "italic")).pack(pady=(4, 0))

        tk.Button(self, text="Cerrar", bg="#334155", fg="white",
                  font=("Segoe UI", 10), relief=tk.FLAT, cursor="hand2",
                  command=self.destroy).pack(pady=8)

    def _crear_bloque(self, titulo, url):
        frame = tk.Frame(self, bg="#1e293b")
        frame.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(frame, text=titulo, bg="#1e293b", fg="#cbd5e1",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        row = tk.Frame(frame, bg="#1e293b")
        row.pack(fill=tk.X, pady=(2, 0))
        entry = tk.Entry(row, font=("Segoe UI", 9), bg="#0f172a", fg="#f8fafc",
                         relief=tk.FLAT, insertbackground="white")
        entry.insert(0, url)
        entry.configure(state="readonly")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        tk.Button(row, text="📋", bg="#973359", fg="white", relief=tk.FLAT,
                  cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=lambda u=url: self._copiar(u)).pack(side=tk.LEFT, padx=(4, 0))
        tk.Button(row, text="🌐", bg="#0ea5e9", fg="white", relief=tk.FLAT,
                  cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=lambda u=url: webbrowser.open(u)).pack(side=tk.LEFT, padx=(4, 0))

    def _copiar(self, texto):
        self.clipboard_clear()
        self.clipboard_append(texto)
        messagebox.showinfo("Copiado", "Link copiado al portapapeles.", parent=self)