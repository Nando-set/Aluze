"""
Generador del índice local de notas de venta.
Crea notas/index_notas.html agrupado por semanas.
Este archivo NO se sube a GitHub (es solo para uso local).
"""
import html
from datetime import datetime

from config import BASE_DIR, CARPETA_NOTAS, NOTAS_HTML, LOGO_PNG, LOGO_PNG_CLARO
from core.notas import leer_notas, calcular_totales, formatear_moneda
from core.tarjetas import obtener_semana_iso, formatear_fecha_larga


DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def regenerar_index_notas():
    """Genera notas/index_notas.html con todas las notas agrupadas por semana."""
    notas = leer_notas()

    if not notas:
        # Generar un índice vacío igual
        _generar_html([], [])
        return True

    # --- Agrupar por semana de la fecha de emisión ---
    semanas = {}
    for nota in notas:
        fecha_str = nota.get("fecha", "")
        try:
            fecha_dt = datetime.strptime(fecha_str.strip(), "%d/%m/%Y")
        except Exception:
            fecha_dt = datetime.now()

        year, week, lunes, domingo = obtener_semana_iso(fecha_dt)
        clave = f"{year}-Semana-{week:02d}"
        semanas.setdefault(clave, {
            "lunes": lunes,
            "domingo": domingo,
            "notas": []
        })["notas"].append((fecha_dt, nota))

    # --- Ordenar semanas (más reciente primero) ---
    claves_ordenadas = sorted(semanas.keys(), reverse=True)

    # --- Ordenar notas dentro de cada semana por fecha (más reciente primero) ---
    grupos = []
    for clave in claves_ordenadas:
        info = semanas[clave]
        info["notas"].sort(key=lambda x: x[0], reverse=True)
        grupos.append({
            "clave": clave,
            "lunes": info["lunes"],
            "domingo": info["domingo"],
            "notas": [n for (_, n) in info["notas"]],
        })

    _generar_html(grupos, notas)
    return True


def _obtener_logo_html():
    """Devuelve el HTML del logo para el índice."""
    if LOGO_PNG_CLARO.exists():
        return '<img src="../assets/LogoAluzeClaro.png" alt="Aluze" class="logo-img">'
    if LOGO_PNG.exists():
        return '<img src="../assets/LogoAluze.png" alt="Aluze" class="logo-img">'
    return '<h2 style="color:#f8fafc;margin:0;letter-spacing:3px;">ALUZE</h2>'


