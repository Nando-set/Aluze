"""
Ventana principal de Aluze.
Estructura: logo arriba + pestañas + contenido + botón global abajo.
"""
import shutil
import re
import tkinter as tk
from tkinter import messagebox, ttk, colorchooser, filedialog
from datetime import datetime
from pathlib import Path

from config import (
    CARPETA_COTIZACIONES, CARPETA_ASSETS,
    LOGO_SVG, LOGO_PNG, LOGO_PNG_CLARO,
    INDEX_HTML, DB_FILE, URL_BASE, BASE_DIR
)

from core.datos import inicializar_csv, leer_registros, agregar_registro, eliminar_registro_por_id
from core.tarjetas import generar_html
from core.panel import regenerar_index
from core.catalogo_datos import (
    inicializar_catalogo, buscar_modelo,
    agregar_modelo, actualizar_modelo, eliminar_modelo,
    guardar_imagenes_modelo, guardar_imagen_linea,
    obtener_carpeta_imagenes_modelo,
    obtener_ruta_video_modelo, guardar_video_modelo
)
from core.imagenes import procesar_imagen
from core.videos import procesar_video, eliminar_video
from core.generador_catalogo import regenerar_catalogo

from servicios.github import subir_a_github

# Módulo de cotizaciones
from interfaz.cotizaciones.formulario import crear_formulario
from interfaz.cotizaciones.dashboard import crear_dashboard, cargar_registros
from interfaz.cotizaciones.ventana_links import VentanaLinks

# Módulo de catálogo
from interfaz.catalogo import panel as cat_panel


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
    inicializar_catalogo()


