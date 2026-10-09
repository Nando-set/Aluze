"""
Procesamiento de video con FFmpeg.
- Detectar duración.
- Recortar a máximo N segundos.
- Convertir a MP4 H.264.
- Redimensionar a 720p máximo.
- Comprimir hasta tamaño objetivo.
"""
import subprocess
import json
from pathlib import Path


# ============================================================
# CONSTANTES
# ============================================================
DURACION_MAX = 5          # segundos
ALTO_MAX = 720            # 720p
PESO_OBJETIVO_KB = 500    # objetivo de peso
BITRATE_INICIAL = "800k"  # bitrate inicial (se reduce si pesa mucho)
BITRATE_MINIMO = "200k"


# ============================================================
# VERIFICACIÓN
# ============================================================
def verificar_ffmpeg():
    """Devuelve True si ffmpeg y ffprobe están disponibles."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# ============================================================
# INFO DEL VIDEO
# ============================================================
def obtener_info_video(ruta):
    """
    Devuelve un dict con duración, ancho, alto, codec.
    None si hay error.
    """
    try:
        resultado = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                str(ruta)
            ],
            capture_output=True,
            check=True,
        )
        info = json.loads(resultado.stdout)

        # Buscar el stream de video
        stream_video = None
        for s in info.get("streams", []):
            if s.get("codec_type") == "video":
                stream_video = s
                break

        if not stream_video:
            return None

        return {
            "duracion": float(info["format"].get("duration", 0)),
            "ancho": int(stream_video.get("width", 0)),
            "alto": int(stream_video.get("height", 0)),
            "codec": stream_video.get("codec_name", "desconocido"),
            "peso_kb": round(int(info["format"].get("size", 0)) / 1024, 1),
        }
    except Exception as e:
        print(f"Error analizando video: {e}")
        return None


# ============================================================
# PROCESAMIENTO PRINCIPAL
# ============================================================
def procesar_video(ruta_origen, ruta_destino):
    """
    Procesa un video: recorta, redimensiona, comprime y guarda como MP4.

    Returns:
        (ok: bool, mensaje: str, datos: dict)
    """
    try:
        # 1. Verificar que ffmpeg está instalado
        if not verificar_ffmpeg():
            return False, "FFmpeg no está instalado o no está en el PATH.", None

        # 2. Obtener info del video original
        info = obtener_info_video(ruta_origen)
        if not info:
            return False, "No se pudo leer el video.", None

        duracion_original = info["duracion"]
        se_recorta = duracion_original > DURACION_MAX

        # 3. Crear carpeta destino
        Path(ruta_destino).parent.mkdir(parents=True, exist_ok=True)

        # 4. Procesar con compresión adaptativa
        peso_kb, exito = _comprimir_con_objetivo(
            ruta_origen, ruta_destino,
            duracion=DURACION_MAX if se_recorta else duracion_original,
            alto_max=ALTO_MAX,
            peso_objetivo_kb=PESO_OBJETIVO_KB,
        )

        if not exito:
            return False, "No se pudo comprimir el video.", None

        # 5. Obtener info del video final
        info_final = obtener_info_video(ruta_destino)

        return True, "OK", {
            "duracion_original": round(duracion_original, 2),
            "duracion_final": round(info_final["duracion"], 2) if info_final else DURACION_MAX,
            "se_recorta": se_recorta,
            "peso_kb": peso_kb,
            "dimensiones": (info_final["ancho"], info_final["alto"]) if info_final else (0, 0),
            "ruta": str(ruta_destino),
        }

    except Exception as e:
        return False, f"Error procesando video: {e}", None


# ============================================================
# COMPRESIÓN ADAPTATIVA
# ============================================================
def _comprimir_con_objetivo(ruta_origen, ruta_destino, duracion,
                             alto_max, peso_objetivo_kb):
    """
    Intenta comprimir el video al peso objetivo.
    Reduce bitrate progresivamente hasta conseguirlo.
    """
    bitrates = ["800k", "600k", "450k", "350k", "250k", "200k"]

    for bitrate in bitrates:
        # Ejecutar ffmpeg
        comando = [
            "ffmpeg", "-y",
            "-i", str(ruta_origen),
            "-t", str(duracion),
            "-c:v", "libx264",
            "-preset", "medium",
            "-b:v", bitrate,
            "-vf", f"scale=-2:'min({alto_max},ih)'",
            "-movflags", "+faststart",
            "-an",  # sin audio
            str(ruta_destino),
        ]

        try:
            subprocess.run(comando, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error ffmpeg con bitrate {bitrate}: {e.stderr.decode()[:200]}")
            continue

        # Verificar peso
        peso_kb = Path(ruta_destino).stat().st_size / 1024
        if peso_kb <= peso_objetivo_kb:
            return round(peso_kb, 1), True

        # Si no, intentar con el siguiente bitrate
        print(f"Video pesa {peso_kb:.0f} KB con bitrate {bitrate}, reduciendo...")

    # Si llegamos aquí, devolvemos el último resultado (el más comprimido)
    peso_kb = Path(ruta_destino).stat().st_size / 1024
    return round(peso_kb, 1), True


# ============================================================
# ELIMINAR
# ============================================================
def eliminar_video(ruta):
    """Borra un archivo de video si existe."""
    try:
        ruta = Path(ruta)
        if ruta.exists():
            ruta.unlink()
            return True
    except Exception as e:
        print(f"Error borrando video: {e}")
    return False