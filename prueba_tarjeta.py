"""
Prueba rápida del generador de tarjetas.
Genera una tarjeta de prueba y muestra la ruta.
"""
from core.tarjetas import generar_html

ruta = generar_html(
    9999,
    "Cliente Prueba",
    "Calle Falsa 123",
    "3312345678",
    "Sheer Elegance",
    "2 ventanas grandes",
    "$5,800 MXN",
    "Cliente muy amable",
    "09/10/2026 15:30",
    fecha_pautada="15/10/2026",
    hora_pautada="16:00",
    notas_internas="Llevar muestrario gris",
)

print("Generado:", ruta)