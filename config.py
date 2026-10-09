"""
Configuración global de Aluze.
Aquí viven las rutas, constantes y credenciales de GitHub.
"""
from pathlib import Path

# ============================================================
# GITHUB
# ============================================================
GITHUB_USER = "Nando-set"
GITHUB_REPO = "Aluze"
GITHUB_BRANCH = "main"

# ============================================================
# RUTAS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

# Archivos
DB_FILE = BASE_DIR / "base_datos_clientes.csv"
INDEX_HTML = BASE_DIR / "index.html"
LOGO_SVG = BASE_DIR / "LogoAluze.svg"
LOGO_PNG = BASE_DIR / "LogoAluze.png"              # Letras negras (tarjetas, fondo blanco)
LOGO_PNG_CLARO = BASE_DIR / "LogoAluzeClaro.png"   # Letras claras (panel y Tkinter, fondo oscuro)

# Carpetas
CARPETA_COTIZACIONES = BASE_DIR / "cotizaciones"
CARPETA_ASSETS = BASE_DIR / "assets"

# ============================================================
# URLS
# ============================================================
URL_BASE = f"https://{GITHUB_USER.lower()}.github.io/{GITHUB_REPO}/"

# ============================================================
# COLORES (para consistencia entre interfaz y HTML)
# ============================================================
COLOR_FONDO_OSCURO = "#0f172a"
COLOR_SIDEBAR = "#1e293b"
COLOR_ROSA_ALUZE = "#973359"
COLOR_VERDE = "#34d399"
# ============================================================
# CATÁLOGO
# ============================================================
CARPETA_CATALOGO = BASE_DIR / "catalogo"
CATALOGO_IMAGENES = CARPETA_CATALOGO / "imagenes"
CATALOGO_VIDEOS = CARPETA_CATALOGO / "videos"
CATALOGO_PAGINAS = CARPETA_CATALOGO / "paginas"
CATALOGO_CATEGORIAS = CARPETA_CATALOGO / "categorias.json"
CATALOGO_MODELOS = CARPETA_CATALOGO / "modelos.json"
CATALOGO_INDEX = BASE_DIR / "catalogo.html"
