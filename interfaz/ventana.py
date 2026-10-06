"""
Ventana principal de Aluze. Une todas las piezas.
"""
import shutil
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

from config import (
    CARPETA_COTIZACIONES, CARPETA_ASSETS,
    LOGO_SVG, LOGO_PNG, LOGO_PNG_CLARO,
    INDEX_HTML, DB_FILE, URL_BASE, BASE_DIR
)

from core.datos import inicializar_csv, leer_registros, agregar_registro, eliminar_registro_por_id
from core.tarjetas import generar_html
from core.panel import regenerar_index

from servicios.github import subir_a_github

from interfaz.formulario import crear_formulario
from interfaz.dashboard import crear_dashboard, cargar_registros
from interfaz.ventana_links import VentanaLinks


def inicializar_estructura():
    """Crea carpetas y copia logos a assets."""
    CARPETA_COTIZACIONES.mkdir(exist_ok=True)
    CARPETA_ASSETS.mkdir(exist_ok=True)

    if LOGO_SVG.exists():
        shutil.copy2(LOGO_SVG, CARPETA_ASSETS / "LogoAluze.svg")
    if LOGO_PNG.exists():
        shutil.copy2(LOGO_PNG, CARPETA_ASSETS / "LogoAluze.png")
    if LOGO_PNG_CLARO.exists():
        shutil.copy2(LOGO_PNG_CLARO, CARPETA_ASSETS / "LogoAluzeClaro.png")

    inicializar_csv()


class AppAluze:
    def __init__(self, root):
        self.root = root
        self.root.title("Aluze - Sistema de Cotizaciones")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 650)
        self.root.configure(bg="#0f172a")

        inicializar_estructura()

        style = ttk.Style()
        style.theme_use('clam')

        # Sidebar más ancho (450px)
        self.sidebar = tk.Frame(root, bg="#1e293b", width=450, padx=15, pady=15)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.main_panel = tk.Frame(root, bg="#0f172a", padx=15, pady=15)
        self.main_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        crear_formulario(self)
        crear_dashboard(self)
        cargar_registros(self)
        regenerar_index()

    # ========================================================
    # ACCIONES
    # ========================================================
    def guardar_cotizacion(self):
        cliente = self.entries["Nombre del Cliente"].get().strip()
        domicilio = self.entries["Domicilio"].get().strip()
        telefono = self.entries["Teléfono Celular"].get().strip()
        concepto = self.entries["Concepto / Sistema"].get().strip()
        cotizacion = self.entries["Detalles de Cotización"].get("1.0", tk.END).strip()
        monto = self.entries["Monto Aproximado"].get().strip()
        notas = self.entries["Notas / Citas / Observaciones"].get("1.0", tk.END).strip()

        if not cliente or not telefono:
            messagebox.showerror("Error", "El nombre del cliente y el teléfono son obligatorios.")
            return

        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        id_reg = int(datetime.now().timestamp() * 1000)

        try:
            ruta_relativa = generar_html(id_reg, cliente, domicilio, telefono,
                                         concepto, cotizacion, monto, notas, fecha)
            link_individual = f"{URL_BASE}{ruta_relativa}"

            agregar_registro([id_reg, fecha, cliente, domicilio, telefono,
                              concepto, cotizacion, monto, notas,
                              ruta_relativa, link_individual])

            regenerar_index()
            self.limpiar_formulario()
            cargar_registros(self)

            if self.subir_auto.get():
                exito, msg = subir_a_github()
                if not exito:
                    messagebox.showwarning("GitHub", f"Guardado local OK, pero falló la subida:\n\n{msg}")
                    return

            VentanaLinks(self.root, link_individual, URL_BASE)

        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar:\n\n{e}")

    def limpiar_formulario(self):
        for label, widget in self.entries.items():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
            else:
                widget.delete("1.0", tk.END)

    def eliminar_registro(self, id_eliminar):
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta cotización del registro?"):
            return
        ruta_relativa = eliminar_registro_por_id(id_eliminar)
        if ruta_relativa:
            ruta = BASE_DIR / ruta_relativa
            if ruta.exists():
                try:
                    ruta.unlink()
                except Exception:
                    pass
        regenerar_index()
        cargar_registros(self)

    def regenerar_todas_las_tarjetas(self):
        registros = leer_registros()
        if not registros:
            messagebox.showwarning("Aviso", "No hay cotizaciones para regenerar.")
            return

        if not messagebox.askyesno("Confirmar",
                                   "Esto regenerará TODAS las tarjetas HTML\n"
                                   "con el código actual.\n\n"
                                   "El CSV no se toca, solo los HTML.\n\n"
                                   "¿Continuar?"):
            return

        try:
            total = len(registros)
            for reg in registros:
                id_reg, fecha, cliente, domicilio, telefono, concepto, cotizacion, monto, notas = reg[:9]
                try:
                    generar_html(id_reg, cliente, domicilio, telefono,
                                 concepto, cotizacion, monto, notas, fecha)
                except Exception as e:
                    print(f"Error regenerando {cliente}: {e}")

            regenerar_index()

            messagebox.showinfo("Listo",
                                f"✅ {total} tarjetas regeneradas.\n\n"
                                "Pulsa '☁️ Subir' para actualizar la nube.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo regenerar:\n\n{e}")

    def borrar_todo(self):
        if not messagebox.askyesno("⚠️ Confirmar",
                                   "¿Borrar TODAS las cotizaciones?\n\n"
                                   "Se eliminará el CSV, la carpeta de cotizaciones\n"
                                   "y se regenerará el panel.\n\n"
                                   "Esta acción NO se puede deshacer."):
            return
        if not messagebox.askyesno("⚠️ ¿SEGURO?",
                                   "Esta es tu última oportunidad.\n\n"
                                   "¿Realmente quieres borrar TODO?"):
            return
        try:
            if DB_FILE.exists():
                DB_FILE.unlink()
            if CARPETA_COTIZACIONES.exists():
                shutil.rmtree(CARPETA_COTIZACIONES)
            if INDEX_HTML.exists():
                INDEX_HTML.unlink()
            inicializar_estructura()
            regenerar_index()
            cargar_registros(self)
            messagebox.showinfo("Listo",
                                "✅ Todo borrado.\n\n"
                                "Recuerda pulsar '☁️ Subir'\n"
                                "para reflejar el cambio en la nube.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo borrar todo:\n\n{e}")

    def accion_subir_github(self):
        exito, msg = subir_a_github()
        if exito:
            messagebox.showinfo("GitHub", msg)
        else:
            messagebox.showerror("GitHub", msg)

    def accion_forzar_actualizacion(self):
        if not messagebox.askyesno("Forzar actualización",
                                   "Esto hará:\n"
                                   "1. Guardar tus cambios locales\n"
                                   "2. Traer cambios de GitHub\n"
                                   "3. Subir todo\n\n"
                                   "¿Continuar?"):
            return
        exito, msg = subir_a_github()
        if exito:
            messagebox.showinfo("GitHub", f"🔄 {msg}")
        else:
            messagebox.showerror("GitHub", msg)