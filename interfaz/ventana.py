"""
Ventana principal de Aluze.
Estructura: logo arriba + pestañas + contenido + botón global abajo.
"""
import shutil
import re
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from pathlib import Path
from datetime import datetime

from config import (
    CARPETA_COTIZACIONES, CARPETA_ASSETS,
    LOGO_SVG, LOGO_PNG, LOGO_PNG_CLARO,
    INDEX_HTML, DB_FILE, URL_BASE, BASE_DIR
)

from core.datos import (
    inicializar_csv, leer_registros, agregar_registro, eliminar_registro_por_id,
    buscar_registro_por_id, actualizar_registro
)
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
    # GUARDAR COTIZACIÓN (con campos nuevos)
    # ========================================================
    def guardar_cotizacion(self):
        # Leer todos los campos
        cliente = self.entries["Nombre del Cliente"].get().strip()
        domicilio = self.entries["Domicilio"].get().strip()
        telefono = self.entries["Teléfono Celular"].get().strip()
        concepto = self.entries["Concepto / Sistema"].get().strip()
        cotizacion = self.entries["Detalles de Cotización"].get("1.0", tk.END).strip()
        monto = self.entries["Monto Aproximado"].get().strip()
        fecha_pautada = self.entries["FechaPautada"].get().strip()
        hora_pautada = self.entries["HoraPautada"].get().strip()
        notas_cliente = self.entries["NotasCliente"].get("1.0", tk.END).strip()
        notas_internas = self.entries["NotasInternas"].get("1.0", tk.END).strip()

        # Validaciones
        if not cliente or not telefono:
            messagebox.showerror("Error", "El nombre del cliente y el teléfono son obligatorios.")
            return

        # Validar formato de fecha pautada si se puso
        if fecha_pautada:
            try:
                datetime.strptime(fecha_pautada, "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Error",
                                     "La fecha pautada debe tener formato dd/mm/aaaa.\n\n"
                                     "Ejemplo: 15/10/2026")
                return

        # Validar hora si se puso (solo si hay fecha)
        if hora_pautada and not fecha_pautada:
            messagebox.showerror("Error", "Si pones hora, también debes poner fecha pautada.")
            return

        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        id_reg = int(datetime.now().timestamp() * 1000)

        try:
            ruta_relativa = generar_html(
                id_reg, cliente, domicilio, telefono, concepto,
                cotizacion, monto, notas_cliente, fecha,
                fecha_pautada=fecha_pautada,
                hora_pautada=hora_pautada,
                notas_internas=notas_internas
            )
            link_individual = f"{URL_BASE}{ruta_relativa}"

            # Fila completa (14 columnas)
            fila = [
                id_reg, fecha, cliente, domicilio, telefono,
                concepto, cotizacion, monto,
                fecha_pautada, hora_pautada,
                notas_cliente, notas_internas,
                ruta_relativa, link_individual
            ]
            agregar_registro(fila)

            regenerar_index()
            self.limpiar_formulario()
            cargar_registros(self)

            if self.subir_auto.get():
                exito, msg = subir_a_github()
                if not exito:
                    messagebox.showwarning("GitHub",
                                           f"Guardado local OK, pero falló la subida:\n\n{msg}")
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

    # ========================================================
    # EDITAR COTIZACIÓN (modal)
    # ========================================================
    def editar_cotizacion(self, id_registro):
        """Abre un modal para editar la cotización."""
        registro = buscar_registro_por_id(id_registro)
        if not registro:
            messagebox.showerror("Error", "No se encontró el registro.")
            return

        VentanaEditar(self, id_registro, registro)

    # ========================================================
    # ELIMINAR COTIZACIÓN
    # ========================================================
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

    # ========================================================
    # REGENERAR TODAS LAS TARJETAS
    # ========================================================
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
                id_reg = reg[0]
                fecha = reg[1]
                cliente = reg[2]
                domicilio = reg[3]
                telefono = reg[4]
                concepto = reg[5]
                cotizacion = reg[6]
                monto = reg[7]
                fecha_pautada = reg[8] if len(reg) > 8 else ""
                hora_pautada = reg[9] if len(reg) > 9 else ""
                notas_cliente = reg[10] if len(reg) > 10 else ""
                notas_internas = reg[11] if len(reg) > 11 else ""

                try:
                    generar_html(
                        id_reg, cliente, domicilio, telefono, concepto,
                        cotizacion, monto, notas_cliente, fecha,
                        fecha_pautada=fecha_pautada,
                        hora_pautada=hora_pautada,
                        notas_internas=notas_internas
                    )
                except Exception as e:
                    print(f"Error regenerando {cliente}: {e}")

            regenerar_index()

            messagebox.showinfo("Listo",
                                f"✅ {total} tarjetas regeneradas.\n\n"
                                "Pulsa '☁️ Subir' para actualizar la nube.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo regenerar:\n\n{e}")

    # ========================================================
    # BORRAR TODO
    # ========================================================
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

    # ========================================================
    # GITHUB
    # ========================================================
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

    # ========================================================
    # CATÁLOGO: ACCIONES
    # ========================================================
    def refrescar_arbol_catalogo(self):
        cat_panel.refrescar_arbol(self)

    def nuevo_modelo_catalogo(self):
        cat_panel._limpiar_editor(self)
        messagebox.showinfo("Nuevo modelo",
                            "Rellena los campos y pulsa 'Guardar modelo'.")

    def guardar_modelo_catalogo(self):
        nombre = self.var_nombre.get().strip()
        categoria_visible = self.var_categoria.get().strip()
        descripcion = self.text_descripcion.get("1.0", tk.END).strip()

        if not nombre:
            messagebox.showerror("Error", "El nombre del modelo es obligatorio.")
            return
        if not categoria_visible:
            messagebox.showerror("Error", "Selecciona una categoría.")
            return

        cat_id = None
        for c in self.categorias_cache:
            if f"{c['emoji']} {c['nombre']}" == categoria_visible:
                cat_id = c["id"]
                break
        if not cat_id:
            messagebox.showerror("Error", "Categoría no encontrada.")
            return

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

        if self.modelo_seleccionado_id:
            # Conservar imágenes, video y líneas existentes
            existente = buscar_modelo(self.modelo_seleccionado_id)
            if existente:
                modelo["imagenes"] = existente.get("imagenes", [])
                modelo["video"] = existente.get("video")
                modelo["lineas"] = existente.get("lineas", [])
            ok, msg = actualizar_modelo(self.modelo_seleccionado_id, modelo)
        else:
            ok, msg = agregar_modelo(modelo)

        if ok:
            messagebox.showinfo("Éxito", msg)
            self.refrescar_arbol_catalogo()
            cat_panel._limpiar_editor(self)
            regenerar_catalogo()
        else:
            messagebox.showerror("Error", msg)

    def eliminar_modelo_catalogo(self):
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

    def accion_generar_catalogo(self):
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
        from config import CATALOGO_INDEX
        if CATALOGO_INDEX.exists():
            webbrowser.open(CATALOGO_INDEX.as_uri())
        else:
            regenerar_catalogo()
            if CATALOGO_INDEX.exists():
                webbrowser.open(CATALOGO_INDEX.as_uri())
            else:
                messagebox.showerror("Error", "No se pudo generar el catálogo.")

    # ========================================================
    # SUBIDA DE IMÁGENES
    # ========================================================
    def subir_fotos_modelo(self):
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

        rutas = filedialog.askopenfilenames(
            title="Selecciona fotos del modelo (máx 3)",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if not rutas:
            return

        disponibles = 3 - len(fotos_actuales)
        rutas = rutas[:disponibles]

        carpeta_modelo = obtener_carpeta_imagenes_modelo(self.modelo_seleccionado_id)
        carpeta_modelo.mkdir(parents=True, exist_ok=True)

        nuevas_rutas = list(fotos_actuales)
        errores = []

        for i, ruta_origen in enumerate(rutas):
            idx_global = len(nuevas_rutas) + 1
            nombre = f"{idx_global:02d}.webp"
            ruta_destino = carpeta_modelo / nombre

            generar_mini = (idx_global == 1)
            ruta_mini = carpeta_modelo / f"{idx_global:02d}_thumb.webp" if generar_mini else None

            ok, msg, datos = procesar_imagen(
                ruta_origen, ruta_destino,
                tamano_max=800, cuadrado=True,
                generar_miniatura=generar_mini,
                ruta_miniatura=ruta_mini
            )

            if ok:
                ruta_rel = ruta_destino.relative_to(BASE_DIR).as_posix()
                nuevas_rutas.append(ruta_rel)
                print(f"✓ Foto procesada: {ruta_rel} ({datos['peso_kb']} KB)")
            else:
                errores.append(f"{Path(ruta_origen).name}: {msg}")

        if nuevas_rutas:
            guardar_imagenes_modelo(self.modelo_seleccionado_id, nuevas_rutas)

        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)
        regenerar_catalogo()

        if errores:
            messagebox.showwarning("Algunas fotos fallaron", "\n".join(errores))
        else:
            messagebox.showinfo("Listo",
                                f"✅ {len(rutas)} foto(s) procesada(s) correctamente.")

    def eliminar_foto_modelo(self, indice):
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

        ruta_rel = fotos[indice]
        ruta_abs = BASE_DIR / ruta_rel
        if ruta_abs.exists():
            try:
                ruta_abs.unlink()
            except Exception as e:
                print(f"Error borrando {ruta_abs}: {e}")

        if indice == 0:
            ruta_mini = ruta_abs.parent / (ruta_abs.stem + "_thumb.webp")
            if ruta_mini.exists():
                try:
                    ruta_mini.unlink()
                except Exception:
                    pass

        fotos.pop(indice)
        self._renumerar_fotos_modelo(fotos)
        guardar_imagenes_modelo(self.modelo_seleccionado_id, fotos)

        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)
        regenerar_catalogo()

    def _renumerar_fotos_modelo(self, fotos):
        carpeta = obtener_carpeta_imagenes_modelo(self.modelo_seleccionado_id)
        for i, ruta_rel in enumerate(fotos):
            ruta_abs = BASE_DIR / ruta_rel
            if not ruta_abs.exists():
                continue
            nuevo_num = i + 1
            ext = ruta_abs.suffix
            nuevo_nombre = f"{nuevo_num:02d}{ext}"
            nueva_ruta_abs = carpeta / nuevo_nombre
            if ruta_abs != nueva_ruta_abs:
                try:
                    ruta_abs.rename(nueva_ruta_abs)
                except Exception as e:
                    print(f"Error renombrando {ruta_abs}: {e}")
                    continue
            fotos[i] = nueva_ruta_abs.relative_to(BASE_DIR).as_posix()
            if i == 0:
                mini_vieja = ruta_abs.parent / (ruta_abs.stem + "_thumb.webp")
                mini_nueva = carpeta / f"{nuevo_num:02d}_thumb.webp"
                if mini_vieja.exists() and mini_vieja != mini_nueva:
                    try:
                        mini_vieja.rename(mini_nueva)
                    except Exception:
                        pass

    def subir_imagen_linea(self, indice_linea):
        if not self.modelo_seleccionado_id:
            messagebox.showwarning("Aviso", "Primero guarda el modelo.")
            return
        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return
        lineas = modelo.get("lineas", [])
        if not (0 <= indice_linea < len(lineas)):
            return

        ruta = filedialog.askopenfilename(
            title="Selecciona imagen para la línea",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if not ruta:
            return

        nombre_linea = lineas[indice_linea].get("nombre", f"linea_{indice_linea}").lower()
        nombre_limpio = re.sub(r'[^a-z0-9]+', '_', nombre_linea).strip('_')
        nombre_archivo = f"linea_{nombre_limpio}.webp"

        carpeta = obtener_carpeta_imagenes_modelo(self.modelo_seleccionado_id)
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_destino = carpeta / nombre_archivo

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

        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)
        regenerar_catalogo()

        messagebox.showinfo("Listo",
                            f"✅ Imagen de línea guardada ({datos['peso_kb']} KB).")

    def eliminar_imagen_linea(self, indice_linea):
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

        ruta_abs = BASE_DIR / ruta_rel
        if ruta_abs.exists():
            try:
                ruta_abs.unlink()
            except Exception as e:
                print(f"Error borrando {ruta_abs}: {e}")

        guardar_imagen_linea(self.modelo_seleccionado_id, indice_linea, None)
        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)
        regenerar_catalogo()

    # ========================================================
    # LÍNEAS Y COLORES
    # ========================================================
    def agregar_linea_modelo(self, nombre_linea):
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
        regenerar_catalogo()

    def eliminar_linea_modelo(self, indice):
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
            regenerar_catalogo()

    def mover_linea(self, indice, direccion):
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
            regenerar_catalogo()

    def editar_descripcion_linea(self, indice, texto):
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
        if not self.modelo_seleccionado_id:
            return
        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return
        lineas = modelo.get("lineas", [])
        if not (0 <= indice_linea < len(lineas)):
            return

        dialogo = _DialogoColor(self.root)
        self.root.wait_window(dialogo)
        if not dialogo.resultado:
            return

        lineas[indice_linea].setdefault("colores", []).append(dialogo.resultado)
        actualizar_modelo(self.modelo_seleccionado_id, modelo)
        cat_panel._cargar_modelo_en_editor(self, modelo)
        regenerar_catalogo()

    def eliminar_color_linea(self, indice_linea, indice_color):
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
                regenerar_catalogo()

    # ========================================================
    # VIDEO
    # ========================================================
    def subir_video_modelo(self):
        if not self.modelo_seleccionado_id:
            messagebox.showwarning("Aviso", "Primero guarda el modelo antes de subir video.")
            return
        modelo = buscar_modelo(self.modelo_seleccionado_id)
        if not modelo:
            return
        if modelo.get("video"):
            if not messagebox.askyesno("Ya tiene video",
                                        "Este modelo ya tiene un video.\n\n"
                                        "¿Quieres reemplazarlo?"):
                return

        ruta = filedialog.askopenfilename(
            title="Selecciona video (máx 5 seg, se recortará si es más largo)",
            filetypes=[
                ("Videos", "*.mp4 *.mov *.avi *.webm *.mkv"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if not ruta:
            return

        ruta_destino = obtener_ruta_video_modelo(self.modelo_seleccionado_id)
        ok, msg, datos = procesar_video(ruta, ruta_destino)

        if not ok:
            messagebox.showerror("Error", f"No se pudo procesar el video:\n\n{msg}")
            return

        ruta_rel = ruta_destino.relative_to(BASE_DIR).as_posix()
        guardar_video_modelo(self.modelo_seleccionado_id, ruta_rel)

        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)
        regenerar_catalogo()

        info = f"✅ Video procesado correctamente.\n\n"
        info += f"📹 Original: {datos['duracion_original']} seg\n"
        if datos['se_recorta']:
            info += f"✂️ Recortado a: {datos['duracion_final']} seg\n"
        info += f"📦 Peso final: {datos['peso_kb']} KB\n"
        info += f"📐 Dimensiones: {datos['dimensiones'][0]}×{datos['dimensiones'][1]}"

        messagebox.showinfo("Video listo", info)

    def eliminar_video_modelo(self):
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

        ruta_abs = BASE_DIR / ruta_rel
        eliminar_video(ruta_abs)
        guardar_video_modelo(self.modelo_seleccionado_id, None)

        modelo_actualizado = buscar_modelo(self.modelo_seleccionado_id)
        cat_panel._cargar_modelo_en_editor(self, modelo_actualizado)
        regenerar_catalogo()


# ============================================================
# MODAL DE EDICIÓN
# ============================================================
class VentanaEditar(tk.Toplevel):
    """Modal para editar una cotización existente."""

    def __init__(self, parent_app, id_registro, registro):
        super().__init__(parent_app.root)
        self.app = parent_app
        self.id_registro = id_registro
        self.registro = registro

        self.title(f"✏️ Editar cotización - {registro[2]}")
        self.configure(bg="#1e293b")
        self.geometry("700x750")
        self.minsize(600, 600)
        self.transient(parent_app.root)
        self.grab_set()

        # Scroll
        canvas = tk.Canvas(self, bg="#1e293b", highlightthickness=0, bd=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg="#1e293b")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Título
        tk.Label(frame, text="EDITAR COTIZACIÓN", bg="#1e293b", fg="#f8fafc",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(15, 15), padx=20)

        self.entries_edit = {}

        def campo(label, valor, multiline=False, height=3):
            tk.Label(frame, text=label, bg="#1e293b", fg="#94a3b8",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(8, 2))
            if multiline:
                txt = tk.Text(frame, height=height, font=("Segoe UI", 10),
                              bg="#334155", fg="#f8fafc", insertbackground="white",
                              relief=tk.FLAT, borderwidth=0)
                txt.pack(fill=tk.X, padx=20)
                txt.insert("1.0", valor)
                return txt
            else:
                ent = tk.Entry(frame, font=("Segoe UI", 10), bg="#334155",
                               fg="#f8fafc", insertbackground="white",
                               relief=tk.FLAT, borderwidth=0)
                ent.pack(fill=tk.X, padx=20, ipady=5)
                ent.insert(0, valor)
                return ent

        self.entries_edit["cliente"] = campo("Cliente *", registro[2])
        self.entries_edit["domicilio"] = campo("Domicilio", registro[3])
        self.entries_edit["telefono"] = campo("Teléfono *", registro[4])
        self.entries_edit["concepto"] = campo("Concepto / Sistema", registro[5])
        self.entries_edit["cotizacion"] = campo("Detalles de Cotización", registro[6], multiline=True, height=4)
        self.entries_edit["monto"] = campo("Monto Aproximado", registro[7])

        # Visita pautada (en 2 columnas)
        tk.Label(frame, text="📅 VISITA PAUTADA (opcional)", bg="#1e293b",
                 fg="#973359", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(14, 4))

        frame_fecha = tk.Frame(frame, bg="#1e293b")
        frame_fecha.pack(fill=tk.X, padx=20)
        frame_fecha.columnconfigure(0, weight=3)
        frame_fecha.columnconfigure(1, weight=2)

        col_f = tk.Frame(frame_fecha, bg="#1e293b")
        col_f.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        tk.Label(col_f, text="Fecha (dd/mm/aaaa)", bg="#1e293b",
                 fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        e_f = tk.Entry(col_f, font=("Segoe UI", 10), bg="#334155",
                       fg="#f8fafc", insertbackground="white",
                       relief=tk.FLAT, borderwidth=0)
        e_f.pack(fill=tk.X, ipady=5)
        e_f.insert(0, registro[8] if len(registro) > 8 else "")
        self.entries_edit["fecha_pautada"] = e_f

        col_h = tk.Frame(frame_fecha, bg="#1e293b")
        col_h.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        tk.Label(col_h, text="Hora (HH:MM)", bg="#1e293b",
                 fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        e_h = tk.Entry(col_h, font=("Segoe UI", 10), bg="#334155",
                       fg="#f8fafc", insertbackground="white",
                       relief=tk.FLAT, borderwidth=0)
        e_h.pack(fill=tk.X, ipady=5)
        e_h.insert(0, registro[9] if len(registro) > 9 else "")
        self.entries_edit["hora_pautada"] = e_h

        # Notas
        tk.Label(frame, text="📝 NOTAS", bg="#1e293b",
                 fg="#973359", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(14, 4))

        self.entries_edit["notas_cliente"] = campo("Notas del cliente",
                                                     registro[10] if len(registro) > 10 else "",
                                                     multiline=True, height=3)
        self.entries_edit["notas_internas"] = campo("Notas internas (no se ven en la tarjeta)",
                                                      registro[11] if len(registro) > 11 else "",
                                                      multiline=True, height=2)

        # Botones
        frame_btns = tk.Frame(frame, bg="#1e293b")
        frame_btns.pack(fill=tk.X, padx=20, pady=20)

        tk.Button(frame_btns, text="Cancelar", bg="#334155", fg="white",
                  font=("Segoe UI", 10), relief=tk.FLAT, cursor="hand2",
                  borderwidth=0, highlightthickness=0,
                  command=self.destroy).pack(side=tk.RIGHT, padx=(6, 0), ipady=8, ipadx=16)

        tk.Button(frame_btns, text="💾  Guardar cambios", bg="#16a34a", fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                  borderwidth=0, highlightthickness=0,
                  command=self._guardar).pack(side=tk.RIGHT, ipady=8, ipadx=16)

        tk.Button(frame_btns, text="☁️  Guardar y subir", bg="#0ea5e9", fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2",
                  borderwidth=0, highlightthickness=0,
                  command=lambda: self._guardar(subir=True)).pack(side=tk.RIGHT, padx=(0, 6), ipady=8, ipadx=16)

    def _guardar(self, subir=False):
        # Leer valores
        cliente = self.entries_edit["cliente"].get().strip()
        domicilio = self.entries_edit["domicilio"].get().strip()
        telefono = self.entries_edit["telefono"].get().strip()
        concepto = self.entries_edit["concepto"].get().strip()
        cotizacion = self.entries_edit["cotizacion"].get("1.0", tk.END).strip()
        monto = self.entries_edit["monto"].get().strip()
        fecha_pautada = self.entries_edit["fecha_pautada"].get().strip()
        hora_pautada = self.entries_edit["hora_pautada"].get().strip()
        notas_cliente = self.entries_edit["notas_cliente"].get("1.0", tk.END).strip()
        notas_internas = self.entries_edit["notas_internas"].get("1.0", tk.END).strip()

        if not cliente or not telefono:
            messagebox.showerror("Error", "Cliente y teléfono son obligatorios.", parent=self)
            return

        if fecha_pautada:
            try:
                datetime.strptime(fecha_pautada, "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Error",
                                     "La fecha pautada debe tener formato dd/mm/aaaa.",
                                     parent=self)
                return

        # Regenerar tarjeta HTML
        reg = self.registro
        id_reg = reg[0]
        fecha_creacion = reg[1]

        try:
            ruta_relativa = generar_html(
                id_reg, cliente, domicilio, telefono, concepto,
                cotizacion, monto, notas_cliente, fecha_creacion,
                fecha_pautada=fecha_pautada,
                hora_pautada=hora_pautada,
                notas_internas=notas_internas
            )
            link_individual = f"{URL_BASE}{ruta_relativa}"

            nueva_fila = [
                id_reg, fecha_creacion, cliente, domicilio, telefono,
                concepto, cotizacion, monto,
                fecha_pautada, hora_pautada,
                notas_cliente, notas_internas,
                ruta_relativa, link_individual
            ]
            actualizar_registro(id_reg, nueva_fila)

            regenerar_index()
            cargar_registros(self.app)

            if subir:
                exito, msg = subir_a_github()
                if not exito:
                    messagebox.showwarning("GitHub",
                                           f"Guardado local OK, pero falló la subida:\n\n{msg}",
                                           parent=self)

            messagebox.showinfo("Listo", "✅ Cotización actualizada.", parent=self)
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar:\n\n{e}", parent=self)


# ============================================================
# DIÁLOGO PARA AÑADIR COLOR
# ============================================================
from tkinter import colorchooser


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