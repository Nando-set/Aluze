"""
Generador del catálogo HTML.
Crea:
- catalogo.html (grid por categorías)
- catalogo/paginas/{id_modelo}.html (detalle por modelo)
"""
import html
import shutil
from datetime import datetime
from pathlib import Path

from config import (
    BASE_DIR, CATALOGO_INDEX, CATALOGO_PAGINAS,
    CATALOGO_IMAGENES, CARPETA_CATALOGO,
    GITHUB_USER, GITHUB_REPO, URL_BASE,
    LOGO_PNG, LOGO_PNG_CLARO
)
from core.catalogo_datos import leer_categorias, leer_modelos


# ============================================================
# UTILIDADES
# ============================================================
def _obtener_logo_html(claro=False):
    """Devuelve el HTML del logo (claro para fondo oscuro)."""
    archivo = "LogoAluzeClaro.png" if claro else "LogoAluze.png"
    ruta_completa = LOGO_PNG_CLARO if claro else LOGO_PNG

    if ruta_completa.exists():
        return f'<img src="assets/{archivo}" alt="Aluze" class="logo-img">'
    return '<h2 style="color:#973359;margin:0;letter-spacing:3px;">ALUZE</h2>'


def _sanitizar_id(texto):
    import re
    texto = texto.lower().strip()
    reemplazos = {'á':'a','à':'a','ä':'a','â':'a','é':'e','è':'e','ë':'e','ê':'e',
                  'í':'i','ì':'i','ï':'i','î':'i','ó':'o','ò':'o','ö':'o','ô':'o',
                  'ú':'u','ù':'u','ü':'u','û':'u','ñ':'n'}
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return re.sub(r'[^a-z0-9_-]+', '_', texto).strip('_') or "sin_nombre"


def _ruta_imagen_desde_pagina(ruta_relativa):
    """
    Convierte una ruta relativa del JSON (ej: catalogo/imagenes/x/01.webp)
    a una ruta válida desde catalogo/paginas/.
    """
    # Desde catalogo/paginas/xxx.html hasta la raíz, son 2 niveles arriba
    return "../../" + ruta_relativa


# ============================================================
# GENERADOR PRINCIPAL
# ============================================================
def regenerar_catalogo():
    """Regenera el catálogo completo (grid + páginas individuales)."""
    categorias = leer_categorias()
    modelos = leer_modelos()

    if not categorias:
        print("No hay categorías definidas.")
        return False

    # 1. Generar el grid principal
    _generar_grid(categorias, modelos)

    # 2. Generar las páginas individuales
    for modelo in modelos:
        _generar_pagina_modelo(modelo)

    print(f"✓ Catálogo regenerado: {len(modelos)} modelos")
    return True


