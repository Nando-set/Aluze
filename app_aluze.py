import os
import csv
import re
import html
import shutil
import subprocess
import webbrowser
import urllib.parse
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# ============================================================
# CONFIGURACIÓN (EDITA SOLO ESTAS 3 LÍNEAS SI CAMBIA ALGO)
# ============================================================
GITHUB_USER = "Nando-set"
GITHUB_REPO = "Aluze"
GITHUB_BRANCH = "main"

# ============================================================
# RUTAS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "base_datos_clientes.csv"
LOGO_SVG = BASE_DIR / "LogoAluze.svg"
LOGO_PNG = BASE_DIR / "LogoAluze.png"
CARPETA_COTIZACIONES = BASE_DIR / "cotizaciones"
CARPETA_ASSETS = BASE_DIR / "assets"
INDEX_HTML = BASE_DIR / "index.html"

URL_BASE = f"https://{GITHUB_USER.lower()}.github.io/{GITHUB_REPO}/"


# ============================================================
# UTILIDADES
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


def inicializar_estructura():
    CARPETA_COTIZACIONES.mkdir(exist_ok=True)
    CARPETA_ASSETS.mkdir(exist_ok=True)

    if LOGO_SVG.exists():
        shutil.copy2(LOGO_SVG, CARPETA_ASSETS / "LogoAluze.svg")

    if not DB_FILE.exists():
        with open(DB_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Fecha", "Cliente", "Domicilio", "Telefono",
                "Concepto", "Cotizacion", "Monto", "Notas",
                "RutaHTML", "LinkIndividual"
            ])


def obtener_logo_svg_inline():
    if LOGO_SVG.exists():
        try:
            contenido = LOGO_SVG.read_text(encoding="utf-8")
            contenido = re.sub(r'\s(width|height)="[^"]*"', '', contenido, count=2)
            if "<svg" in contenido:
                return contenido
        except Exception:
            pass
    return '<h2 style="color:#973359;margin:0;letter-spacing:3px;">ALUZE</h2>'


