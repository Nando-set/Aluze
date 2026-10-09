"""
Botones modernos con esquinas redondeadas para Tkinter.
Se implementan con Canvas porque Tkinter no soporta redondeo nativo.
"""
import tkinter as tk


# ============================================================
# PALETA DE COLORES
# ============================================================
COLOR_FONDO_SIDEBAR = "#1e293b"      # fondo del sidebar (para el borde exterior)
COLOR_BOTON = "#f8fafc"               # blanco perla del botón
COLOR_BOTON_HOVER = "#e2e8f0"         # gris muy claro al pasar el ratón
COLOR_TEXTO = "#334155"               # gris oscuro del texto
COLOR_BOTON_PELIGRO = "#f1f5f9"       # gris muy claro del botón peligroso
COLOR_BOTON_PELIGRO_HOVER = "#fee2e2" # rosa muy tenue al hover
COLOR_TEXTO_PELIGRO = "#b91c1c"       # rojo tenue del texto


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================
def crear_boton_moderno(parent,
                        texto,
                        comando,
                        bg=COLOR_BOTON,
                        fg=COLOR_TEXTO,
                        bg_hover=COLOR_BOTON_HOVER,
                        fuente=("Segoe UI", 10, "bold"),
                        ancho=None,
                        altura=36,
                        radio=12,
                        padding_x=16,
                        color_borde=None):
    """
    Crea un botón moderno con esquinas redondeadas usando Canvas.

    Args:
        parent: widget padre
        texto: texto del botón
        comando: función a ejecutar al hacer clic
        bg: color de fondo (por defecto blanco perla)
        fg: color del texto
        bg_hover: color al pasar el ratón
        fuente: tupla de fuente
        ancho: ancho en px (None = calcular automáticamente)
        altura: alto en px
        radio: radio de las esquinas redondeadas
        padding_x: espacio horizontal dentro del botón
        color_borde: color del borde (None = sin borde)

    Returns:
        Un frame contenedor con el botón dentro.
    """
    # Frame contenedor (para que se vea el padding del sidebar)
    contenedor = tk.Frame(parent, bg=parent.cget("bg"), height=altura)
    contenedor.pack_propagate(False)

    canvas = tk.Canvas(contenedor,
                       bg=parent.cget("bg"),
                       highlightthickness=0,
                       bd=0,
                       height=altura)

    # Calcular ancho
    if ancho is None:
        # Ancho automático basado en el texto (aproximado)
        canvas.update_idletasks()
        try:
            import tkinter.font as tkfont
            f = tkfont.Font(family=fuente[0], size=fuente[1], weight=fuente[2] if len(fuente) > 2 else "normal")
            ancho_texto = f.measure(texto)
        except Exception:
            ancho_texto = len(texto) * 8
        ancho = ancho_texto + padding_x * 2

    canvas.configure(width=ancho)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Dibujar el rectángulo redondeado
    def dibujar(color_fondo):
        canvas.delete("all")
        _dibujar_rectangulo_redondeado(
            canvas, 0, 0, ancho, altura, radio,
            color_fondo, color_borde
        )
        canvas.create_text(
            ancho // 2, altura // 2,
            text=texto,
            fill=fg,
            font=fuente,
            anchor="center"
        )

    dibujar(bg)

    # ---- Eventos ----
    def on_enter(e):
        dibujar(bg_hover)
        canvas.configure(cursor="hand2")

    def on_leave(e):
        dibujar(bg)
        canvas.configure(cursor="")

    def on_click(e):
        comando()

    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Button-1>", on_click)

    return contenedor


# ============================================================
# VARIANTES
# ============================================================
def boton_principal(parent, texto, comando, **kwargs):
    """Botón principal (más grande, ligeramente más énfasis)."""
    return crear_boton_moderno(
        parent, texto, comando,
        fuente=("Segoe UI", 11, "bold"),
        altura=42,
        radio=14,
        padding_x=20,
        **kwargs
    )


def boton_secundario(parent, texto, comando, **kwargs):
    """Botón secundario (tamaño normal)."""
    return crear_boton_moderno(
        parent, texto, comando,
        fuente=("Segoe UI", 9, "bold"),
        altura=34,
        radio=10,
        padding_x=12,
        **kwargs
    )


def boton_peligro(parent, texto, comando, **kwargs):
    """Botón peligroso (rojo tenue)."""
    return crear_boton_moderno(
        parent, texto, comando,
        bg=COLOR_BOTON_PELIGRO,
        fg=COLOR_TEXTO_PELIGRO,
        bg_hover=COLOR_BOTON_PELIGRO_HOVER,
        fuente=("Segoe UI", 9, "bold"),
        altura=34,
        radio=10,
        padding_x=12,
        **kwargs
    )


# ============================================================
# UTILIDAD INTERNA
# ============================================================
def _dibujar_rectangulo_redondeado(canvas, x1, y1, x2, y2, radio,
                                     relleno, borde=None):
    """
    Dibuja un rectángulo con esquinas redondeadas en un Canvas.
    Usa polígonos suavizados.
    """
    puntos = [
        x1 + radio, y1,
        x2 - radio, y1,
        x2, y1,
        x2, y1 + radio,
        x2, y2 - radio,
        x2, y2,
        x2 - radio, y2,
        x1 + radio, y2,
        x1, y2,
        x1, y2 - radio,
        x1, y1 + radio,
        x1, y1,
    ]
    if borde:
        canvas.create_polygon(
            puntos,
            fill=relleno,
            outline=borde,
            width=1,
            smooth=True,
            splinesteps=36
        )
    else:
        canvas.create_polygon(
            puntos,
            fill=relleno,
            outline="",
            smooth=True,
            splinesteps=36
        )