# ============================================================
# GRID PRINCIPAL (catalogo.html)
# ============================================================
def _generar_grid(categorias, modelos):
    """Genera el HTML del catálogo con grid por categorías."""
    logo_html = _obtener_logo_html(claro=True)

    # Total y métricas
    total = len(modelos)
    categorias_con_modelos = [c for c in categorias if any(m.get("categoria") == c["id"] for m in modelos)]

    # Bloques por categoría
    bloques = []
    for cat in categorias_con_modelos:
        modelos_cat = [m for m in modelos if m.get("categoria") == cat["id"]]
        if not modelos_cat:
            continue

        tarjetas = []
        for modelo in modelos_cat:
            tarjetas.append(_tarjeta_modelo_html(modelo))

        bloques.append(f"""
        <section class="categoria" data-categoria="{cat['id']}">
          <h2>{cat['emoji']} {html.escape(cat['nombre'])}
            <span class="badge">{len(modelos_cat)} modelo{"s" if len(modelos_cat) != 1 else ""}</span>
          </h2>
          <div class="grid">
            {''.join(tarjetas)}
          </div>
        </section>""")

    # Filtros por categoría
    botones_filtro = ['<button class="activo" data-filtro="todas" onclick="setFiltro(\'todas\', this)">📋 Todas</button>']
    for cat in categorias_con_modelos:
        botones_filtro.append(
            f'<button data-filtro="{cat["id"]}" onclick="setFiltro(\'{cat["id"]}\', this)">'
            f'{cat["emoji"]} {html.escape(cat["nombre"])}</button>'
        )

    contenido = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aluze | Catálogo de Productos</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
  .header {{ text-align: center; margin-bottom: 24px; padding-bottom: 20px;
            border-bottom: 2px solid #1e293b; }}
  .header img {{ max-width: 180px; height: auto; }}
  .header h1 {{ font-size: 22px; margin: 12px 0 4px; color: #f8fafc; }}
  .header p {{ color: #94a3b8; font-size: 13px; margin: 0; }}

  .top-nav {{ max-width: 640px; margin: 16px auto 0; text-align: center; }}
  .top-nav a {{ display: inline-block; padding: 8px 18px; border-radius: 8px;
               background: #1e293b; color: #cbd5e1; text-decoration: none;
               font-size: 13px; font-weight: 600; border: 1px solid #334155; }}
  .top-nav a:hover {{ border-color: #973359; color: #f8fafc; }}

  .controles {{ max-width: 640px; margin: 24px auto 30px; }}
  .buscador input {{ width: 100%; padding: 12px 16px; border-radius: 10px;
                    border: 1px solid #334155; background: #1e293b;
                    color: #f8fafc; font-size: 15px; outline: none; }}
  .buscador input:focus {{ border-color: #973359; }}
  .filtros {{ display: flex; gap: 8px; justify-content: center;
             margin-top: 12px; flex-wrap: wrap; }}
  .filtros button {{ padding: 8px 14px; border-radius: 8px; border: 1px solid #334155;
                    background: #1e293b; color: #cbd5e1; font-size: 12px;
                    font-weight: 600; cursor: pointer; }}
  .filtros button:hover {{ border-color: #973359; color: #f8fafc; }}
  .filtros button.activo {{ background: #973359; border-color: #973359; color: #fff; }}

  .categoria {{ margin-bottom: 40px; }}
  .categoria h2 {{ font-size: 16px; color: #f8fafc; border-left: 4px solid #973359;
                  padding-left: 10px; margin-bottom: 16px;
                  display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .badge {{ background: #334155; color: #cbd5e1; font-size: 11px;
           padding: 3px 8px; border-radius: 10px; font-weight: 600; }}

  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }}
  .card {{ display: block; text-decoration: none; background: #1e293b;
          border-radius: 12px; overflow: hidden; border: 1px solid #334155;
          transition: transform 0.15s, border-color 0.15s; color: inherit; }}
  .card:hover {{ transform: translateY(-3px); border-color: #973359;
                box-shadow: 0 6px 20px rgba(151,51,89,0.2); }}
  .card-img {{ width: 100%; aspect-ratio: 1/1; background: #0f172a;
              display: flex; align-items: center; justify-content: center; overflow: hidden; }}
  .card-img img {{ width: 100%; height: 100%; object-fit: cover; }}
  .card-img .placeholder {{ font-size: 60px; color: #334155; }}
  .card-body {{ padding: 14px; }}
  .card-body h3 {{ font-size: 15px; color: #f8fafc; margin: 0 0 6px; }}
  .card-body p {{ font-size: 12px; color: #94a3b8; margin: 0 0 10px;
                 display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
                 overflow: hidden; }}
  .card-cta {{ font-size: 12px; color: #973359; font-weight: 600; }}

  .vacio {{ text-align: center; color: #64748b; padding: 60px 20px; }}
  footer {{ text-align: center; color: #475569; font-size: 12px;
           margin-top: 40px; padding-top: 20px; border-top: 1px solid #1e293b; }}
</style>
</head>
<body>
  <div class="header">
    {logo_html}
    <h1>Catálogo de Productos</h1>
    <p>Persianas &amp; Decoración · Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <div class="top-nav">
      <a href="index.html">← Volver al panel de cotizaciones</a>
    </div>
  </div>

  <div class="controles">
    <div class="buscador">
      <input type="text" id="buscador" placeholder="🔍 Buscar producto..." oninput="aplicarFiltros()">
    </div>
    <div class="filtros">
      {''.join(botones_filtro)}
    </div>
  </div>

  <div id="contenido">
    {''.join(bloques) if bloques else '<div class="vacio"><h3>Catálogo vacío</h3><p>Aún no hay modelos publicados.</p></div>'}
  </div>

  <footer>Persianas Aluze · Catálogo generado automáticamente</footer>

  <script>
    let filtroActual = "todas";

    function setFiltro(filtro, boton) {{
      filtroActual = filtro;
      document.querySelectorAll('.filtros button').forEach(b => b.classList.remove('activo'));
      boton.classList.add('activo');
      aplicarFiltros();
    }}

    function aplicarFiltros() {{
      const q = document.getElementById('buscador').value.toLowerCase();

      document.querySelectorAll('.categoria').forEach(sec => {{
        const cat = sec.dataset.categoria;
        let pasaFiltro = true;
        if (filtroActual !== 'todas' && cat !== filtroActual) pasaFiltro = false;

        let cardsVisibles = 0;
        sec.querySelectorAll('.card').forEach(card => {{
          const coincide = card.innerText.toLowerCase().includes(q);
          card.style.display = coincide ? '' : 'none';
          if (coincide) cardsVisibles++;
        }});

        sec.style.display = (pasaFiltro && cardsVisibles > 0) ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>
"""
    CATALOGO_INDEX.write_text(contenido, encoding="utf-8")


def _tarjeta_modelo_html(modelo):
    """Genera el HTML de una tarjeta del grid."""
    id_modelo = modelo["id"]
    nombre = html.escape(modelo.get("nombre", "Sin nombre"))
    descripcion = html.escape(modelo.get("descripcion", ""))[:120]

    # Primera imagen
    imagenes = modelo.get("imagenes", [])
    if imagenes:
        # Buscar la miniatura de la primera, si existe
        ruta_original = imagenes[0]
        ruta_mini = ruta_original.replace(".webp", "_thumb.webp")
        # Verificar si existe la miniatura
        ruta_abs_mini = BASE_DIR / ruta_mini
        if ruta_abs_mini.exists():
            ruta_img = ruta_mini
        else:
            ruta_img = ruta_original

        img_html = f'<img src="{html.escape(ruta_img)}" alt="{nombre}" loading="lazy">'
    else:
        img_html = '<div class="placeholder">📷</div>'

    url_pagina = f"catalogo/paginas/{id_modelo}.html"

    return f"""
    <a class="card" href="{url_pagina}">
      <div class="card-img">{img_html}</div>
      <div class="card-body">
        <h3>{nombre}</h3>
        <p>{descripcion}</p>
        <div class="card-cta">Ver detalles →</div>
      </div>
    </a>"""


# ============================================================
# PÁGINA INDIVIDUAL POR MODELO
# ============================================================
def _generar_pagina_modelo(modelo):
    """Genera la página HTML individual de un modelo."""
    id_modelo = modelo["id"]
    nombre = html.escape(modelo.get("nombre", "Sin nombre"))
    descripcion = html.escape(modelo.get("descripcion", ""))

    logo_html = _obtener_logo_html(claro=True)

    # Carrusel de fotos
    fotos = modelo.get("imagenes", [])
    carrusel_slides = []
    for i, ruta in enumerate(fotos):
        ruta_pagina = _ruta_imagen_desde_pagina(ruta)
        activo = "activo" if i == 0 else ""
        carrusel_slides.append(
            f'<div class="slide {activo}" data-slide="{i}">'
            f'<img src="{html.escape(ruta_pagina)}" alt="{nombre} - Foto {i+1}">'
            f'</div>'
        )

    if fotos:
        puntos = ''.join(
            f'<span class="punto {"activo" if i == 0 else ""}" onclick="irASlide({i})"></span>'
            for i in range(len(fotos))
        )
        carrusel_html = f"""
        <div class="carrusel">
          <div class="slides">{''.join(carrusel_slides)}</div>
          <button class="nav prev" onclick="cambiarSlide(-1)">‹</button>
          <button class="nav next" onclick="cambiarSlide(1)">›</button>
          <div class="puntos">{puntos}</div>
        </div>"""
    else:
        carrusel_html = '<div class="carrusel vacio">📷<p>Sin fotos aún</p></div>'

    # Video
    video = modelo.get("video")
    if video:
        ruta_video = _ruta_imagen_desde_pagina(video)
        video_html = f"""
        <div class="video-box">
          <video controls preload="none" poster="">
            <source src="{html.escape(ruta_video)}" type="video/mp4">
          </video>
        </div>"""
    else:
        video_html = ""

    # Líneas como pestañas
    lineas = modelo.get("lineas", [])
    lineas_tabs_html = ""
    lineas_contenido_html = ""

    if lineas:
        tabs = []
        contenidos = []
        for i, linea in enumerate(lineas):
            nombre_linea = html.escape(linea.get("nombre", f"Línea {i+1}"))
            activo = "activo" if i == 0 else ""
            tabs.append(
                f'<button class="tab {activo}" onclick="cambiarLinea({i})" data-linea="{i}">'
                f'{nombre_linea}</button>'
            )
            contenidos.append(_contenido_linea_html(linea, i))

        lineas_tabs_html = f'<div class="tabs">{"".join(tabs)}</div>'
        lineas_contenido_html = f'<div class="lineas-contenido">{"".join(contenidos)}</div>'
    else:
        lineas_tabs_html = '<p class="sin-lineas">Este modelo aún no tiene líneas definidas.</p>'

    contenido = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{nombre} | Catálogo Aluze</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}

  .header {{ display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid #1e293b; }}
  .header img {{ max-width: 140px; height: auto; }}
  .header .volver {{ padding: 8px 16px; border-radius: 8px; background: #1e293b;
                    color: #cbd5e1; text-decoration: none; font-size: 13px;
                    font-weight: 600; border: 1px solid #334155; }}
  .header .volver:hover {{ border-color: #973359; color: #f8fafc; }}

  .detalle {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 30px; }}
  @media (max-width: 700px) {{ .detalle {{ grid-template-columns: 1fr; }} }}

  /* Carrusel */
  .carrusel {{ position: relative; background: #1e293b; border-radius: 12px;
              overflow: hidden; aspect-ratio: 1/1; }}
  .carrusel.vacio {{ display: flex; flex-direction: column; align-items: center;
                    justify-content: center; color: #475569; font-size: 50px; }}
  .carrusel.vacio p {{ font-size: 13px; margin: 10px 0 0; }}
  .slides {{ width: 100%; height: 100%; position: relative; }}
  .slide {{ position: absolute; inset: 0; opacity: 0; transition: opacity 0.3s; }}
  .slide.activo {{ opacity: 1; }}
  .slide img {{ width: 100%; height: 100%; object-fit: cover; }}
  .nav {{ position: absolute; top: 50%; transform: translateY(-50%);
         background: rgba(15, 23, 42, 0.7); color: #fff; border: none;
         font-size: 30px; width: 44px; height: 44px; border-radius: 50%;
         cursor: pointer; font-weight: 300; }}
  .nav:hover {{ background: rgba(151, 51, 89, 0.9); }}
  .nav.prev {{ left: 10px; }}
  .nav.next {{ right: 10px; }}
  .puntos {{ position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%);
            display: flex; gap: 6px; }}
  .punto {{ width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.4);
           cursor: pointer; }}
  .punto.activo {{ background: #fff; }}

  /* Info */
  .info h1 {{ font-size: 26px; color: #f8fafc; margin: 0 0 12px; }}
  .info .descripcion {{ font-size: 14px; color: #cbd5e1; line-height: 1.6;
                       margin-bottom: 20px; white-space: pre-line; }}
  .video-box {{ margin-top: 20px; border-radius: 12px; overflow: hidden;
               background: #1e293b; }}
  .video-box video {{ width: 100%; display: block; }}

  /* Líneas */
  .seccion-titulo {{ font-size: 18px; color: #f8fafc; border-left: 4px solid #973359;
                    padding-left: 12px; margin: 30px 0 16px; }}
  .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
  .tab {{ padding: 10px 18px; border-radius: 8px; background: #1e293b;
         color: #cbd5e1; border: 1px solid #334155; cursor: pointer;
         font-size: 13px; font-weight: 600; }}
  .tab:hover {{ border-color: #973359; color: #f8fafc; }}
  .tab.activo {{ background: #973359; border-color: #973359; color: #fff; }}

  .linea {{ display: none; }}
  .linea.activo {{ display: block; }}
  .linea-inner {{ display: grid; grid-template-columns: 200px 1fr; gap: 20px;
                 background: #1e293b; border-radius: 12px; padding: 20px;
                 border: 1px solid #334155; }}
  @media (max-width: 500px) {{ .linea-inner {{ grid-template-columns: 1fr; }} }}
  .linea-img {{ background: #0f172a; border-radius: 8px; overflow: hidden;
               aspect-ratio: 1/1; }}
  .linea-img img {{ width: 100%; height: 100%; object-fit: cover; }}
  .linea-img .vacio {{ display: flex; align-items: center; justify-content: center;
                      color: #475569; font-size: 40px; height: 100%; }}
  .linea-info h3 {{ margin: 0 0 8px; color: #f8fafc; font-size: 16px; }}
  .linea-info p {{ margin: 0 0 14px; color: #cbd5e1; font-size: 13px;
                  line-height: 1.5; white-space: pre-line; }}
  .colores-titulo {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
                    color: #94a3b8; font-weight: 700; margin-bottom: 8px; }}
  .chips {{ display: flex; gap: 6px; flex-wrap: wrap; }}
  .chip {{ display: inline-flex; align-items: center; gap: 5px;
          background: #0f172a; padding: 4px 10px 4px 4px; border-radius: 20px;
          border: 1px solid #334155; font-size: 11px; color: #cbd5e1; }}
  .chip-circulo {{ width: 16px; height: 16px; border-radius: 50%;
                  border: 1px solid #64748b; }}

  .sin-lineas {{ color: #64748b; font-style: italic; padding: 20px;
                text-align: center; background: #1e293b; border-radius: 12px; }}

  /* WhatsApp */
  .whatsapp-box {{ text-align: center; margin: 40px 0; }}
  .btn-wa {{ display: inline-flex; align-items: center; gap: 8px;
            background: #25d366; color: #fff; padding: 14px 28px;
            border-radius: 30px; text-decoration: none; font-weight: 700;
            font-size: 15px; }}
  .btn-wa:hover {{ opacity: 0.9; }}

  footer {{ text-align: center; color: #475569; font-size: 12px;
           margin-top: 40px; padding-top: 20px; border-top: 1px solid #1e293b; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    {logo_html}
    <a href="../../catalogo.html" class="volver">← Volver al catálogo</a>
  </div>

  <div class="detalle">
    <div>
      {carrusel_html}
    </div>
    <div class="info">
      <h1>{nombre}</h1>
      <div class="descripcion">{descripcion}</div>
      {video_html}
    </div>
  </div>

  <h2 class="seccion-titulo">Líneas disponibles</h2>
  {lineas_tabs_html}
  {lineas_contenido_html}

  <div class="whatsapp-box">
    <a class="btn-wa" href="https://wa.me/?text=Hola,%20me%20interesa%20el%20modelo%20{nombre}" target="_blank">
      💬 Consultar por WhatsApp
    </a>
  </div>

  <footer>Persianas Aluze · Catálogo generado automáticamente</footer>
</div>

<script>
  // Carrusel
  let slideActual = 0;
  const slides = document.querySelectorAll('.slide');
  const puntos = document.querySelectorAll('.punto');

  function mostrarSlide(n) {{
    if (slides.length === 0) return;
    slideActual = (n + slides.length) % slides.length;
    slides.forEach((s, i) => s.classList.toggle('activo', i === slideActual));
    puntos.forEach((p, i) => p.classList.toggle('activo', i === slideActual));
  }}

  function cambiarSlide(dir) {{ mostrarSlide(slideActual + dir); }}
  function irASlide(n) {{ mostrarSlide(n); }}

  // Líneas
  function cambiarLinea(n) {{
    document.querySelectorAll('.tab').forEach((t, i) => t.classList.toggle('activo', i === n));
    document.querySelectorAll('.linea').forEach((l, i) => l.classList.toggle('activo', i === n));
  }}
</script>
</body>
</html>
"""
    # Guardar la página
    CATALOGO_PAGINAS.mkdir(parents=True, exist_ok=True)
    ruta_pagina = CATALOGO_PAGINAS / f"{id_modelo}.html"
    ruta_pagina.write_text(contenido, encoding="utf-8")


def _contenido_linea_html(linea, indice):
    """Genera el HTML del contenido de una línea (imagen + desc + colores)."""
    nombre = html.escape(linea.get("nombre", ""))
    descripcion = html.escape(linea.get("descripcion", ""))
    imagen = linea.get("imagen")

    if imagen:
        ruta_img = _ruta_imagen_desde_pagina(imagen)
        img_html = f'<img src="{html.escape(ruta_img)}" alt="{nombre}">'
    else:
        img_html = '<div class="vacio">📷</div>'

    # Colores
    colores = linea.get("colores", [])
    if colores:
        chips = []
        for col in colores:
            chips.append(
                f'<span class="chip">'
                f'<span class="chip-circulo" style="background: {col.get("hex", "#fff")};"></span>'
                f'{html.escape(col.get("nombre", ""))}'
                f'</span>'
            )
        colores_html = f'''
        <div class="colores-titulo">Colores disponibles</div>
        <div class="chips">{"".join(chips)}</div>'''
    else:
        colores_html = ''

    activo = "activo" if indice == 0 else ""

    return f"""
    <div class="linea {activo}" data-linea="{indice}">
      <div class="linea-inner">
        <div class="linea-img">{img_html}</div>
        <div class="linea-info">
          <h3>{nombre}</h3>
          <p>{descripcion}</p>
          {colores_html}
        </div>
      </div>
    </div>"""