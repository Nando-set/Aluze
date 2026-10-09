"""
Generador de tarjetas HTML individuales.
Aquí vive TODO lo relacionado con el diseño de una cotización.
"""
import re
import html
import urllib.parse
from datetime import datetime
from pathlib import Path

from config import (
    BASE_DIR, CARPETA_COTIZACIONES,
    LOGO_PNG, LOGO_PNG_CLARO, URL_BASE
)


# ============================================================
# DÍAS Y MESES EN ESPAÑOL
# ============================================================
DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def formatear_fecha_larga(fecha_str):
    """Convierte '15/10/2026' en 'Jueves 15 de octubre'."""
    if not fecha_str:
        return ""
    try:
        dt = datetime.strptime(fecha_str.strip(), "%d/%m/%Y")
        dia_semana = DIAS_ES[dt.weekday()]
        mes = MESES_ES[dt.month - 1]
        return f"{dia_semana} {dt.day} de {mes}"
    except Exception:
        return fecha_str


# ============================================================
# DETECCIÓN DE LINKS DE GOOGLE MAPS
# ============================================================
# Patrones que reconocemos como links de Google Maps
PATRONES_MAPS = [
    r"maps\.app\.goo\.gl",           # link corto oficial
    r"goo\.gl/maps",                  # link corto viejo
    r"google\.com/maps",              # link largo
    r"maps\.google\.com",             # link largo viejo
    r"maps\.google\.",                # variante internacional
]


def es_link_maps(texto):
    """Devuelve True si el texto parece un link de Google Maps."""
    if not texto:
        return False
    texto_lower = texto.lower()
    return any(re.search(patron, texto_lower) for patron in PATRONES_MAPS)


def es_url(texto):
    """Devuelve True si el texto empieza por http:// o https://."""
    if not texto:
        return False
    texto_strip = texto.strip().lower()
    return texto_strip.startswith("http://") or texto_strip.startswith("https://")


def obtener_maps_url(domicilio):
    """
    Devuelve la URL correcta para abrir Google Maps.

    - Si el domicilio es un link de Google Maps → devuelve ese link tal cual.
    - Si el domicilio es otra URL → devuelve esa URL (por si pegaste un link raro).
    - Si el domicilio es texto → busca la dirección en Google Maps.
    """
    if not domicilio:
        return ""

    domicilio_strip = domicilio.strip()

    # Caso 1: es un link de Google Maps → usarlo tal cual
    if es_link_maps(domicilio_strip):
        return domicilio_strip

    # Caso 2: es alguna otra URL → usarla tal cual
    if es_url(domicilio_strip):
        return domicilio_strip

    # Caso 3: es una dirección escrita → buscar en Google Maps
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(domicilio_strip)}"


def obtener_texto_boton_maps(domicilio):
    """Devuelve el texto del botón según el tipo de domicilio."""
    if es_link_maps(domicilio):
        return "📍 Ver ubicación compartida"
    return "📍 Abrir en Google Maps"


# ============================================================
# UTILIDADES INTERNAS
# ============================================================
def sanitizar_nombre(texto):
    texto = texto.lower().strip()
    reemplazos = {'á':'a','à':'a','ä':'a','â':'a','é':'e','è':'e','ë':'e','ê':'e',
                  'í':'i','ì':'i','ï':'i','î':'i','ó':'o','ò':'o','ö':'o','ô':'o',
                  'ú':'u','ù':'u','ü':'u','û':'u','ñ':'n'}
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    texto = re.sub(r'[^a-z0-9_-]+', '_', texto)
    return texto.strip('_') or "sin_nombre"


def obtener_semana_iso(fecha=None):
    if fecha is None:
        fecha = datetime.now()
    year, week, _ = fecha.isocalendar()
    lunes = fecha.fromordinal(fecha.toordinal() - fecha.weekday())
    domingo = fecha.fromordinal(lunes.toordinal() + 6)
    return year, week, lunes, domingo


def obtener_logo_html(desde_subcarpeta=False, claro=False):
    """Devuelve el HTML del logo."""
    archivo = "LogoAluzeClaro.png" if claro else "LogoAluze.png"
    ruta_completa = LOGO_PNG_CLARO if claro else LOGO_PNG

    if ruta_completa.exists():
        if desde_subcarpeta:
            ruta = f"../../assets/{archivo}"
        else:
            ruta = f"assets/{archivo}"
        return f'<img src="{ruta}" alt="Aluze" class="logo-img">'

    color = "#f8fafc" if claro else "#973359"
    return f'<h2 style="color:{color};margin:0;letter-spacing:3px;">ALUZE</h2>'


