"""
Capa de datos: leer y escribir en el CSV.
Todo lo que toca la base de datos vive aquí.
"""
import csv
from config import DB_FILE


def inicializar_csv():
    """Crea el CSV con encabezados si no existe."""
    if not DB_FILE.exists():
        with open(DB_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Fecha", "Cliente", "Domicilio", "Telefono",
                "Concepto", "Cotizacion", "Monto", "Notas",
                "RutaHTML", "LinkIndividual"
            ])


def leer_registros():
    """Devuelve todos los registros del CSV como lista de listas."""
    if not DB_FILE.exists():
        return []
    with open(DB_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # saltar encabezado
        return [r for r in reader if len(r) >= 9]


def agregar_registro(fila):
    """Añade una fila al final del CSV."""
    with open(DB_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fila)


def eliminar_registro_por_id(id_eliminar):
    """Elimina la fila con el ID dado. Devuelve la ruta HTML a borrar (o None)."""
    if not DB_FILE.exists():
        return None

    nuevos = []
    ruta_a_borrar = None

    with open(DB_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        nuevos.append(header)
        for reg in reader:
            if reg and reg[0] == str(id_eliminar):
                if len(reg) > 9:
                    ruta_a_borrar = reg[9]
            else:
                nuevos.append(reg)

    with open(DB_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(nuevos)

    return ruta_a_borrar