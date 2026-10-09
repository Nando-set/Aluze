"""
Capa de datos del catálogo.
Lee y escribe categorías y modelos en archivos JSON.
Gestiona también las rutas de imágenes y videos.
"""
import json
import shutil
from pathlib import Path

from config import (
    CARPETA_CATALOGO, CATALOGO_IMAGENES, CATALOGO_VIDEOS,
    CATALOGO_PAGINAS, CATALOGO_CATEGORIAS, CATALOGO_MODELOS
)


# ============================================================
# INICIALIZACIÓN
# ============================================================
def inicializar_catalogo():
    """Crea las carpetas y archivos base del catálogo si no existen."""
    CARPETA_CATALOGO.mkdir(exist_ok=True)
    CATALOGO_IMAGENES.mkdir(exist_ok=True)
    CATALOGO_VIDEOS.mkdir(exist_ok=True)
    CATALOGO_PAGINAS.mkdir(exist_ok=True)

    if not CATALOGO_CATEGORIAS.exists():
        categorias_default = [
            {"id": "interior", "nombre": "Persianas de interior", "emoji": "🏠"},
            {"id": "exterior", "nombre": "Persianas de exterior", "emoji": "🌤️"},
            {"id": "cortinas", "nombre": "Cortinas", "emoji": "🪟"},
            {"id": "otros", "nombre": "Otros", "emoji": "📦"},
        ]
        _escribir_json(CATALOGO_CATEGORIAS, categorias_default)

    if not CATALOGO_MODELOS.exists():
        _escribir_json(CATALOGO_MODELOS, [])


# ============================================================
# CATEGORÍAS
# ============================================================
def leer_categorias():
    """Devuelve la lista de categorías."""
    if not CATALOGO_CATEGORIAS.exists():
        return []
    return _leer_json(CATALOGO_CATEGORIAS)


def agregar_categoria(id_cat, nombre, emoji="📦"):
    """Añade una nueva categoría."""
    categorias = leer_categorias()
    if any(c["id"] == id_cat for c in categorias):
        return False, "Ya existe una categoría con ese ID."
    categorias.append({"id": id_cat, "nombre": nombre, "emoji": emoji})
    _escribir_json(CATALOGO_CATEGORIAS, categorias)
    return True, "Categoría añadida."


def eliminar_categoria(id_cat):
    """Elimina una categoría. No falla si no existe."""
    categorias = leer_categorias()
    categorias = [c for c in categorias if c["id"] != id_cat]
    _escribir_json(CATALOGO_CATEGORIAS, categorias)


# ============================================================
# MODELOS
# ============================================================
def leer_modelos():
    """Devuelve la lista completa de modelos."""
    if not CATALOGO_MODELOS.exists():
        return []
    return _leer_json(CATALOGO_MODELOS)


def buscar_modelo(id_modelo):
    """Devuelve un modelo por su ID, o None."""
    for m in leer_modelos():
        if m["id"] == id_modelo:
            return m
    return None


def agregar_modelo(modelo):
    """
    Añade un modelo nuevo.
    `modelo` es un dict con las claves:
    id, nombre, categoria, descripcion, imagenes, video, lineas
    """
    modelos = leer_modelos()
    if any(m["id"] == modelo["id"] for m in modelos):
        return False, "Ya existe un modelo con ese ID."
    modelos.append(modelo)
    _escribir_json(CATALOGO_MODELOS, modelos)
    return True, "Modelo añadido."


def actualizar_modelo(id_modelo, modelo_nuevo):
    """Sobrescribe un modelo existente."""
    modelos = leer_modelos()
    for i, m in enumerate(modelos):
        if m["id"] == id_modelo:
            modelos[i] = modelo_nuevo
            _escribir_json(CATALOGO_MODELOS, modelos)
            return True, "Modelo actualizado."
    return False, "Modelo no encontrado."


def eliminar_modelo(id_modelo):
    """
    Elimina un modelo por su ID.
    También borra sus imágenes y video del disco.
    """
    # Borrar archivos del disco
    _borrar_archivos_modelo(id_modelo)

    # Borrar del JSON
    modelos = leer_modelos()
    modelos = [m for m in modelos if m["id"] != id_modelo]
    _escribir_json(CATALOGO_MODELOS, modelos)
    return True, "Modelo eliminado."


# ============================================================
# IMÁGENES Y VIDEO
# ============================================================
def obtener_carpeta_imagenes_modelo(id_modelo):
    """Devuelve el Path a la carpeta de imágenes del modelo."""
    return CATALOGO_IMAGENES / id_modelo


def obtener_ruta_video_modelo(id_modelo):
    """Devuelve el Path donde se guardará el video del modelo."""
    return CATALOGO_VIDEOS / f"{id_modelo}.mp4"


def guardar_imagenes_modelo(id_modelo, lista_rutas):
    """
    Guarda la lista de rutas de imágenes del modelo.
    `lista_rutas` es una lista de strings relativos al proyecto.
    """
    modelo = buscar_modelo(id_modelo)
    if not modelo:
        return False, "Modelo no encontrado."
    modelo["imagenes"] = lista_rutas
    actualizar_modelo(id_modelo, modelo)
    return True, "Imágenes guardadas."


def guardar_video_modelo(id_modelo, ruta_video):
    """Guarda la ruta del video del modelo (o None si no tiene)."""
    modelo = buscar_modelo(id_modelo)
    if not modelo:
        return False, "Modelo no encontrado."
    modelo["video"] = ruta_video
    actualizar_modelo(id_modelo, modelo)
    return True, "Video guardado."


def guardar_imagen_linea(id_modelo, indice_linea, ruta_imagen):
    """Guarda la imagen de una línea específica del modelo."""
    modelo = buscar_modelo(id_modelo)
    if not modelo:
        return False, "Modelo no encontrado."
    lineas = modelo.get("lineas", [])
    if not (0 <= indice_linea < len(lineas)):
        return False, "Línea no encontrada."
    lineas[indice_linea]["imagen"] = ruta_imagen
    actualizar_modelo(id_modelo, modelo)
    return True, "Imagen de línea guardada."


def _borrar_archivos_modelo(id_modelo):
    """Borra del disco las imágenes y el video de un modelo."""
    # Borrar carpeta de imágenes
    carpeta_img = obtener_carpeta_imagenes_modelo(id_modelo)
    if carpeta_img.exists():
        try:
            shutil.rmtree(carpeta_img)
        except Exception:
            pass

    # Borrar video
    video = obtener_ruta_video_modelo(id_modelo)
    if video.exists():
        try:
            video.unlink()
        except Exception:
            pass


# ============================================================
# UTILIDADES INTERNAS
# ============================================================
def _leer_json(ruta):
    with open(ruta, mode='r', encoding='utf-8') as f:
        return json.load(f)


def _escribir_json(ruta, datos):
    with open(ruta, mode='w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)