# ============================================================
# GENERAR TARJETA HTML INDIVIDUAL
# ============================================================
def generar_html(id_reg, cliente, domicilio, telefono, concepto,
                 cotizacion, monto, notas, fecha):
    year, week, _, _ = obtener_semana_iso()
    nombre_semana = f"{year}-Semana-{week:02d}"
    carpeta_semana = CARPETA_COTIZACIONES / nombre_semana
    carpeta_semana.mkdir(parents=True, exist_ok=True)

    cliente_seguro = sanitizar_nombre(cliente)
    nombre_archivo = f"cotizacion_{id_reg}_{cliente_seguro}.html"
    ruta_html = carpeta_semana / nombre_archivo
    ruta_relativa = ruta_html.relative_to(BASE_DIR).as_posix()

    cliente_e = html.escape(cliente)
    domicilio_e = html.escape(domicilio)
    telefono_e = html.escape(telefono)
    concepto_e = html.escape(concepto)
    cotizacion_e = html.escape(cotizacion)
    monto_e = html.escape(monto)
    notas_e = html.escape(notas)

    maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(domicilio)}"
    telefono_limpio = re.sub(r'\D', '', telefono)
    whatsapp_url = f"https://wa.me/{telefono_limpio}"
    logo_html = obtener_logo_svg_inline()

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
  .tagline {{ font-size: 10px; text-transform: uppercase; letter-spacing: 3px; color: #64748b; font-weight: 600; }}
  .card-title {{ font-size: 13px; text-transform: uppercase; letter-spacing: 1.5px; color: #973359; font-weight: 700; margin: 0 0 20px; text-align: center; }}
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
  .toast {{ position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #10b981; color: #fff; padding: 10px 20px; border-radius: 30px; font-size: 13px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: none; z-index: 1000; }}
  .footer {{ text-align: center; font-size: 11px; color: #94a3b8; margin-top: 20px; border-top: 1px solid #f1f5f9; padding-top: 15px; }}
</style>
</head>
<body>
<div class="card">
  <div class="header-brand">
    <div class="logo-container">{logo_html}</div>
    <div class="tagline">Persianas &amp; Decoración</div>
  </div>
  <div class="card-title">Tarjeta de Cotización</div>

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
    <a class="map-link" href="{maps_url}" target="_blank">📍 Abrir ubicación en Google Maps</a>
  </div>
  <div class="section">
    <div class="label">Detalles de la Cotización</div>
    <div class="box" id="val-detalles">{cotizacion_e}</div>
  </div>
  <div class="section">
    <div class="label">Notas / Observaciones</div>
    <div class="box" id="val-notas" style="border-left-color:#d97706;">{notas_e}</div>
  </div>
  <div class="price-box">
    <div class="price-label">Monto Aproximado</div>
    <div class="price-value" id="val-monto">{monto_e}</div>
  </div>
  <button class="btn-universal-copy" onclick="copiarTodo()">📋 Copiar toda la información para chat</button>
  <div class="footer">Generado el {fecha} | Persianas Aluze</div>
</div>
<div id="toast" class="toast">¡Copiado!</div>
<script>
function mostrarToast(msg) {{
  const t = document.getElementById('toast');
  t.innerText = msg; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 2000);
}}
function copiarTexto(id, msg) {{
  const texto = document.getElementById(id).innerText;
  navigator.clipboard.writeText(texto).then(() => mostrarToast(msg));
}}
function copiarTodo() {{
  const g = id => document.getElementById(id).innerText;
  let txt = `*COTIZACIÓN ALUZE*\\n`;
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
</script>
</body>
</html>
"""
    ruta_html.write_text(html_content, encoding="utf-8")
    return ruta_relativa


# ============================================================
# GENERAR INDEX.HTML (panel con filtros y contador)
# ============================================================
def regenerar_index():
    if not DB_FILE.exists():
        return

    with open(DB_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        registros = [r for r in reader if len(r) >= 9]

    # Semanas ISO
    semanas = {}
    for reg in registros:
        try:
            fecha_dt = datetime.strptime(reg[1], "%d/%m/%Y %H:%M")
        except Exception:
            fecha_dt = datetime.now()
        year, week, lunes, domingo = obtener_semana_iso(fecha_dt)
        clave = f"{year}-Semana-{week:02d}"
        semanas.setdefault(clave, {"lunes": lunes, "domingo": domingo, "registros": []})["registros"].append(reg)

    # Métricas globales
    total = len(registros)
    _, _, lunes_actual, domingo_actual = obtener_semana_iso()
    esta_semana = 0
    for reg in registros:
        try:
            fecha_dt = datetime.strptime(reg[1], "%d/%m/%Y %H:%M")
        except Exception:
            continue
        if lunes_actual <= fecha_dt <= (domingo_actual.replace(hour=23, minute=59, second=59)):
            esta_semana += 1

    logo_html = obtener_logo_svg_inline()
    bloques = []

    for clave in sorted(semanas.keys(), reverse=True):
        info = semanas[clave]
        lunes = info["lunes"].strftime("%d/%m/%Y")
        domingo = info["domingo"].strftime("%d/%m/%Y")
        cantidad = len(info["registros"])

        # Semana actual vs antigua
        year_actual, week_actual, _, _ = obtener_semana_iso()
        es_actual = clave == f"{year_actual}-Semana-{week_actual:02d}"
        clase_semana = "semana semana-actual" if es_actual else "semana"

        # Fecha de la semana para filtro por mes (YYYY-MM)
        mes_clave = info["lunes"].strftime("%Y-%m")

        tarjetas = []
        for reg in reversed(info["registros"]):
            id_reg, fecha, cliente, domicilio, telefono, concepto, cotizacion, monto, notas = reg[:9]
            ruta_html = reg[9] if len(reg) > 9 else ""
            cliente_e = html.escape(cliente)
            concepto_e = html.escape(concepto)
            monto_e = html.escape(monto)
            telefono_e = html.escape(telefono)
            notas_e = html.escape(notas[:100]) if notas else ""
            nota_html = f'<div class="nota">📝 {notas_e}{"..." if len(notas) > 100 else ""}</div>' if notas else ""
            tarjetas.append(f"""
            <a class="cot-card" href="{html.escape(ruta_html)}" target="_blank">
              <div class="cot-head">
                <span class="cliente">👤 {cliente_e}</span>
                <span class="monto">{monto_e}</span>
              </div>
              <div class="cot-info">📦 {concepto_e}</div>
              <div class="cot-info">📞 {telefono_e} &nbsp;|&nbsp; 🗓️ {html.escape(fecha)}</div>
              {nota_html}
              <div class="cot-cta">🔗 Ver cotización completa →</div>
            </a>""")

        bloques.append(f"""
        <section class="{clase_semana}" data-semana="{clave}" data-mes="{mes_clave}">
          <h2>📅 {clave} <span class="rango">({lunes} → {domingo})</span> <span class="badge">{cantidad} cotización{"es" if cantidad != 1 else ""}</span></h2>
          <div class="grid">{''.join(tarjetas)}</div>
        </section>""")

    mes_actual = datetime.now().strftime("%Y-%m")

    contenido = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aluze | Panel de Cotizaciones</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
  .header {{ text-align: center; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 2px solid #1e293b; }}
  .header svg {{ max-width: 180px; height: auto; }}
  .header h1 {{ font-size: 22px; margin: 12px 0 4px; color: #f8fafc; }}
  .header p {{ color: #94a3b8; font-size: 13px; margin: 0; }}
  .contador {{ display: flex; justify-content: center; gap: 14px; flex-wrap: wrap; margin-top: 14px; }}
  .contador .stat {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 10px 18px; }}
  .contador .num {{ font-size: 22px; font-weight: 800; color: #f8fafc; display: block; }}
  .contador .lbl {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; font-weight: 600; }}
  .contador .stat.destacado .num {{ color: #34d399; }}

  .controles {{ max-width: 640px; margin: 24px auto 30px; }}
  .buscador input {{ width: 100%; padding: 12px 16px; border-radius: 10px; border: 1px solid #334155; background: #1e293b; color: #f8fafc; font-size: 15px; outline: none; }}
  .buscador input:focus {{ border-color: #973359; }}
  .filtros {{ display: flex; gap: 8px; justify-content: center; margin-top: 12px; flex-wrap: wrap; }}
  .filtros button {{ padding: 8px 16px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #cbd5e1; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.15s; }}
  .filtros button:hover {{ border-color: #973359; color: #f8fafc; }}
  .filtros button.activo {{ background: #973359; border-color: #973359; color: #fff; }}

  .semana {{ margin-bottom: 30px; }}
  .semana h2 {{ font-size: 16px; color: #f8fafc; border-left: 4px solid #973359; padding-left: 10px; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .semana-actual h2 {{ border-left-color: #34d399; }}
  .rango {{ font-size: 12px; color: #94a3b8; font-weight: 400; }}
  .badge {{ background: #334155; color: #cbd5e1; font-size: 11px; padding: 3px 8px; border-radius: 10px; font-weight: 600; }}
  .semana-actual .badge {{ background: #064e3b; color: #6ee7b7; }}

  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }}
  .cot-card {{ display: block; text-decoration: none; background: #1e293b; border-radius: 12px; padding: 16px; border: 1px solid #334155; transition: transform 0.15s, border-color 0.15s; color: inherit; cursor: pointer; }}
  .cot-card:hover {{ transform: translateY(-3px); border-color: #973359; box-shadow: 0 6px 20px rgba(151,51,89,0.2); }}
  .cot-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 10px; }}
  .cliente {{ font-weight: 700; color: #f8fafc; font-size: 15px; }}
  .monto {{ color: #34d399; font-weight: 700; font-size: 15px; white-space: nowrap; }}
  .cot-info {{ font-size: 13px; color: #cbd5e1; margin-bottom: 5px; }}
  .nota {{ font-size: 12px; color: #fbbf24; font-style: italic; margin-top: 6px; }}
  .cot-cta {{ margin-top: 12px; padding-top: 10px; border-top: 1px solid #334155; font-size: 12px; color: #973359; font-weight: 600; }}
  .vacio {{ text-align: center; color: #64748b; padding: 40px; font-size: 15px; }}
  footer {{ text-align: center; color: #475569; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #1e293b; }}
</style>
</head>
<body>
  <div class="header">
    {logo_html}
    <h1>Panel de Cotizaciones</h1>
    <p>Persianas &amp; Decoración · Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <div class="contador">
      <div class="stat"><span class="num">{total}</span><span class="lbl">Total</span></div>
      <div class="stat destacado"><span class="num">{esta_semana}</span><span class="lbl">Esta semana</span></div>
      <div class="stat"><span class="num">{len(semanas)}</span><span class="lbl">Semanas</span></div>
    </div>
  </div>

  <div class="controles">
    <div class="buscador">
      <input type="text" id="buscador" placeholder="🔍 Buscar por cliente, concepto o teléfono..." oninput="aplicarFiltros()">
    </div>
    <div class="filtros">
      <button class="activo" data-filtro="todas" onclick="setFiltro('todas', this)">📋 Todas</button>
      <button data-filtro="semana" onclick="setFiltro('semana', this)">📅 Esta semana</button>
      <button data-filtro="mes" onclick="setFiltro('mes', this)">🗓️ Este mes</button>
    </div>
  </div>

  <div id="contenido">
    {''.join(bloques) if bloques else '<div class="vacio">No hay cotizaciones registradas aún.</div>'}
  </div>
  <footer>Persianas Aluze · Generado automáticamente</footer>

  <script>
    const SEMANA_ACTUAL = "{datetime.now().isocalendar()[0]}-Semana-{datetime.now().isocalendar()[1]:02d}";
    const MES_ACTUAL = "{mes_actual}";
    let filtroActual = "todas";

    function setFiltro(filtro, boton) {{
      filtroActual = filtro;
      document.querySelectorAll('.filtros button').forEach(b => b.classList.remove('activo'));
      boton.classList.add('activo');
      aplicarFiltros();
    }}

    function aplicarFiltros() {{
      const q = document.getElementById('buscador').value.toLowerCase();

      document.querySelectorAll('.semana').forEach(sec => {{
        const semana = sec.dataset.semana;
        const mes = sec.dataset.mes;

        // Filtro por botón
        let pasaFiltro = true;
        if (filtroActual === 'semana' && semana !== SEMANA_ACTUAL) pasaFiltro = false;
        if (filtroActual === 'mes' && mes !== MES_ACTUAL) pasaFiltro = false;

        // Filtro por búsqueda (dentro de la semana)
        let tarjetasVisibles = 0;
        sec.querySelectorAll('.cot-card').forEach(card => {{
          const coincide = card.innerText.toLowerCase().includes(q);
          card.style.display = coincide ? '' : 'none';
          if (coincide) tarjetasVisibles++;
        }});

        sec.style.display = (pasaFiltro && tarjetasVisibles > 0) ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>
"""
    INDEX_HTML.write_text(contenido, encoding="utf-8")


# ============================================================
# SUBIR A GITHUB (con pull previo para evitar conflictos)
# ============================================================
def subir_a_github():
    try:
        # 1. Añadir cambios locales
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True, capture_output=True)

        # 2. Commit (si no hay cambios, seguimos)
        msg = f"Actualización {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        r = subprocess.run(["git", "commit", "-m", msg], cwd=BASE_DIR, capture_output=True)
        commit_out = (r.stdout or b"").decode() + (r.stderr or b"").decode()
        if "nothing to commit" in commit_out or "nada para hacer commit" in commit_out:
            return True, "ℹ️ No había cambios nuevos que subir."

        # 3. Pull con rebase (trae cambios remotos sin crear merge commit)
        pull = subprocess.run(["git", "pull", "--rebase", "origin", GITHUB_BRANCH],
                              cwd=BASE_DIR, capture_output=True)
        pull_out = (pull.stdout or b"").decode() + (pull.stderr or b"").decode()

        if pull.returncode != 0:
            # Si el pull falla, abortamos el rebase para no dejar el repo en mal estado
            subprocess.run(["git", "rebase", "--abort"], cwd=BASE_DIR, capture_output=True)
            return False, ("⚠️ No se pudo sincronizar con GitHub.\n\n"
                           "Puede que haya cambios en el repo remoto que choquen.\n\n"
                           f"Detalle:\n{pull_out[:500]}")

        # 4. Push
        subprocess.run(["git", "push", "origin", GITHUB_BRANCH],
                       cwd=BASE_DIR, check=True, capture_output=True)

        return True, "✅ Subido a GitHub correctamente."
    except subprocess.CalledProcessError as e:
        error = (e.stderr or b"").decode() if e.stderr else str(e)
        return False, f"❌ Error:\n{error}"
    except FileNotFoundError:
        return False, "❌ Git no está instalado o no está en el PATH."
    except Exception as e:
        return False, f"❌ Error inesperado:\n{e}"


# ============================================================
# VENTANA DE LINKS
# ============================================================
class VentanaLinks(tk.Toplevel):
    def __init__(self, parent, link_individual, link_panel):
        super().__init__(parent)
        self.title("🔗 Links de la cotización")
        self.configure(bg="#1e293b")
        self.geometry("520x280")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text="✅ Cotización subida", bg="#1e293b", fg="#34d399",
                 font=("Segoe UI", 13, "bold")).pack(pady=(18, 4))
        tk.Label(self, text="Comparte estos links:", bg="#1e293b", fg="#94a3b8",
                 font=("Segoe UI", 10)).pack(pady=(0, 14))

        self._crear_bloque("🔗 Link individual (esta cotización)", link_individual)
        self._crear_bloque("📋 Link del panel completo (para tu jefe)", link_panel)

        tk.Label(self, text="⏱️ GitHub Pages tarda 30-60 seg en actualizar.",
                 bg="#1e293b", fg="#fbbf24", font=("Segoe UI", 8, "italic")).pack(pady=(4, 0))

        tk.Button(self, text="Cerrar", bg="#334155", fg="white",
                  font=("Segoe UI", 10), relief=tk.FLAT, cursor="hand2",
                  command=self.destroy).pack(pady=8)

    def _crear_bloque(self, titulo, url):
        frame = tk.Frame(self, bg="#1e293b")
        frame.pack(fill=tk.X, padx=20, pady=6)
        tk.Label(frame, text=titulo, bg="#1e293b", fg="#cbd5e1",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        row = tk.Frame(frame, bg="#1e293b")
        row.pack(fill=tk.X, pady=(2, 0))
        entry = tk.Entry(row, font=("Segoe UI", 9), bg="#0f172a", fg="#f8fafc",
                         relief=tk.FLAT, insertbackground="white")
        entry.insert(0, url)
        entry.configure(state="readonly")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        tk.Button(row, text="📋", bg="#973359", fg="white", relief=tk.FLAT,
                  cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=lambda u=url: self._copiar(u)).pack(side=tk.LEFT, padx=(4, 0))
        tk.Button(row, text="🌐", bg="#0ea5e9", fg="white", relief=tk.FLAT,
                  cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=lambda u=url: webbrowser.open(u)).pack(side=tk.LEFT, padx=(4, 0))

    def _copiar(self, texto):
        self.clipboard_clear()
        self.clipboard_append(texto)
        messagebox.showinfo("Copiado", "Link copiado al portapapeles.", parent=self)


# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
class AppAluze:
    def __init__(self, root):
        self.root = root
        self.root.title("Aluze - Sistema de Cotizaciones")
        self.root.geometry("1150x780")
        self.root.configure(bg="#0f172a")

        inicializar_estructura()

        style = ttk.Style()
        style.theme_use('clam')

        self.sidebar = tk.Frame(root, bg="#1e293b", width=410, padx=15, pady=15)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.main_panel = tk.Frame(root, bg="#0f172a", padx=15, pady=15)
        self.main_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.crear_formulario()
        self.crear_dashboard()
        self.cargar_registros()
        regenerar_index()

    def crear_formulario(self):
        logo_mostrado = False
        if LOGO_PNG.exists():
            try:
                self.logo_img = tk.PhotoImage(file=str(LOGO_PNG))
                factor = max(1, self.logo_img.width() // 220)
                if factor > 1:
                    self.logo_img = self.logo_img.subsample(factor, factor)
                tk.Label(self.sidebar, image=self.logo_img, bg="#1e293b").pack(pady=(0, 8))
                logo_mostrado = True
            except Exception as e:
                print(f"Error cargando PNG: {e}")
        if not logo_mostrado:
            tk.Label(self.sidebar, text="LogoAluze.png no encontrado",
                     bg="#1e293b", fg="#fbbf24",
                     font=("Segoe UI", 8, "italic")).pack(pady=(0, 8))

        tk.Label(self.sidebar, text="NUEVA COTIZACIÓN", bg="#1e293b",
                 fg="#f8fafc", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        canvas = tk.Canvas(self.sidebar, bg="#1e293b", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.sidebar, orient="vertical", command=canvas.yview)
        self.form_frame = tk.Frame(canvas, bg="#1e293b")
        self.form_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.entries = {}
        campos = [
            ("Nombre del Cliente", "entry"),
            ("Domicilio", "entry"),
            ("Teléfono Celular", "entry"),
            ("Concepto / Sistema", "entry"),
            ("Detalles de Cotización", "text"),
            ("Monto Aproximado", "entry"),
            ("Notas / Citas / Observaciones", "text"),
        ]
        for label_text, tipo in campos:
            tk.Label(self.form_frame, text=label_text, bg="#1e293b",
                     fg="#94a3b8", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 2))
            if tipo == "entry":
                ent = tk.Entry(self.form_frame, font=("Segoe UI", 10), bg="#334155",
                               fg="#f8fafc", insertbackground="white", relief=tk.FLAT)
                ent.pack(fill=tk.X, ipady=4)
                self.entries[label_text] = ent
            else:
                txt = tk.Text(self.form_frame, height=4, font=("Segoe UI", 10), bg="#334155",
                              fg="#f8fafc", insertbackground="white", relief=tk.FLAT)
                txt.pack(fill=tk.X)
                self.entries[label_text] = txt

        self.subir_auto = tk.BooleanVar(value=True)
        tk.Checkbutton(self.form_frame, text="☁️ Subir a GitHub al guardar",
                       variable=self.subir_auto, bg="#1e293b", fg="#cbd5e1",
                       selectcolor="#334155", activebackground="#1e293b",
                       activeforeground="#f8fafc", font=("Segoe UI", 9),
                       cursor="hand2").pack(anchor="w", pady=(14, 6))

        tk.Button(self.form_frame, text="✨ Generar Tarjeta y Guardar",
                  bg="#973359", fg="white", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, cursor="hand2",
                  command=self.guardar_cotizacion).pack(fill=tk.X, pady=(4, 8), ipady=8)

        tk.Button(self.form_frame, text="🌐 Abrir panel web",
                  bg="#0ea5e9", fg="white", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, cursor="hand2",
                  command=lambda: webbrowser.open(URL_BASE)).pack(fill=tk.X, pady=(0, 8), ipady=6)

        tk.Button(self.form_frame, text="☁️ Subir TODO a GitHub",
                  bg="#16a34a", fg="white", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, cursor="hand2",
                  command=self.accion_subir_github).pack(fill=tk.X, pady=(0, 8), ipady=6)

        tk.Button(self.form_frame, text="🔄 Forzar actualización (pull + push)",
                  bg="#7c3aed", fg="white", font=("Segoe UI", 9, "bold"),
                  relief=tk.FLAT, cursor="hand2",
                  command=self.accion_forzar_actualizacion).pack(fill=tk.X, pady=(0, 8), ipady=5)

        tk.Button(self.form_frame, text="🗑️ Borrar TODAS las cotizaciones",
                  bg="#7f1d1d", fg="#fecaca", font=("Segoe UI", 9, "bold"),
                  relief=tk.FLAT, cursor="hand2",
                  command=self.borrar_todo).pack(fill=tk.X, pady=(0, 8), ipady=5)

    def crear_dashboard(self):
        tk.Label(self.main_panel, text="REGISTRO DE COTIZACIONES",
                 bg="#0f172a", fg="#f8fafc",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))

        self.canvas_dash = tk.Canvas(self.main_panel, bg="#0f172a", highlightthickness=0)
        self.scrollbar_dash = ttk.Scrollbar(self.main_panel, orient="vertical", command=self.canvas_dash.yview)
        self.cards_frame = tk.Frame(self.canvas_dash, bg="#0f172a")
        self.cards_frame.bind("<Configure>",
                              lambda e: self.canvas_dash.configure(scrollregion=self.canvas_dash.bbox("all")))
        self.canvas_dash.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.canvas_dash.configure(yscrollcommand=self.scrollbar_dash.set)
        self.canvas_dash.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar_dash.pack(side=tk.RIGHT, fill=tk.Y)

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

            with open(DB_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([id_reg, fecha, cliente, domicilio, telefono,
                                 concepto, cotizacion, monto, notas,
                                 ruta_relativa, link_individual])

            regenerar_index()
            self.limpiar_formulario()
            self.cargar_registros()

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

    def cargar_registros(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        if not DB_FILE.exists():
            return

        with open(DB_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            registros = [r for r in reader if len(r) >= 9]

        if not registros:
            tk.Label(self.cards_frame, text="No hay cotizaciones registradas aún.",
                     bg="#0f172a", fg="#64748b", font=("Segoe UI", 11)).pack(anchor="w", pady=20)
            return

        for reg in reversed(registros):
            id_reg, fecha, cliente, domicilio, telefono, concepto, cotizacion, monto, notas = reg[:9]
            ruta_html = reg[9] if len(reg) > 9 else ""
            link_ind = reg[10] if len(reg) > 10 else ""

            card = tk.Frame(self.cards_frame, bg="#1e293b", padx=15, pady=12)
            card.pack(fill=tk.X, pady=6, padx=5)

            top = tk.Frame(card, bg="#1e293b")
            top.pack(fill=tk.X)
            tk.Label(top, text=cliente, bg="#1e293b", fg="#f8fafc",
                     font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
            tk.Label(top, text=monto, bg="#1e293b", fg="#34d399",
                     font=("Segoe UI", 11, "bold")).pack(side=tk.RIGHT)

            tk.Label(card, text=f"Concepto: {concepto} | Tel: {telefono} | {fecha}",
                     bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 6))

            if notas:
                tk.Label(card, text=f"📝 {notas[:100]}", bg="#1e293b", fg="#fbbf24",
                         font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(0, 6))

            btn_frame = tk.Frame(card, bg="#1e293b")
            btn_frame.pack(anchor="w", pady=(4, 0))

            tk.Button(btn_frame, text="🌐 Abrir", bg="#0ea5e9", fg="white",
                      font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
                      command=lambda r=ruta_html: self.abrir_html(r)).pack(side=tk.LEFT, padx=(0, 6))

            if link_ind:
                tk.Button(btn_frame, text="📋 Copiar link", bg="#973359", fg="white",
                          font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
                          command=lambda u=link_ind: self.copiar_al_portapapeles(u)).pack(side=tk.LEFT, padx=(0, 6))

            tel_limpio = re.sub(r'\D', '', telefono)
            tk.Button(btn_frame, text="💬 WA", bg="#16a34a", fg="white",
                      font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
                      command=lambda t=tel_limpio: webbrowser.open(f"https://wa.me/{t}")).pack(side=tk.LEFT, padx=(0, 6))

            tk.Button(btn_frame, text="🗑️", bg="#ef4444", fg="white",
                      font=("Segoe UI", 8, "bold"), relief=tk.FLAT,
                      command=lambda i=id_reg: self.eliminar_registro(i)).pack(side=tk.LEFT)

    def copiar_al_portapapeles(self, texto):
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        messagebox.showinfo("Copiado", "Link copiado al portapapeles.")

    def abrir_html(self, ruta_relativa):
        if not ruta_relativa:
            messagebox.showwarning("Aviso", "Este registro no tiene HTML asociado.")
            return
        ruta = BASE_DIR / ruta_relativa
        if ruta.exists():
            webbrowser.open(ruta.as_uri())
        else:
            messagebox.showerror("Error", f"No se encontró:\n{ruta}")

    def eliminar_registro(self, id_eliminar):
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta cotización del registro?"):
            return
        nuevos = []
        ruta_a_borrar = None
        with open(DB_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            nuevos.append(header)
            for reg in reader:
                if reg and reg[0] == str(id_eliminar):
                    if len(reg) > 9:
                        ruta_a_borrar = BASE_DIR / reg[9]
                else:
                    nuevos.append(reg)
        with open(DB_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(nuevos)
        if ruta_a_borrar and ruta_a_borrar.exists():
            try:
                ruta_a_borrar.unlink()
            except Exception:
                pass
        regenerar_index()
        self.cargar_registros()

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
            self.cargar_registros()
            messagebox.showinfo("Listo",
                                "✅ Todo borrado.\n\n"
                                "Recuerda pulsar '☁️ Subir TODO a GitHub'\n"
                                "para reflejar el cambio en la nube.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo borrar todo:\n\n{e}")

    def accion_subir_github(self):
        exito, msg = subir_a_github()
        if exito:
            messagebox.showinfo("GitHub", msg)
        else:
            messagebox.showerror("GitHub", msg)

    def accion_forzar_actualizacion(self):
        """Pull forzado + push, con manejo de errores."""
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


if __name__ == "__main__":
    root = tk.Tk()
    app = AppAluze(root)
    root.mainloop()