class AppAluze:
    def __init__(self, root):
        self.root = root
        self.root.title("Aluze - Sistema de Gestión")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 650)
        self.root.configure(bg="#0f172a")

        inicializar_estructura()

        style = ttk.Style()
        style.theme_use('clam')

        # ============================================================
        # CONTENEDOR PRINCIPAL
        # ============================================================
        self.contenedor = tk.Frame(root, bg="#0f172a")
        self.contenedor.pack(fill=tk.BOTH, expand=True)

        # ============================================================
        # BARRA DE PESTAÑAS
        # ============================================================
        self.tab_bar = tk.Frame(self.contenedor, bg="#0f172a", pady=10)
        self.tab_bar.pack(side=tk.TOP, fill=tk.X)

        self.tab_activa = tk.StringVar(value="cotizaciones")

        self.botones_tab = {}
        self._crear_tab_button("cotizaciones", "📝  Cotizaciones")
        self._crear_tab_button("catalogo", "🛍️  Catálogo")

        # ============================================================
        # ÁREA DE CONTENIDO
        # ============================================================
        self.area_contenido = tk.Frame(self.contenedor, bg="#0f172a")
        self.area_contenido.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.vista_cotizaciones = tk.Frame(self.area_contenido, bg="#0f172a")
        self.vista_catalogo = tk.Frame(self.area_contenido, bg="#0f172a")

        # ============================================================
        # BARRA INFERIOR
        # ============================================================
        self.barra_inferior = tk.Frame(self.contenedor, bg="#0f172a", pady=8)
        self.barra_inferior.pack(side=tk.BOTTOM, fill=tk.X)

        btn_subir = tk.Button(
            self.barra_inferior,
            text="☁️  Subir TODO a GitHub",
            bg="#16a34a", fg="white",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
            activebackground="#15803d", activeforeground="white",
            borderwidth=0, highlightthickness=0,
            command=self.accion_subir_github,
        )
        btn_subir.pack(fill=tk.X, padx=20, ipady=10)
        self._aplicar_hover(btn_subir, "#16a34a", "#15803d")

        # ============================================================
        # VISTA DE COTIZACIONES
        # ============================================================
        self.sidebar = tk.Frame(self.vista_cotizaciones, bg="#1e293b", width=450, padx=15, pady=15)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.main_panel = tk.Frame(self.vista_cotizaciones, bg="#0f172a", padx=15, pady=15)
        self.main_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        crear_formulario(self)
        crear_dashboard(self)
        cargar_registros(self)
        regenerar_index()

        # ============================================================
        # VISTA DE CATÁLOGO
        # ============================================================
        cat_panel.construir_panel_catalogo(self)

        # Regenerar catálogo automáticamente al iniciar
        regenerar_catalogo()

        # ============================================================
        # MOSTRAR PESTAÑA INICIAL
        # ============================================================
        self._cambiar_tab("cotizaciones")

    # ============================================================
    # SISTEMA DE PESTAÑAS
    # ============================================================
    def _crear_tab_button(self, nombre, texto):
        btn = tk.Button(
            self.tab_bar,
            text=texto,
            bg="#1e293b", fg="#94a3b8",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
            activebackground="#334155", activeforeground="#f8fafc",
            borderwidth=0, highlightthickness=0,
            padx=20, pady=10,
            command=lambda n=nombre: self._cambiar_tab(n),
        )
        btn.pack(side=tk.LEFT, padx=(20, 6))
        self.botones_tab[nombre] = btn

    def _cambiar_tab(self, nombre):
        self.tab_activa.set(nombre)
        self.vista_cotizaciones.pack_forget()
        self.vista_catalogo.pack_forget()

        for n, btn in self.botones_tab.items():
            if n == nombre:
                btn.configure(bg="#973359", fg="#ffffff",
                              activebackground="#7f2a4a")
            else:
                btn.configure(bg="#1e293b", fg="#94a3b8",
                              activebackground="#334155")

        if nombre == "cotizaciones":
            self.vista_cotizaciones.pack(fill=tk.BOTH, expand=True)
        elif nombre == "catalogo":
            self.vista_catalogo.pack(fill=tk.BOTH, expand=True)

    # ============================================================
    # UTILIDAD: hover
    # ============================================================
    @staticmethod
    def _aplicar_hover(boton, color_normal, hover):
        boton.bind("<Enter>", lambda e: boton.configure(bg=hover))
        boton.bind("<Leave>", lambda e: boton.configure(bg=color_normal))

    # ========================================================
    # ACCIONES DEL CATÁLOGO (llamadas desde el panel)
    # ========================================================
    def refrescar_arbol_catalogo(self):
        cat_panel.refrescar_arbol(self)

    def nuevo_modelo_catalogo(self):
        """Limpia el editor para crear un modelo nuevo."""
        cat_panel._limpiar_editor(self)
        messagebox.showinfo("Nuevo modelo",
                            "Rellena los campos y pulsa 'Guardar modelo'.")

    def guardar_modelo_catalogo(self):
        """Guarda el modelo que está en el editor."""
        nombre = self.var_nombre.get().strip()
        categoria_visible = self.var_categoria.get().strip()
        descripcion = self.text_descripcion.get("1.0", tk.END).strip()

        if not nombre:
            messagebox.showerror("Error", "El nombre del modelo es obligatorio.")
            return
        if not categoria_visible:
            messagebox.showerror("Error", "Selecciona una categoría.")
            return

        # Encontrar el id de categoría a partir del texto visible
        cat_id = None
        for c in self.categorias_cache:
            if f"{c['emoji']} {c['nombre']}" == categoria_visible:
                cat_id = c["id"]
                break
        if not cat_id:
            messagebox.showerror("Error", "Categoría no encontrada.")
            return

        # Generar id del modelo (sanitizado)
        id_modelo = re.sub(r'[^a-z0-9_]+', '_', nombre.lower()).strip('_')
        if not id_modelo:
            messagebox.showerror("Error", "El nombre del modelo no es válido.")
            return

        modelo = {
            "id": id_modelo,
            "nombre": nombre,
            "categoria": cat_id,
            "descripcion": descripcion,
            "imagenes": [],
            "video": None,
            "lineas": []
        }

        # ¿Nuevo o existente?
        if self.modelo_seleccionado_id:
            # Actualizar
            ok, msg = actualizar_modelo(self.modelo_seleccionado_id, modelo)
        else:
            # Nuevo
            ok, msg = agregar_modelo(modelo)

        if ok:
            messagebox.showinfo("Éxito", msg)
            self.refrescar_arbol_catalogo()
            cat_panel._limpiar_editor(self)
            regenerar_catalogo()
        else:
            messagebox.showerror("Error", msg)

    def eliminar_modelo_catalogo(self):
        """Elimina el modelo actualmente seleccionado."""
        if not self.modelo_seleccionado_id:
            messagebox.showwarning("Aviso", "No hay ningún modelo seleccionado.")
            return

        if not messagebox.askyesno("Confirmar",
                                    "¿Eliminar este modelo del catálogo?\n\n"
                                    "Esta acción no se puede deshacer."):
            return

        eliminar_modelo(self.modelo_seleccionado_id)
        self.refrescar_arbol_catalogo()
        cat_panel._limpiar_editor(self)
        regenerar_catalogo()
        messagebox.showinfo("Listo", "Modelo eliminado.")

    # ========================================================
    # ACCIONES DE COTIZACIONES
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

    # ========================================================
    # GESTIÓN DE LÍNEAS Y COLORES
    # ========================================================
    def agregar_linea_modelo(self, nombre_linea):
        """Añade una línea al modelo actual en el editor."""
        if not self.modelo_seleccionado_id:
            messagebox.showwarning("Aviso", "Primero guarda el modelo antes de añadir líneas.")
            return

        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return

        modelo.setdefault("lineas", []).append({
            "nombre": nombre_linea,
            "descripcion": "",
            "colores": []
        })
        actualizar_modelo(self.modelo_seleccionado_id, modelo)
        cat_panel._cargar_modelo_en_editor(self, modelo)

    def eliminar_linea_modelo(self, indice):
        """Elimina una línea del modelo actual."""
        if not self.modelo_seleccionado_id:
            return

        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return

        lineas = modelo.get("lineas", [])
        if 0 <= indice < len(lineas):
            if not messagebox.askyesno("Confirmar",
                                        f"¿Eliminar la línea '{lineas[indice]['nombre']}'?"):
                return
            lineas.pop(indice)
            actualizar_modelo(self.modelo_seleccionado_id, modelo)
            cat_panel._cargar_modelo_en_editor(self, modelo)

    def mover_linea(self, indice, direccion):
        """Mueve una línea arriba (-1) o abajo (+1)."""
        if not self.modelo_seleccionado_id:
            return

        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return

        lineas = modelo.get("lineas", [])
        nuevo_indice = indice + direccion
        if 0 <= nuevo_indice < len(lineas):
            lineas[indice], lineas[nuevo_indice] = lineas[nuevo_indice], lineas[indice]
            actualizar_modelo(self.modelo_seleccionado_id, modelo)
            cat_panel._cargar_modelo_en_editor(self, modelo)

    def editar_descripcion_linea(self, indice, texto):
        """Actualiza la descripción de una línea."""
        if not self.modelo_seleccionado_id:
            return
        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return
        lineas = modelo.get("lineas", [])
        if 0 <= indice < len(lineas):
            lineas[indice]["descripcion"] = texto
            actualizar_modelo(self.modelo_seleccionado_id, modelo)

    def agregar_color_linea(self, indice_linea):
        """Abre el diálogo para añadir un color a una línea."""
        if not self.modelo_seleccionado_id:
            return
        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return
        lineas = modelo.get("lineas", [])
        if not (0 <= indice_linea < len(lineas)):
            return

        # Diálogo simple: pedir nombre + color
        dialogo = _DialogoColor(self.root)
        self.root.wait_window(dialogo)
        if not dialogo.resultado:
            return

        lineas[indice_linea].setdefault("colores", []).append(dialogo.resultado)
        actualizar_modelo(self.modelo_seleccionado_id, modelo)
        cat_panel._cargar_modelo_en_editor(self, modelo)

    def eliminar_color_linea(self, indice_linea, indice_color):
        """Elimina un color de una línea."""
        if not self.modelo_seleccionado_id:
            return
        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return
        lineas = modelo.get("lineas", [])
        if 0 <= indice_linea < len(lineas):
            colores = lineas[indice_linea].get("colores", [])
            if 0 <= indice_color < len(colores):
                colores.pop(indice_color)
                actualizar_modelo(self.modelo_seleccionado_id, modelo)
                cat_panel._cargar_modelo_en_editor(self, modelo)

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

    # ========================================================
    # SUBIDA DE IMÁGENES
    # ========================================================
    def subir_fotos_modelo(self):
        """Abre el selector y procesa hasta 3 fotos para el modelo."""
        if not self.modelo_seleccionado_id:
            messagebox.showwarning("Aviso", "Primero guarda el modelo antes de subir fotos.")
            return

        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return

        fotos_actuales = modelo.get("imagenes", [])
        if len(fotos_actuales) >= 3:
            messagebox.showwarning("Aviso", "Ya tienes 3 fotos. Elimina alguna para subir más.")
            return

        # Abrir selector de archivos (múltiple)
        rutas = filedialog.askopenfilenames(
            title="Selecciona fotos del modelo (máx 3)",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if not rutas:
            return

        # Limitar al espacio disponible
        disponibles = 3 - len(fotos_actuales)
        rutas = rutas[:disponibles]

        # Procesar cada una
        carpeta_modelo = obtener_carpeta_imagenes_modelo(self.modelo_seleccionado_id)
        carpeta_modelo.mkdir(parents=True, exist_ok=True)

        nuevas_rutas = list(fotos_actuales)
        errores = []

        for i, ruta_origen in enumerate(rutas):
            # Nombre del archivo: 01.webp, 02.webp, etc.
            # Se basa en el índice global del modelo
            idx_global = len(nuevas_rutas) + 1
            nombre = f"{idx_global:02d}.webp"
            ruta_destino = carpeta_modelo / nombre

            # Generar miniatura solo si es la primera foto
            generar_mini = (idx_global == 1)
            ruta_mini = carpeta_modelo / f"{idx_global:02d}_thumb.webp" if generar_mini else None

            ok, msg, datos = procesar_imagen(
                ruta_origen, ruta_destino,
                tamano_max=800, cuadrado=True,
                generar_miniatura=generar_mini,
                ruta_miniatura=ruta_mini
            )

            if ok:
                # Ruta relativa al proyecto
                ruta_rel = ruta_destino.relative_to(BASE_DIR).as_posix()
                nuevas_rutas.append(ruta_rel)
                print(f"✓ Foto procesada: {ruta_rel} ({datos['peso_kb']} KB)")
            else:
                errores.append(f"{Path(ruta_origen).name}: {msg}")

        # Guardar en JSON
        if nuevas_rutas:
            guardar_imagenes_modelo(self.modelo_seleccionado_id, nuevas_rutas)

        # Refrescar editor
        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)

        # Regenerar catálogo
        regenerar_catalogo()

        # Feedback
        if errores:
            messagebox.showwarning("Algunas fotos fallaron",
                                    "\n".join(errores))
        else:
            messagebox.showinfo("Listo",
                                f"✅ {len(rutas)} foto(s) procesada(s) correctamente.")

    def eliminar_foto_modelo(self, indice):
        """Elimina una foto del modelo."""
        if not self.modelo_seleccionado_id:
            return

        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return

        fotos = modelo.get("imagenes", [])
        if not (0 <= indice < len(fotos)):
            return

        if not messagebox.askyesno("Confirmar", "¿Eliminar esta foto?"):
            return

        # Borrar archivo del disco
        ruta_rel = fotos[indice]
        ruta_abs = BASE_DIR / ruta_rel
        if ruta_abs.exists():
            try:
                ruta_abs.unlink()
            except Exception as e:
                print(f"Error borrando {ruta_abs}: {e}")

        # Si era la primera foto, borrar también la miniatura
        if indice == 0:
            ruta_mini = ruta_abs.parent / (ruta_abs.stem + "_thumb.webp")
            if ruta_mini.exists():
                try:
                    ruta_mini.unlink()
                except Exception:
                    pass

        # Quitar de la lista y renumerar archivos
        fotos.pop(indice)
        self._renumerar_fotos_modelo(fotos)

        # Guardar
        guardar_imagenes_modelo(self.modelo_seleccionado_id, fotos)

        # Refrescar
        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)

        # Regenerar catálogo
        regenerar_catalogo()

    def _renumerar_fotos_modelo(self, fotos):
        """
        Renombra los archivos de fotos para que queden 01, 02, 03...
        sin huecos. Actualiza las rutas en la lista.
        """
        carpeta = obtener_carpeta_imagenes_modelo(self.modelo_seleccionado_id)

        for i, ruta_rel in enumerate(fotos):
            ruta_abs = BASE_DIR / ruta_rel
            if not ruta_abs.exists():
                continue

            nuevo_num = i + 1
            ext = ruta_abs.suffix
            nuevo_nombre = f"{nuevo_num:02d}{ext}"
            nueva_ruta_abs = carpeta / nuevo_nombre

            # Renombrar si hace falta
            if ruta_abs != nueva_ruta_abs:
                try:
                    ruta_abs.rename(nueva_ruta_abs)
                except Exception as e:
                    print(f"Error renombrando {ruta_abs}: {e}")
                    continue

            # Actualizar la lista con la nueva ruta relativa
            fotos[i] = nueva_ruta_abs.relative_to(BASE_DIR).as_posix()

            # Renombrar también la miniatura si es la primera
            if i == 0:
                # Buscar miniatura antigua por nombre anterior
                mini_vieja = ruta_abs.parent / (ruta_abs.stem + "_thumb.webp")
                mini_nueva = carpeta / f"{nuevo_num:02d}_thumb.webp"
                if mini_vieja.exists() and mini_vieja != mini_nueva:
                    try:
                        mini_vieja.rename(mini_nueva)
                    except Exception:
                        pass

    def subir_imagen_linea(self, indice_linea):
        """Sube una imagen para una línea específica."""
        if not self.modelo_seleccionado_id:
            messagebox.showwarning("Aviso", "Primero guarda el modelo.")
            return

        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return

        lineas = modelo.get("lineas", [])
        if not (0 <= indice_linea < len(lineas)):
            return

        # Selector de archivo
        ruta = filedialog.askopenfilename(
            title="Selecciona imagen para la línea",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if not ruta:
            return

        # Nombre del archivo: linea_basic.webp, linea_intermedio.webp, etc.
        nombre_linea = lineas[indice_linea].get("nombre", f"linea_{indice_linea}").lower()
        nombre_limpio = re.sub(r'[^a-z0-9]+', '_', nombre_linea).strip('_')
        nombre_archivo = f"linea_{nombre_limpio}.webp"

        carpeta = obtener_carpeta_imagenes_modelo(self.modelo_seleccionado_id)
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_destino = carpeta / nombre_archivo

        # Procesar imagen
        ok, msg, datos = procesar_imagen(
            ruta, ruta_destino,
            tamano_max=600, cuadrado=True,
            generar_miniatura=False
        )

        if not ok:
            messagebox.showerror("Error", f"No se pudo procesar la imagen:\n\n{msg}")
            return

        ruta_rel = ruta_destino.relative_to(BASE_DIR).as_posix()
        guardar_imagen_linea(self.modelo_seleccionado_id, indice_linea, ruta_rel)

        # Refrescar
        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)

        # Regenerar catálogo
        regenerar_catalogo()

        messagebox.showinfo("Listo",
                            f"✅ Imagen de línea guardada ({datos['peso_kb']} KB).")

    def eliminar_imagen_linea(self, indice_linea):
        """Elimina la imagen de una línea."""
        if not self.modelo_seleccionado_id:
            return

        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return

        lineas = modelo.get("lineas", [])
        if not (0 <= indice_linea < len(lineas)):
            return

        ruta_rel = lineas[indice_linea].get("imagen")
        if not ruta_rel:
            return

        if not messagebox.askyesno("Confirmar", "¿Eliminar la imagen de esta línea?"):
            return

        # Borrar archivo
        ruta_abs = BASE_DIR / ruta_rel
        if ruta_abs.exists():
            try:
                ruta_abs.unlink()
            except Exception as e:
                print(f"Error borrando {ruta_abs}: {e}")

        # Quitar del JSON
        guardar_imagen_linea(self.modelo_seleccionado_id, indice_linea, None)

        # Refrescar
        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)

        # Regenerar catálogo
        regenerar_catalogo()

    # ========================================================
    # SUBIDA DE VIDEO
    # ========================================================
    def subir_video_modelo(self):
        """Abre el selector y procesa un video para el modelo."""
        if not self.modelo_seleccionado_id:
            messagebox.showwarning("Aviso", "Primero guarda el modelo antes de subir video.")
            return

        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return

        # Aviso si ya tiene video
        if modelo.get("video"):
            if not messagebox.askyesno("Ya tiene video",
                                        "Este modelo ya tiene un video.\n\n"
                                        "¿Quieres reemplazarlo?"):
                return

        # Selector de archivos
        ruta = filedialog.askopenfilename(
            title="Selecciona video (máx 5 seg, se recortará si es más largo)",
            filetypes=[
                ("Videos", "*.mp4 *.mov *.avi *.webm *.mkv"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if not ruta:
            return

        # Ruta destino
        ruta_destino = obtener_ruta_video_modelo(self.modelo_seleccionado_id)

        # Procesar
        ok, msg, datos = procesar_video(ruta, ruta_destino)

        if not ok:
            messagebox.showerror("Error", f"No se pudo procesar el video:\n\n{msg}")
            return

        # Guardar ruta relativa
        ruta_rel = ruta_destino.relative_to(BASE_DIR).as_posix()
        guardar_video_modelo(self.modelo_seleccionado_id, ruta_rel)

        # Refrescar editor
        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)

        # Regenerar catálogo
        regenerar_catalogo()

        # Feedback
        info = f"✅ Video procesado correctamente.\n\n"
        info += f"📹 Original: {datos['duracion_original']} seg\n"
        if datos['se_recorta']:
            info += f"✂️ Recortado a: {datos['duracion_final']} seg\n"
        info += f"📦 Peso final: {datos['peso_kb']} KB\n"
        info += f"📐 Dimensiones: {datos['dimensiones'][0]}×{datos['dimensiones'][1]}"

        messagebox.showinfo("Video listo", info)

    def eliminar_video_modelo(self):
        """Elimina el video del modelo."""
        if not self.modelo_seleccionado_id:
            return

        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return

        ruta_rel = modelo.get("video")
        if not ruta_rel:
            return

        if not messagebox.askyesno("Confirmar", "¿Eliminar el video de este modelo?"):
            return

        # Borrar archivo
        ruta_abs = BASE_DIR / ruta_rel
        eliminar_video(ruta_abs)

        # Quitar del JSON
        guardar_video_modelo(self.modelo_seleccionado_id, None)

        # Refrescar
        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)

        # Regenerar catálogo
        regenerar_catalogo()

    # ========================================================
    # CATÁLOGO: ACCIONES
    # ========================================================
    def accion_generar_catalogo(self):
        """Regenera el catálogo HTML manualmente."""
        try:
            exito = regenerar_catalogo()
            if exito:
                messagebox.showinfo("Listo",
                                    "✅ Catálogo regenerado correctamente.\n\n"
                                    "Pulsa '☁️ Subir TODO' para publicarlo en GitHub.")
            else:
                messagebox.showwarning("Aviso", "No hay modelos para generar el catálogo.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el catálogo:\n\n{e}")

    def accion_ver_catalogo(self):
        """Abre el catálogo HTML en el navegador."""
        from config import CATALOGO_INDEX
        import webbrowser

        if CATALOGO_INDEX.exists():
            webbrowser.open(CATALOGO_INDEX.as_uri())
        else:
            # Generarlo primero
            regenerar_catalogo()
            if CATALOGO_INDEX.exists():
                webbrowser.open(CATALOGO_INDEX.as_uri())
            else:
                messagebox.showerror("Error", "No se pudo generar el catálogo.")


# ============================================================
# DIÁLOGO PARA AÑADIR COLOR
# ============================================================
class _DialogoColor(tk.Toplevel):
    """Diálogo simple para añadir un color: nombre + selector."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Añadir color")
        self.configure(bg="#1e293b")
        self.geometry("400x260")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.resultado = None
        self.color_actual = "#FFFFFF"

        tk.Label(self, text="Nombre del color", bg="#1e293b", fg="#f8fafc",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(20, 4))

        self.var_nombre = tk.StringVar()
        entry = tk.Entry(self, textvariable=self.var_nombre, font=("Segoe UI", 11),
                         bg="#334155", fg="#f8fafc", insertbackground="white",
                         relief=tk.FLAT, borderwidth=0)
        entry.pack(fill=tk.X, padx=20, ipady=6)
        entry.focus()

        tk.Label(self, text="Color", bg="#1e293b", fg="#f8fafc",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(16, 4))

        frame_color = tk.Frame(self, bg="#1e293b")
        frame_color.pack(fill=tk.X, padx=20)

        self.canvas_color = tk.Canvas(frame_color, width=60, height=40,
                                       bg=self.color_actual, highlightthickness=0)
        self.canvas_color.pack(side=tk.LEFT)

        tk.Button(frame_color, text="🎨  Elegir color",
                  bg="#0ea5e9", fg="white", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, cursor="hand2", borderwidth=0, highlightthickness=0,
                  command=self._elegir_color).pack(side=tk.LEFT, padx=(10, 0), ipady=8, ipadx=10)

        # Botones inferiores
        frame_btns = tk.Frame(self, bg="#1e293b")
        frame_btns.pack(fill=tk.X, padx=20, pady=20)

        tk.Button(frame_btns, text="Cancelar", bg="#334155", fg="white",
                  font=("Segoe UI", 10), relief=tk.FLAT, cursor="hand2",
                  borderwidth=0, highlightthickness=0,
                  command=self.destroy).pack(side=tk.RIGHT, padx=(6, 0), ipady=6, ipadx=12)

        tk.Button(frame_btns, text="Añadir", bg="#16a34a", fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                  borderwidth=0, highlightthickness=0,
                  command=self._aceptar).pack(side=tk.RIGHT, ipady=6, ipadx=12)

    def _elegir_color(self):
        color = colorchooser.askcolor(color=self.color_actual, parent=self)
        if color and color[1]:
            self.color_actual = color[1]
            self.canvas_color.configure(bg=self.color_actual)

    def _aceptar(self):
        nombre = self.var_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Escribe un nombre para el color.", parent=self)
            return
        self.resultado = {"nombre": nombre, "hex": self.color_actual}
        self.destroy()