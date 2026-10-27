"""
Generador de notas de venta.
Cada nota se guarda como:
- Entrada en notas/notas_db.json
- Archivo HTML en notas/html/{folio}_{nombre_cliente}.html
"""
import json
import html
import re
from pathlib import Path
from datetime import datetime

from config import (
    BASE_DIR, CARPETA_NOTAS, NOTAS_DB, NOTAS_HTML,
    LOGO_PNG
)


# ============================================================
# INICIALIZACIÓN
# ============================================================
def inicializar_notas():
    """Crea la carpeta y el archivo de base de datos si no existen."""
    CARPETA_NOTAS.mkdir(exist_ok=True)
    NOTAS_HTML.mkdir(exist_ok=True)

    if not NOTAS_DB.exists():
        with open(NOTAS_DB, mode='w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)


# ============================================================
# LECTURA / ESCRITURA
# ============================================================
def leer_notas():
    """Devuelve todas las notas como lista de dicts."""
    if not NOTAS_DB.exists():
        return []
    with open(NOTAS_DB, mode='r', encoding='utf-8') as f:
        return json.load(f)


def buscar_nota(folio):
    """Devuelve una nota por su folio, o None."""
    for n in leer_notas():
        if n.get("folio") == str(folio):
            return n
    return None


def siguiente_folio():
    """Devuelve el siguiente folio como string de 4 dígitos."""
    notas = leer_notas()
    if not notas:
        return "0001"
    folios = [int(n["folio"]) for n in notas if n.get("folio", "").isdigit()]
    if not folios:
        return "0001"
    return f"{max(folios) + 1:04d}"


def agregar_nota(nota):
    """Añade una nota nueva. Devuelve (ok, mensaje)."""
    notas = leer_notas()
    if any(n.get("folio") == nota["folio"] for n in notas):
        return False, f"Ya existe una nota con folio {nota['folio']}."
    notas.append(nota)
    _guardar_notas(notas)
    return True, "Nota agregada."


def actualizar_nota(folio, nota_nueva):
    """Reemplaza una nota existente."""
    notas = leer_notas()
    for i, n in enumerate(notas):
        if n.get("folio") == str(folio):
            notas[i] = nota_nueva
            _guardar_notas(notas)
            return True, "Nota actualizada."
    return False, "Nota no encontrada."


def eliminar_nota(folio):
    """Elimina una nota y su HTML."""
    notas = leer_notas()
    nota_a_borrar = None
    notas_nuevas = []

    for n in notas:
        if n.get("folio") == str(folio):
            nota_a_borrar = n
        else:
            notas_nuevas.append(n)

    if not nota_a_borrar:
        return False, "Nota no encontrada."

    ruta_html = nota_a_borrar.get("ruta_html")
    if ruta_html:
        ruta_abs = BASE_DIR / ruta_html
        if ruta_abs.exists():
            try:
                ruta_abs.unlink()
            except Exception as e:
                print(f"Error borrando {ruta_abs}: {e}")

    _guardar_notas(notas_nuevas)
    return True, "Nota eliminada."


def _guardar_notas(notas):
    with open(NOTAS_DB, mode='w', encoding='utf-8') as f:
        json.dump(notas, f, ensure_ascii=False, indent=2)


# ============================================================
# UTILIDADES
# ============================================================
def formatear_moneda(valor):
    """Formatea un número como $1,234.56 MXN."""
    try:
        num = float(valor)
    except (ValueError, TypeError):
        return "$0.00 MXN"
    return f"${num:,.2f} MXN"


def calcular_totales(items, incluye_iva):
    """Calcula subtotal, IVA y total a partir de los items."""
    subtotal = 0.0
    for item in items:
        try:
            cant = int(item.get("cantidad", 0))
        except (ValueError, TypeError):
            cant = 0
        try:
            precio = float(item.get("precio_unitario", 0))
        except (ValueError, TypeError):
            precio = 0.0
        subtotal += cant * precio

    iva = subtotal * 0.16 if incluye_iva else 0.0
    total = subtotal + iva

    return {
        "subtotal": round(subtotal, 2),
        "iva": round(iva, 2),
        "total": round(total, 2),
    }


def sanitizar_nombre(texto):
    """Convierte un texto en algo seguro para nombre de archivo."""
    texto = texto.lower().strip()
    reemplazos = {'á':'a','à':'a','ä':'a','â':'a','é':'e','è':'e','ë':'e','ê':'e',
                  'í':'i','ì':'i','ï':'i','î':'i','ó':'o','ò':'o','ö':'o','ô':'o',
                  'ú':'u','ù':'u','ü':'u','û':'u','ñ':'n'}
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    texto = re.sub(r'[^a-z0-9_-]+', '_', texto)
    return texto.strip('_') or "sin_nombre"


def _obtener_logo_html():
    """Devuelve el HTML del logo para la nota."""
    if LOGO_PNG.exists():
        return '<img src="../../assets/LogoAluze.png" alt="Aluze" class="logo-img">'
    return '<h2 style="color:#fff;margin:0;letter-spacing:3px;font-weight:800;">ALUZE</h2>'


# ============================================================
# GENERACIÓN DE HTML
# ============================================================
def generar_nota_html(nota):
    """
    Genera el HTML de la nota y lo guarda.
    Devuelve la ruta relativa (string) o None si falla.
    """
    folio = nota["folio"]
    cliente = nota.get("cliente", {})
    items = nota.get("items", [])
    fecha = nota.get("fecha", datetime.now().strftime("%d/%m/%Y"))
    incluye_iva = nota.get("incluye_iva", False)
    anticipo = nota.get("anticipo", 0)
    autorizo = nota.get("autorizo", "")

    totales = calcular_totales(items, incluye_iva)
    subtotal = totales["subtotal"]
    iva = totales["iva"]
    total = totales["total"]

    try:
        anticipo_num = float(anticipo)
    except (ValueError, TypeError):
        anticipo_num = 0.0
    saldo = total - anticipo_num

    nombre_e = html.escape(cliente.get("nombre", ""))
    contacto_e = html.escape(cliente.get("contacto", ""))
    domicilio_e = html.escape(cliente.get("domicilio", ""))
    otros_e = html.escape(cliente.get("otros", ""))
    autorizo_e = html.escape(autorizo)

    filas_items = []
    for item in items:
        cant = item.get("cantidad", 0)
        desc = html.escape(item.get("descripcion", "")).replace("\n", "<br>")
        medida = html.escape(item.get("medida", ""))
        try:
            precio = float(item.get("precio_unitario", 0))
        except (ValueError, TypeError):
            precio = 0.0
        try:
            cant_int = int(cant)
        except (ValueError, TypeError):
            cant_int = 0
        tot_item = cant_int * precio

        filas_items.append(f"""
          <tr>
            <td class="col-cant">{cant_int}</td>
            <td class="col-desc">{desc}</td>
            <td class="col-medida">{medida}</td>
            <td class="col-precio">{formatear_moneda(precio)}</td>
            <td class="col-total">{formatear_moneda(tot_item)}</td>
          </tr>""")

    if incluye_iva:
        fila_iva = f"""
          <tr class="fila-totales-sec">
            <td class="lbl-total">IVA (16%):</td>
            <td class="val-total">{formatear_moneda(iva)}</td>
          </tr>"""
    else:
        fila_iva = ""

    logo_html = _obtener_logo_html()

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nota de Venta - Folio {folio} | Aluze</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0f172a;
    margin: 0;
    padding: 20px;
    display: flex;
    justify-content: center;
    min-height: 100vh;
  }}
  .nota {{
    background: #fff;
    width: 100%;
    max-width: 820px;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }}
  .header {{
    background: linear-gradient(135deg, #973359 0%, #7f2a4a 100%);
    color: #fff;
    padding: 24px 30px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 20px;
  }}
  .header-left {{ flex: 1; min-width: 200px; }}
  .logo-img {{ max-width: 140px; height: auto; margin-bottom: 8px;
               filter: brightness(0) invert(1); }}
  .empresa-info {{ font-size: 11px; line-height: 1.5; opacity: 0.9; }}
  .header-right {{ text-align: right; }}
  .folio-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: 2px;
                  opacity: 0.9; margin-bottom: 4px; }}
  .folio-numero {{ font-size: 26px; font-weight: 800; }}
  .fecha {{ font-size: 12px; margin-top: 6px; opacity: 0.9; }}

  .body {{ padding: 30px; }}
  .titulo-nota {{ font-size: 16px; font-weight: 800; color: #973359;
                  text-transform: uppercase; letter-spacing: 2px;
                  margin: 0 0 20px; }}

  .seccion {{ margin-bottom: 24px; }}
  .seccion-titulo {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #973359;
    font-weight: 800;
    border-bottom: 2px solid #f1f5f9;
    padding-bottom: 6px;
    margin-bottom: 12px;
  }}
  .cliente-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }}
  @media (max-width: 600px) {{
    .cliente-grid {{ grid-template-columns: 1fr; }}
  }}
  .campo-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: 1px;
                  color: #94a3b8; font-weight: 700; margin-bottom: 2px; }}
  .campo-valor {{ font-size: 14px; color: #1e293b; font-weight: 500; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  thead {{ background: #973359; color: #fff; }}
  thead th {{ padding: 10px 8px; text-align: left; font-weight: 700;
              font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }}
  tbody tr {{ border-bottom: 1px solid #f1f5f9; }}
  tbody tr:last-child {{ border-bottom: none; }}
  tbody td {{ padding: 10px 8px; color: #334155; vertical-align: top; }}
  .col-cant {{ width: 50px; text-align: center; font-weight: 700; }}
  .col-medida {{ width: 100px; }}
  .col-precio {{ width: 120px; text-align: right; }}
  .col-total {{ width: 120px; text-align: right; font-weight: 700; color: #973359; }}

  .totales {{
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }}
  .totales-tabla {{
    min-width: 280px;
    background: #f8fafc;
    border-radius: 10px;
    padding: 16px 20px;
  }}
  .totales-tabla table {{ font-size: 13px; }}
  .totales-tabla td {{ padding: 6px 8px; border: none; }}
  .lbl-total {{ text-align: left; color: #64748b; }}
  .val-total {{ text-align: right; color: #1e293b; font-weight: 600; }}
  .fila-total-final {{ border-top: 2px solid #973359; }}
  .fila-total-final td {{
    padding-top: 10px !important;
    font-size: 16px;
    font-weight: 800;
    color: #973359;
  }}

  .forma-pago {{
    background: #fdf2f8;
    border: 1px dashed #973359;
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 20px;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }}
  @media (max-width: 600px) {{
    .forma-pago {{ grid-template-columns: 1fr; }}
  }}
  .pago-item {{ text-align: center; }}
  .pago-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #831843;
    font-weight: 700;
    margin-bottom: 4px;
  }}
  .pago-valor {{ font-size: 16px; font-weight: 800; color: #973359; }}
  .pago-valor-texto {{ font-size: 14px; font-weight: 500; color: #1e293b; }}

  .validez {{
    text-align: center;
    font-size: 11px;
    color: #64748b;
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #f1f5f9;
  }}

  .footer {{
    background: #f8fafc;
    padding: 14px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    border-top: 1px solid #e2e8f0;
  }}
  .footer-texto {{ font-size: 11px; color: #64748b; }}
  .footer-botones {{ display: flex; gap: 8px; }}
  .btn-footer {{
    padding: 6px 14px;
    border-radius: 6px;
    border: none;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }}
  .btn-footer:hover {{ opacity: 0.85; }}
  .btn-imprimir {{ background: #973359; color: #fff; }}
  .btn-descargar {{ background: #fff; color: #334155; border: 1px solid #cbd5e1; }}

  /* ========================================== */
  /* CSS DE IMPRESIÓN — PDF igual que el HTML   */
  /* ========================================== */
  @media print {{
    * {{
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
      color-adjust: exact !important;
    }}
    @page {{
      size: A4;
      margin: 10mm;
    }}
    body {{
      background: #fff !important;
      padding: 0;
      margin: 0;
    }}
    .nota {{
      box-shadow: none;
      border-radius: 0;
      max-width: 100%;
      margin: 0 auto;
    }}
    .header {{
      background: linear-gradient(135deg, #973359 0%, #7f2a4a 100%) !important;
    }}
    thead {{
      background: #973359 !important;
    }}
    .forma-pago {{
      background: #fdf2f8 !important;
    }}
    .totales-tabla {{
      background: #f8fafc !important;
    }}
    .footer {{
      background: #f8fafc !important;
    }}
    .footer-botones {{
      display: none !important;
    }}
  }}
</style>
</head>
<body>
<div class="nota">
  <div class="header">
    <div class="header-left">
      {logo_html}
      <div class="empresa-info">
        Fábrica de Persianas &amp; Showroom<br>
        C. Joaquin Angulo 1493a, Santa Teresita<br>
        44600 Guadalajara, Jal., México<br>
        Tel: 33 1409 5263
      </div>
    </div>
    <div class="header-right">
      <div class="folio-label">Folio</div>
      <div class="folio-numero">#{folio}</div>
      <div class="fecha">{fecha}</div>
    </div>
  </div>

  <div class="body">
    <h1 class="titulo-nota">Nota de Venta</h1>

    <div class="seccion">
      <div class="seccion-titulo">Datos del Cliente</div>
      <div class="cliente-grid">
        <div class="campo">
          <div class="campo-label">Nombre</div>
          <div class="campo-valor">{nombre_e}</div>
        </div>
        <div class="campo">
          <div class="campo-label">Cel / Contacto</div>
          <div class="campo-valor">{contacto_e}</div>
        </div>
        <div class="campo">
          <div class="campo-label">Domicilio</div>
          <div class="campo-valor">{domicilio_e}</div>
        </div>
        <div class="campo">
          <div class="campo-label">Otros</div>
          <div class="campo-valor">{otros_e}</div>
        </div>
      </div>
    </div>

    <div class="seccion">
      <div class="seccion-titulo">Artículos</div>
      <table>
        <thead>
          <tr>
            <th class="col-cant">Cant.</th>
            <th class="col-desc">Descripción</th>
            <th class="col-medida">Medida</th>
            <th class="col-precio">Precio Unit.</th>
            <th class="col-total">Total</th>
          </tr>
        </thead>
        <tbody>
          {''.join(filas_items)}
        </tbody>
      </table>
    </div>

    <div class="totales">
      <div class="totales-tabla">
        <table>
          <tr>
            <td class="lbl-total">Subtotal:</td>
            <td class="val-total">{formatear_moneda(subtotal)}</td>
          </tr>
          {fila_iva}
          <tr class="fila-total-final">
            <td class="lbl-total">TOTAL:</td>
            <td class="val-total">{formatear_moneda(total)}</td>
          </tr>
        </table>
      </div>
    </div>

    <div class="forma-pago">
      <div class="pago-item">
        <div class="pago-label">Anticipo</div>
        <div class="pago-valor">{formatear_moneda(anticipo_num)}</div>
      </div>
      <div class="pago-item">
        <div class="pago-label">Saldo</div>
        <div class="pago-valor">{formatear_moneda(saldo)}</div>
      </div>
      <div class="pago-item">
        <div class="pago-label">Autorizó</div>
        <div class="pago-valor-texto">{autorizo_e if autorizo_e else "—"}</div>
      </div>
    </div>

    <div class="validez">
      Válida por 15 días a partir de la fecha de emisión
    </div>
  </div>

  <div class="footer">
    <div class="footer-texto">Gracias por su preferencia · Aluze Persianas</div>
    <div class="footer-botones">
      <button class="btn-footer btn-imprimir" onclick="window.print()">🖨️ PDF</button>
      <a class="btn-footer btn-descargar" href="#" download>📥 HTML</a>
    </div>
  </div>
</div>
</body>
</html>
"""

    nombre_cliente = sanitizar_nombre(cliente.get("nombre", "cliente"))
    nombre_archivo = f"{folio}_{nombre_cliente}.html"
    ruta_html = NOTAS_HTML / nombre_archivo

    try:
        ruta_html.write_text(html_content, encoding="utf-8")
        return ruta_html.relative_to(BASE_DIR).as_posix()
    except Exception as e:
        print(f"Error guardando nota HTML: {e}")
        return None