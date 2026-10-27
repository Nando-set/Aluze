from config import *
from core.notas import inicializar_notas, generar_nota_html, siguiente_folio

# Inicializar
inicializar_notas()

# Nota de prueba
nota = {
    "folio": siguiente_folio(),
    "fecha": "23/10/2026",
    "cliente": {
        "nombre": "Sarai Berumen",
        "contacto": "33 1409 5263",
        "domicilio": "Chapala",
        "otros": "Cliente recurrente",
    },
    "items": [
        {
            "cantidad": 1,
            "descripcion": "Persiana Sheer Elegance (Basic)\n(Color LINO WHITE)",
            "medida": "1.3m x 1.5m",
            "precio_unitario": 1075,
        },
        {
            "cantidad": 1,
            "descripcion": "Persiana Sheer Elegance (Basic)\n(Color LINO WHITE)",
            "medida": "1.22m x 1.6m",
            "precio_unitario": 1076,
        },
    ],
    "incluye_iva": False,
    "anticipo": 1075,
    "autorizo": "Dani",
}

ruta = generar_nota_html(nota)
print(f"Nota generada: {ruta}")