def _generar_html(grupos, notas_todas):
    """Genera el HTML del índice de notas."""
    total = len(notas_todas)

    # Contar notas de esta semana
    year_actual, week_actual, _, _ = obtener_semana_iso()
    clave_actual = f"{year_actual}-Semana-{week_actual:02d}"
    esta_semana = 0
    for g in grupos:
        if g["clave"] == clave_actual:
            esta_semana = len(g["notas"])
            break

    # Suma total
    suma_total = 0.0
    for nota in notas_todas:
        items = nota.get("items", [])
        incluye_iva = nota.get("incluye_iva", False)
        totales = calcular_totales(items, incluye_iva)
        suma_total += totales["total"]

    logo_html = _obtener_logo_html()

    # Bloques por semana
    bloques = []
    for g in grupos:
        clave = g["clave"]
        lunes_str = g["lunes"].strftime("%d/%m/%Y")
        domingo_str = g["domingo"].strftime("%d/%m/%Y")
        cantidad = len(g["notas"])

        es_actual = clave == clave_actual

        tarjetas = []
        for nota in g["notas"]:
            folio = nota.get("folio", "????")
            cliente = nota.get("cliente", {})
            nombre = cliente.get("nombre", "Sin nombre")
            fecha = nota.get("fecha", "")
            items = nota.get("items", [])
            incluye_iva = nota.get("incluye_iva", False)
            totales = calcular_totales(items, incluye_iva)
            total = totales["total"]

            ruta_html = nota.get("ruta_html", "")
            # Convertir ruta relativa al proyecto en ruta relativa al índice
            if ruta_html:
                # ruta_html = "notas/html/0001_xxx.html"
                # El index está en "notas/index_notas.html"
                # Entonces necesitamos quitar "notas/" del principio
                url_nota = ruta_html.replace("notas/", "", 1)
            else:
                url_nota = ""

            nombre_e = html.escape(nombre)
            folio_e = html.escape(folio)
            fecha_e = html.escape(fecha)

            iva_badge = '<span class="badge-iva">IVA</span>' if incluye_iva else ""

            tarjetas.append(f"""
            <a class="nota-card" href="{html.escape(url_nota)}" target="_blank">
              <div class="nota-head">
                <span class="folio">#{folio_e}</span>
                <span class="total">{formatear_moneda(total)}</span>
              </div>
              <div class="cliente">👤 {nombre_e}</div>
              <div class="fecha">📅 {fecha_e} {iva_badge}</div>
              <div class="nota-cta">Ver nota →</div>
            </a>""")

        clase = "semana semana-actual" if es_actual else "semana"
        etiqueta = ' <span class="etiqueta-actual">ACTUAL</span>' if es_actual else ""

        bloques.append(f"""
        <section class="{clase}">
          <h2>📅 {clave}{etiqueta} <span class="rango">({lunes_str} → {domingo_str})</span>
            <span class="badge">{cantidad} nota{"s" if cantidad != 1 else ""}</span>
          </h2>
          <div class="grid">
            {''.join(tarjetas)}
          </div>
        </section>""")

    contenido = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aluze | Índice de Notas</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    margin: 0;
    padding: 20px;
  }}
  .header {{
    text-align: center;
    margin-bottom: 24px;
    padding-bottom: 20px;
    border-bottom: 2px solid #1e293b;
  }}
  .header img {{ max-width: 180px; height: auto; }}
  .header h1 {{ font-size: 22px; margin: 12px 0 4px; color: #f8fafc; }}
  .header p {{ color: #94a3b8; font-size: 13px; margin: 0; }}
  .contador {{
    display: flex;
    justify-content: center;
    gap: 14px;
    flex-wrap: wrap;
    margin-top: 14px;
  }}
  .contador .stat {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 10px 18px;
  }}
  .contador .num {{
    font-size: 22px;
    font-weight: 800;
    color: #f8fafc;
    display: block;
  }}
  .contador .lbl {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
    font-weight: 600;
  }}
  .contador .stat.destacado .num {{ color: #fbbf24; }}
  .contador .stat.dinero .num {{ color: #34d399; }}

  .semana {{ margin-bottom: 30px; }}
  .semana > h2 {{
    font-size: 16px;
    color: #f8fafc;
    border-left: 4px solid #973359;
    padding-left: 10px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .semana-actual > h2 {{ border-left-color: #34d399; }}
  .rango {{ font-size: 12px; color: #94a3b8; font-weight: 400; }}
  .badge {{
    background: #334155;
    color: #cbd5e1;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 10px;
    font-weight: 600;
  }}
  .semana-actual .badge {{ background: #064e3b; color: #6ee7b7; }}
  .etiqueta-actual {{
    background: #064e3b;
    color: #6ee7b7;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 6px;
    font-weight: 700;
    letter-spacing: 1px;
  }}

  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 14px;
  }}
  .nota-card {{
    display: block;
    text-decoration: none;
    background: #1e293b;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #334155;
    transition: transform 0.15s, border-color 0.15s;
    color: inherit;
    cursor: pointer;
  }}
  .nota-card:hover {{
    transform: translateY(-3px);
    border-color: #973359;
    box-shadow: 0 6px 20px rgba(151,51,89,0.2);
  }}
  .nota-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    gap: 10px;
  }}
  .folio {{ font-weight: 800; color: #973359; font-size: 16px; }}
  .total {{ color: #34d399; font-weight: 700; font-size: 14px; }}
  .cliente {{ font-size: 14px; color: #f8fafc; font-weight: 600; margin-bottom: 6px; }}
  .fecha {{ font-size: 12px; color: #94a3b8; }}
  .badge-iva {{
    background: #fbbf24;
    color: #78350f;
    font-size: 9px;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 700;
    margin-left: 6px;
  }}
  .nota-cta {{
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid #334155;
    font-size: 12px;
    color: #973359;
    font-weight: 600;
  }}

  .vacio {{
    text-align: center;
    color: #64748b;
    padding: 60px 20px;
    font-size: 15px;
  }}
  footer {{
    text-align: center;
    color: #475569;
    font-size: 12px;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #1e293b;
  }}
</style>
</head>
<body>
  <div class="header">
    {logo_html}
    <h1>Índice de Notas de Venta</h1>
    <p>Uso local · Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <div class="contador">
      <div class="stat"><span class="num">{total}</span><span class="lbl">Total</span></div>
      <div class="stat destacado"><span class="num">{esta_semana}</span><span class="lbl">Esta semana</span></div>
      <div class="stat dinero"><span class="num">{formatear_moneda(suma_total)}</span><span class="lbl">Suma total</span></div>
    </div>
  </div>

  <div>
    {''.join(bloques) if bloques else '<div class="vacio">No hay notas emitidas aún.</div>'}
  </div>
  <footer>Aluze Persianas · Índice local (no se sube a GitHub)</footer>
</body>
</html>
"""

    ruta = CARPETA_NOTAS / "index_notas.html"
    ruta.write_text(contenido, encoding="utf-8")