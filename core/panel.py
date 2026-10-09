"""
Generador del panel central (index.html).
Aquí vive TODO lo relacionado con el listado general de cotizaciones.
"""
import html
from datetime import datetime

from config import INDEX_HTML
from core.datos import leer_registros
from core.tarjetas import obtener_semana_iso, obtener_logo_html


def regenerar_index():
    registros = leer_registros()
    if not registros:
        # Generar un panel vacío igualmente
        pass

    semanas = {}
    for reg in registros:
        try:
            fecha_dt = datetime.strptime(reg[1], "%d/%m/%Y %H:%M")
        except Exception:
            fecha_dt = datetime.now()
        year, week, lunes, domingo = obtener_semana_iso(fecha_dt)
        clave = f"{year}-Semana-{week:02d}"
        semanas.setdefault(clave, {"lunes": lunes, "domingo": domingo, "registros": []})["registros"].append(reg)

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

    logo_html = obtener_logo_html(desde_subcarpeta=False, claro=True)
    bloques = []

    for clave in sorted(semanas.keys(), reverse=True):
        info = semanas[clave]
        lunes = info["lunes"].strftime("%d/%m/%Y")
        domingo = info["domingo"].strftime("%d/%m/%Y")
        cantidad = len(info["registros"])

        year_actual, week_actual, _, _ = obtener_semana_iso()
        es_actual = clave == f"{year_actual}-Semana-{week_actual:02d}"
        clase_semana = "semana semana-actual" if es_actual else "semana"

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
  .header img {{ max-width: 180px; height: auto; }}
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
    <div class="top-nav" style="margin-top: 14px;">
      <a href="catalogo.html" style="display: inline-block; padding: 10px 22px;
         border-radius: 10px; background: #973359; color: #fff;
         text-decoration: none; font-weight: 700; font-size: 14px;">
        🛍️ Ver catálogo de productos
      </a>
    </div>
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

        let pasaFiltro = true;
        if (filtroActual === 'semana' && semana !== SEMANA_ACTUAL) pasaFiltro = false;
        if (filtroActual === 'mes' && mes !== MES_ACTUAL) pasaFiltro = false;

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