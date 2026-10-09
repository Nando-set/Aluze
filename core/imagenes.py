"""
Procesamiento de imágenes con Pillow.
- Recorte al centro (para hacerlas cuadradas).
- Redimensión a tamaño máximo.
- Conversión a WebP.
- Generación de miniaturas.
"""
from pathlib import Path
from PIL import Image


# ============================================================
# CONSTANTES
# ============================================================
TAMANO_GRANDE = 800       # px lado mayor para fotos del modelo
TAMANO_MINIATURA = 400    # px lado mayor para miniaturas del grid
TAMANO_LINEA = 600        # px lado mayor para imágenes de línea
CALIDAD_WEBP = 85         # calidad de compresión (0-100)
PESO_MAX_KB = 150         # si supera esto, se comprime más


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================
def procesar_imagen(ruta_origen, ruta_destino, tamano_max=TAMANO_GRANDE,
                     cuadrado=True, generar_miniatura=False, ruta_miniatura=None):
    """
    Procesa una imagen: recorta, redimensiona, convierte a WebP y guarda.

    Args:
        ruta_origen: Path de la imagen original.
        ruta_destino: Path donde guardar la imagen procesada (.webp).
        tamano_max: Tamaño máximo del lado mayor (800 por defecto).
        cuadrado: Si True, recorta al centro para hacerla cuadrada.
        generar_miniatura: Si True, genera también una miniatura.
        ruta_miniatura: Path donde guardar la miniatura.

    Returns:
        (ok: bool, mensaje: str, datos: dict)
        datos incluye 'peso_kb' y 'dimensiones'.
    """
    try:
        # 1. Abrir imagen
        img = Image.open(ruta_origen)

        # 2. Convertir a RGB (para WebP; PNG con transparencia se aplana)
        if img.mode in ("RGBA", "LA", "P"):
            fondo = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            fondo.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = fondo
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 3. Recortar al centro (si cuadrado=True)
        if cuadrado:
            img = _recortar_cuadrado(img)

        # 4. Redimensionar si es más grande que tamano_max
        if img.width > tamano_max or img.height > tamano_max:
            img.thumbnail((tamano_max, tamano_max), Image.LANCZOS)

        # 5. Crear carpeta destino si no existe
        Path(ruta_destino).parent.mkdir(parents=True, exist_ok=True)

        # 6. Guardar como WebP (con compresión adaptativa)
        peso_kb = _guardar_webp_optimizado(img, ruta_destino, CALIDAD_WEBP)

        # 7. Generar miniatura si se pide
        if generar_miniatura and ruta_miniatura:
            img_mini = img.copy()
            if img_mini.width > TAMANO_MINIATURA or img_mini.height > TAMANO_MINIATURA:
                img_mini.thumbnail((TAMANO_MINIATURA, TAMANO_MINIATURA), Image.LANCZOS)
            Path(ruta_miniatura).parent.mkdir(parents=True, exist_ok=True)
            _guardar_webp_optimizado(img_mini, ruta_miniatura, CALIDAD_WEBP)

        return True, "OK", {
            "peso_kb": peso_kb,
            "dimensiones": (img.width, img.height),
            "ruta": str(ruta_destino),
        }

    except FileNotFoundError:
        return False, f"No se encontró el archivo: {ruta_origen}", None
    except Exception as e:
        return False, f"Error procesando imagen: {e}", None


def procesar_imagen_linea(ruta_origen, ruta_destino):
    """Atajo para imágenes de línea (600x600)."""
    return procesar_imagen(ruta_origen, ruta_destino,
                            tamano_max=TAMANO_LINEA,
                            cuadrado=True,
                            generar_miniatura=False)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def _recortar_cuadrado(img):
    """Recorta la imagen al centro para hacerla cuadrada."""
    ancho, alto = img.size
    if ancho == alto:
        return img

    lado = min(ancho, alto)
    izquierda = (ancho - lado) // 2
    arriba = (alto - lado) // 2
    return img.crop((izquierda, arriba, izquierda + lado, arriba + lado))


def _guardar_webp_optimizado(img, ruta, calidad_inicial):
    """
    Guarda la imagen como WebP. Si supera PESO_MAX_KB, reduce calidad
    progresivamente hasta que quepa.
    Devuelve el peso final en KB.
    """
    calidad = calidad_inicial
    while calidad >= 40:
        img.save(ruta, "WEBP", quality=calidad, method=6)
        peso_kb = Path(ruta).stat().st_size / 1024
        if peso_kb <= PESO_MAX_KB:
            break
        calidad -= 10

    return round(peso_kb, 1)


def obtener_info_imagen(ruta):
    """Devuelve info básica de una imagen sin procesarla."""
    try:
        img = Image.open(ruta)
        return {
            "width": img.width,
            "height": img.height,
            "formato": img.format,
            "peso_kb": round(Path(ruta).stat().st_size / 1024, 1),
        }
    except Exception as e:
        return None