# ============================================================
# GENERADOR PRINCIPAL
# ============================================================
def generar_html(id_reg, cliente, domicilio, telefono, concepto,
                 cotizacion, monto, notas_cliente, fecha,
                 fecha_pautada="", hora_pautada="", notas_internas=""):
    """Genera la tarjeta HTML de una cotización."""
    year, week, _, _ = obtener_semana_iso()
    nombre_semana = f"{year}-Semana-{week:02d}"
    carpeta_semana = CARPETA_COTIZACIONES / nombre_semana
    carpeta_semana.mkdir(parents=True, exist_ok=True)

    cliente_seguro = sanitizar_nombre(cliente)
    nombre_archivo = f"cotizacion_{id_reg}_{cliente_seguro}.html"
    ruta_html = carpeta_semana / nombre_archivo
    ruta_relativa = ruta_html.relative_to(BASE_DIR).as_posix()

    url_individual = f"{URL_BASE}{ruta_relativa}"

    # Escapar
    cliente_e = html.escape(cliente)
    domicilio_e = html.escape(domicilio)
    telefono_e = html.escape(telefono)
    concepto_e = html.escape(concepto)
    cotizacion_e = html.escape(cotizacion)
    monto_e = html.escape(monto)
    notas_cliente_e = html.escape(notas_cliente)

    # MAPS con detección de link vs dirección
    maps_url = obtener_maps_url(domicilio)
    maps_texto_boton = obtener_texto_boton_maps(domicilio)

    telefono_limpio = re.sub(r'\D', '', telefono)
    whatsapp_url = f"https://wa.me/{telefono_limpio}"

    logo_html = obtener_logo_html(desde_subcarpeta=True, claro=False)

    # ---- Bloque FECHA PAUTADA ----
    if fecha_pautada:
        fecha_larga = formatear_fecha_larga(fecha_pautada)
        if hora_pautada:
            texto_fecha = f"{fecha_larga} · {hora_pautada}"
        else:
            texto_fecha = fecha_larga

        bloque_fecha_html = f"""
  <div class="fecha-pautada">
    <div class="fecha-pautada-label">📅 Visita pautada</div>
    <div class="fecha-pautada-valor">{html.escape(texto_fecha)}</div>
  </div>"""
    else:
        bloque_fecha_html = ""

    # ---- Sección de notas del cliente ----
    if notas_cliente.strip():
        bloque_notas_html = f"""
  <div class="section">
    <div class="label">Notas / Observaciones</div>
    <div class="box" id="val-notas" style="border-left-color:#d97706;">{notas_cliente_e}</div>
  </div>"""
    else:
        bloque_notas_html = """
  <div class="section" style="display:none;">
    <div class="box" id="val-notas"></div>
  </div>"""

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cotización - {cliente_e} | Aluze</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #0f172a; color: #334155; margin: 0; padding: 20px;
         display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
  .card {{ background: #fff; width: 100%; max-width: 440px; padding: 30px;
           border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }}
  .header-brand {{ text-align: center; margin-bottom: 25px; border-bottom: 2px solid #f1f5f9; padding-bottom: 20px; }}
  .logo-container svg {{ max-width: 150px; height: auto; display: block; margin: 0 auto 8px; }}
  .logo-container img {{ max-width: 150px; height: auto; display: block; margin: 0 auto 8px; }}
  .tagline {{ font-size: 10px; text-transform: uppercase; letter-spacing: 3px; color: #64748b; font-weight: 600; }}
  .card-title {{ font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px; color: #973359; font-weight: 700; margin: 0 0 20px; text-align: center; }}

  .fecha-pautada {{
    background: linear-gradient(135deg, #973359 0%, #7f2a4a 100%);
    color: #fff; padding: 14px 18px; border-radius: 10px;
    margin-bottom: 20px; text-align: center;
    box-shadow: 0 4px 12px rgba(151,51,89,0.25);
  }}
  .fecha-pautada-label {{
    font-size: 10px; text-transform: uppercase; letter-spacing: 2px;
    opacity: 0.9; margin-bottom: 4px; font-weight: 600;
  }}
  .fecha-pautada-valor {{ font-size: 18px; font-weight: 800; letter-spacing: 0.5px; }}

  .section {{ margin-bottom: 18px; }}
  .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; margin-bottom: 4px; font-weight: 600; }}
  .value-row {{ display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 8px 12px; border-radius: 6px; border: 1px solid #e2e8f0; gap: 10px; }}
  .value {{ font-size: 15px; color: #1e293b; font-weight: 500; word-break: break-word; }}
  .actions-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }}
  .btn-action {{ display: inline-flex; align-items: center; gap: 5px; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 500; text-decoration: none; cursor: pointer; border: none; }}
  .btn-call {{ color: #973359; background: #fdf2f8; border: 1px solid #fbcfe8; }}
  .btn-wa {{ color: #166534; background: #dcfce7; border: 1px solid #bbf7d0; }}
  .btn-copy {{ color: #475569; background: #e2e8f0; font-size: 12px; padding: 4px 8px; border-radius: 4px; font-weight: 600; }}
  .btn-copy:hover {{ background: #cbd5e1; }}
  .map-link {{ display: inline-flex; align-items: center; gap: 5px; color: #831843; background: #fdf2f8; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 500; text-decoration: none; margin-top: 6px; border: 1px solid #fbcfe8; }}
  .box {{ background: #f8fafc; border-left: 4px solid #973359; padding: 14px; border-radius: 6px; margin-top: 6px; white-space: pre-line; font-size: 14px; color: #334155; line-height: 1.4; }}
  .price-box {{ background: #fdf2f8; border: 1px dashed #973359; padding: 12px; border-radius: 8px; text-align: center; margin-top: 15px; }}
  .price-label {{ font-size: 11px; text-transform: uppercase; color: #831843; font-weight: 600; }}
  .price-value {{ font-size: 20px; font-weight: 800; color: #973359; margin-top: 2px; }}
  .btn-universal-copy {{ width: 100%; background: #1e293b; color: #fff; border: none; padding: 12px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 20px; }}
  .btn-universal-copy:hover {{ background: #334155; }}

  .share-buttons {{ display: flex; gap: 10px; margin-top: 18px; padding-top: 18px; border-top: 1px solid #f1f5f9; }}
  .btn-share {{ flex: 1; display: inline-flex; align-items: center; justify-content: center;
                gap: 6px; padding: 11px 14px; border-radius: 8px; font-size: 13px;
                font-weight: 600; text-decoration: none; cursor: pointer; border: none;
                transition: opacity 0.15s, transform 0.1s; }}
  .btn-share:hover {{ opacity: 0.88; }}
  .btn-share:active {{ transform: scale(0.98); }}
  .btn-copy-link {{ background: #f1f5f9; color: #334155; border: 1px solid #e2e8f0; }}
  .btn-whatsapp {{ background: #25d366; color: #fff; }}

  .toast {{ position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
           background: #10b981; color: #fff; padding: 10px 20px; border-radius: 30px;
           font-size: 13px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
           display: none; z-index: 1000; }}
  .footer {{ text-align: center; font-size: 11px; color: #94a3b8; margin-top: 20px;
            border-top: 1px solid #f1f5f9; padding-top: 15px; }}
</style>
</head>
<body>
<div class="card">
  <div class="header-brand">
    <div class="logo-container">{logo_html}</div>
    <div class="tagline">Persianas &amp; Decoración</div>
  </div>
  <div class="card-title">Tarjeta de Cotización</div>

  {bloque_fecha_html}

  <div class="section">
    <div class="label">Cliente</div>
    <div class="value-row"><span class="value" id="val-cliente">{cliente_e}</span></div>
  </div>
  <div class="section">
    <div class="label">Concepto / Sistema</div>
    <div class="value-row"><span class="value" id="val-concepto">{concepto_e}</span></div>
  </div>
  <div class="section">
    <div class="label">Teléfono y Contacto</div>
    <div class="value-row">
      <span class="value" id="val-tel">{telefono_e}</span>
      <button class="btn-action btn-copy" onclick="copiarTexto('val-tel','¡Teléfono copiado!')">📋 Copiar</button>
    </div>
    <div class="actions-row">
      <a class="btn-action btn-call" href="tel:{telefono_e}">📞 Llamar</a>
      <a class="btn-action btn-wa" href="{whatsapp_url}" target="_blank">💬 WhatsApp</a>
    </div>
  </div>
  <div class="section">
    <div class="label">Domicilio</div>
    <div class="value-row" style="align-items:flex-start;">
      <span class="value" id="val-dom">{domicilio_e}</span>
      <button class="btn-action btn-copy" onclick="copiarTexto('val-dom','¡Domicilio copiado!')">📋 Copiar</button>
    </div>
    <a class="map-link" href="{maps_url}" target="_blank">{maps_texto_boton}</a>
  </div>
  <div class="section">
    <div class="label">Detalles de la Cotización</div>
    <div class="box" id="val-detalles">{cotizacion_e}</div>
  </div>
  {bloque_notas_html}
  <div class="price-box">
    <div class="price-label">Monto Aproximado</div>
    <div class="price-value" id="val-monto">{monto_e}</div>
  </div>
  <button class="btn-universal-copy" onclick="copiarTodo()">📋 Copiar toda la información para chat</button>

  <div class="share-buttons">
    <button class="btn-share btn-copy-link" onclick="copiarEnlace()">
      📋 Copiar enlace
    </button>
    <a class="btn-share btn-whatsapp" id="btn-whatsapp-share" href="#" target="_blank">
      💬 Compartir por WhatsApp
    </a>
  </div>

  <div class="footer">Generado el {fecha} | Persianas Aluze</div>
</div>
<div id="toast" class="toast">¡Copiado!</div>
<script>
const URL_FALLBACK = "{url_individual}";
const FECHA_PAUTADA = "{html.escape(fecha_pautada)}";
const HORA_PAUTADA = "{html.escape(hora_pautada)}";

function obtenerUrl() {{
  if (window.location.protocol === "http:" || window.location.protocol === "https:") {{
    return window.location.href;
  }}
  return URL_FALLBACK;
}}

function mostrarToast(msg) {{
  const t = document.getElementById('toast');
  t.innerText = msg; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 2000);
}}

function copiarTexto(id, msg) {{
  const texto = document.getElementById(id).innerText;
  navigator.clipboard.writeText(texto).then(() => mostrarToast(msg));
}}

function copiarEnlace() {{
  const url = obtenerUrl();
  navigator.clipboard.writeText(url).then(() => {{
    mostrarToast('¡Enlace copiado al portapapeles!');
  }}).catch(err => {{
    console.error('Error al copiar: ', err);
    mostrarToast('No se pudo copiar el enlace');
  }});
}}

function copiarTodo() {{
  const g = id => {{
    const el = document.getElementById(id);
    return el ? el.innerText : '';
  }};
  let txt = `*COTIZACIÓN ALUZE*\\n`;
  if (FECHA_PAUTADA) {{
    let fp = FECHA_PAUTADA;
    if (HORA_PAUTADA) fp += ` · ${{HORA_PAUTADA}}`;
    txt += `📅 *Visita pautada:* ${{fp}}\\n`;
  }}
  txt += `👤 *Cliente:* ${{g('val-cliente')}}\\n`;
  txt += `📦 *Concepto:* ${{g('val-concepto')}}\\n`;
  txt += `📞 *Teléfono:* ${{g('val-tel')}}\\n`;
  txt += `📍 *Domicilio:* ${{g('val-dom')}}\\n`;
  txt += `📋 *Detalles:*\\n${{g('val-detalles')}}\\n`;
  const notas = g('val-notas').trim();
  if (notas) txt += `📝 *Notas:*\\n${{notas}}\\n`;
  txt += `💰 *Monto:* ${{g('val-monto')}}`;
  navigator.clipboard.writeText(txt).then(() => mostrarToast('¡Copiado!'));
}}

document.addEventListener('DOMContentLoaded', () => {{
  const url = obtenerUrl();
  const mensaje = encodeURIComponent(
    `Hola, aquí está tu cotización de Persianas Aluze:\\n\\n${{url}}\\n\\nCualquier duda, quedo atento.`
  );
  document.getElementById('btn-whatsapp-share').href = `https://wa.me/?text=${{mensaje}}`;
}});
</script>
</body>
</html>
"""
    ruta_html.write_text(html_content, encoding="utf-8")
    return ruta_relativa