"""
Capa de datos: leer y escribir en el CSV.
Todo lo que toca la base de datos vive aquí.
"""
import csv
from config import DB_FILE


# ============================================================
# CONSTANTES
# ============================================================
CAMPOS_CSV = [
    "ID", "Fecha", "Cliente", "Domicilio", "Telefono",
    "Concepto", "Cotizacion", "Monto",
    "FechaPautada", "HoraPautada",
    "NotasCliente", "NotasInternas",
    "RutaHTML", "LinkIndividual"
]

# Estructura vieja con 11 columnas (incluye LinkIndividual)
CAMPOS_CSV_VIEJO_11 = [
    "ID", "Fecha", "Cliente", "Domicilio", "Telefono",
    "Concepto", "Cotizacion", "Monto", "Notas",
    "RutaHTML", "LinkIndividual"
]

# Estructura vieja con 10 columnas (SIN LinkIndividual)
CAMPOS_CSV_VIEJO_10 = [
    "ID", "Fecha", "Cliente", "Domicilio", "Telefono",
    "Concepto", "Cotizacion", "Monto", "Notas",
    "RutaHTML"
]


# ============================================================
# INICIALIZACIÓN + MIGRACIÓN
# ============================================================
def inicializar_csv():
    """
    Crea el CSV con encabezados si no existe.
    Si existe pero tiene estructura vieja, lo migra automáticamente.
    """
    if not DB_FILE.exists():
        _crear_csv_nuevo()
        return

    _migrar_si_necesario()


def _crear_csv_nuevo():
    """Crea un CSV vacío con la estructura nueva."""
    with open(DB_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(CAMPOS_CSV)


def _migrar_si_necesario():
    """
    Detecta si el CSV tiene estructura vieja y lo migra a la nueva.
    No pierde datos: rellena con vacíos las columnas nuevas.
    """
    with open(DB_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        filas = list(reader)

    if not header:
        return

    # Si ya está migrado, no hacer nada
    if header == CAMPOS_CSV:
        return

    # Detectar cuál de las estructuras viejas conocidas es
    if header == CAMPOS_CSV_VIEJO_11:
        tiene_link = True
    elif header == CAMPOS_CSV_VIEJO_10:
        tiene_link = False
    else:
        print(f"⚠️  El CSV tiene una estructura desconocida. No se migra.")
        print(f"   Esperado: {CAMPOS_CSV}")
        print(f"   Encontrado: {header}")
        return

    print("🔄 Migrando CSV a la nueva estructura...")

    # Migrar cada fila
    # Orden viejo:  ID, Fecha, Cliente, Domicilio, Telefono,
    #               Concepto, Cotizacion, Monto, Notas,
    #               RutaHTML[, LinkIndividual]
    # Orden nuevo:  ID, Fecha, Cliente, Domicilio, Telefono,
    #               Concepto, Cotizacion, Monto,
    #               FechaPautada, HoraPautada,
    #               NotasCliente, NotasInternas,
    #               RutaHTML, LinkIndividual
    nuevas_filas = []

    for fila in filas:
        if tiene_link:
            if len(fila) < 11:
                continue
            (id_reg, fecha, cliente, domicilio, telefono,
             concepto, cotizacion, monto, notas, ruta, link) = fila[:11]
        else:
            if len(fila) < 10:
                continue
            (id_reg, fecha, cliente, domicilio, telefono,
             concepto, cotizacion, monto, notas, ruta) = fila[:10]
            link = ""

        nueva_fila = [
            id_reg, fecha, cliente, domicilio, telefono,
            concepto, cotizacion, monto,
            "", "",           # FechaPautada, HoraPautada (vacías)
            notas, "",        # NotasCliente (lo que había en "Notas"), NotasInternas
            ruta, link
        ]
        nuevas_filas.append(nueva_fila)

    # Escribir de vuelta
    with open(DB_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(CAMPOS_CSV)
        writer.writerows(nuevas_filas)

    print(f"✅ CSV migrado: {len(nuevas_filas)} filas actualizadas.")


# ============================================================
# LEER
# ============================================================
def leer_registros():
    """
    Devuelve todos los registros del CSV como lista de listas.
    Cada fila tiene 14 campos (los nuevos).
    """
    if not DB_FILE.exists():
        return []
    with open(DB_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # saltar encabezado
        registros = []
        for r in reader:
            if len(r) < 14:
                r = r + [""] * (14 - len(r))
            registros.append(r[:14])
        return registros


def buscar_registro_por_id(id_buscar):
    """Devuelve la fila del registro con ese ID, o None."""
    for reg in leer_registros():
        if reg[0] == str(id_buscar):
            return reg
    return None


# ============================================================
# AGREGAR
# ============================================================
def agregar_registro(fila):
    """
    Añade una fila al final del CSV.
    `fila` debe tener 14 elementos en el orden de CAMPOS_CSV.
    """
    if len(fila) < 14:
        fila = list(fila) + [""] * (14 - len(fila))

    with open(DB_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fila[:14])


# ============================================================
# ACTUALIZAR (editar)
# ============================================================
def actualizar_registro(id_registro, fila_nueva):
    """
    Reemplaza la fila con ese ID por `fila_nueva`.
    Devuelve True si se encontró y actualizó.
    """
    if not DB_FILE.exists():
        return False

    if len(fila_nueva) < 14:
        fila_nueva = list(fila_nueva) + [""] * (14 - len(fila_nueva))
    fila_nueva = fila_nueva[:14]

    filas = []
    header = None
    encontrado = False

    with open(DB_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for reg in reader:
            if reg and reg[0] == str(id_registro):
                filas.append(fila_nueva)
                encontrado = True
            else:
                filas.append(reg)

    if not encontrado:
        return False

    with open(DB_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(CAMPOS_CSV)
        writer.writerows(filas)

    return True


# ============================================================
# ELIMINAR
# ============================================================
def eliminar_registro_por_id(id_eliminar):
    """
    Elimina la fila con el ID dado.
    Devuelve la ruta HTML a borrar (o None).
    """
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
                # RutaHTML está en el índice 12 (contando desde 0)
                if len(reg) > 12:
                    ruta_a_borrar = reg[12]
            else:
                nuevos.append(reg)

    with open(DB_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(nuevos)

    return ruta_a_borrar