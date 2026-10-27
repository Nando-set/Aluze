"""
Sistema de notificaciones push vía ntfy.
Envía notificaciones al celular cuando se agenda una cita.
"""
import requests
from datetime import datetime, timedelta

from config import NTFY_TOPIC, NTFY_SERVER


# ============================================================
# NOTIFICACIÓN INMEDIATA
# ============================================================
def enviar_notificacion(titulo, mensaje, prioridad="default", tags=None):
    """
    Envía una notificación push inmediata al celular.

    Args:
        titulo: Título de la notificación
        mensaje: Cuerpo del mensaje
        prioridad: "min", "low", "default", "high", "max"
        tags: Lista de tags (ej: ["calendar", "bell"])

    Returns:
        True si se envió correctamente, False si falló
    """
    if not NTFY_TOPIC:
        print("⚠️  NTFY_TOPIC no configurado en config.py")
        return False

    try:
        headers = {
            "Title": titulo.encode('utf-8'),
            "Priority": prioridad,
        }
        if tags:
            headers["Tags"] = ",".join(tags)

        response = requests.post(
            f"{NTFY_SERVER}/{NTFY_TOPIC}",
            data=mensaje.encode('utf-8'),
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            print(f"✓ Notificación enviada: {titulo}")
            return True
        else:
            print(f"⚠️  Error enviando notificación: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("⚠️  Timeout al enviar notificación (sin conexión?)")
        return False
    except Exception as e:
        print(f"⚠️  Error enviando notificación: {e}")
        return False


# ============================================================
# NOTIFICACIÓN PROGRAMADA
# ============================================================
def enviar_notificacion_programada(titulo, mensaje, fecha_hora_envio,
                                     prioridad="high", tags=None):
    """
    Programa una notificación para que se envíe en una fecha/hora específica.
    ntfy la guarda en el servidor y la envía aunque el PC esté apagado.

    Args:
        titulo: Título de la notificación
        mensaje: Cuerpo del mensaje
        fecha_hora_envio: datetime (cuándo enviar la notificación)
        prioridad: "min", "low", "default", "high", "max"
        tags: Lista de tags

    Returns:
        True si se programó correctamente, False si falló
    """
    if not NTFY_TOPIC:
        print("⚠️  NTFY_TOPIC no configurado")
        return False

    try:
        ahora = datetime.now()
        delta = fecha_hora_envio - ahora
        segundos = int(delta.total_seconds())

        # Validaciones de ntfy:
        # - Mínimo: 10 segundos
        # - Máximo: 3 días (259200 segundos)
        if segundos < 10:
            print(f"⚠️  La fecha de envío es muy próxima ({segundos}s). Debe ser al menos 10s.")
            return False

        if segundos > 259200:
            print(f"⚠️  La fecha de envío es muy lejana ({segundos}s). Máximo 3 días permitido por ntfy.")
            return False

        headers = {
            "Title": titulo.encode('utf-8'),
            "Priority": prioridad,
            "Delay": f"{segundos}s",
        }
        if tags:
            headers["Tags"] = ",".join(tags)

        response = requests.post(
            f"{NTFY_SERVER}/{NTFY_TOPIC}",
            data=mensaje.encode('utf-8'),
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            print(f"✓ Notificación programada para {fecha_hora_envio.strftime('%d/%m/%Y %H:%M')}")
            return True
        else:
            print(f"⚠️  Error programando notificación: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("⚠️  Timeout al programar notificación")
        return False
    except Exception as e:
        print(f"⚠️  Error programando notificación: {e}")
        return False


# ============================================================
# NOTIFICACIÓN DE CITA
# ============================================================
def notificar_cita_agendada(cliente, concepto, monto,
                             fecha_pautada, hora_pautada):
    """
    Envía las notificaciones de una cita agendada:
    1. Notificación inmediata (confirmación)
    2. Notificación programada (recordatorio para el día de la cita)

    Args:
        cliente: Nombre del cliente
        concepto: Concepto / sistema
        monto: Monto de la cotización
        fecha_pautada: Fecha en formato "dd/mm/aaaa"
        hora_pautada: Hora en formato "HH:MM" (puede ser vacío)
    """
    if not fecha_pautada:
        return  # Sin fecha pautada, no hay cita que notificar

    # --- 1. Notificación inmediata ---
    hora_texto = f" a las {hora_pautada}" if hora_pautada else ""
    mensaje_inmediato = (
        f"👤 Cliente: {cliente}\n"
        f"📦 Concepto: {concepto}\n"
        f"📅 Fecha: {fecha_pautada}{hora_texto}\n"
        f"💰 Monto: {monto}"
    )

    enviar_notificacion(
        titulo=f"📅 Cita agendada: {cliente}",
        mensaje=mensaje_inmediato,
        prioridad="default",
        tags=["calendar", "white_check_mark"]
    )

    # --- 2. Notificación programada (recordatorio) ---
    try:
        fecha_dt = datetime.strptime(fecha_pautada.strip(), "%d/%m/%Y")

        # Programar recordatorio para las 8:00 AM del día de la cita
        if hora_pautada:
            try:
                hora_dt = datetime.strptime(hora_pautada.strip(), "%H:%M")
                fecha_recordatorio = fecha_dt.replace(
                    hour=hora_dt.hour, minute=hora_dt.minute, second=0
                )
                # Programar 1 hora antes de la cita
                fecha_recordatorio = fecha_recordatorio - timedelta(hours=1)
            except ValueError:
                fecha_recordatorio = fecha_dt.replace(hour=8, minute=0, second=0)
        else:
            fecha_recordatorio = fecha_dt.replace(hour=8, minute=0, second=0)

        # Verificar que sea futuro
        if fecha_recordatorio <= datetime.now():
            print("⚠️  La fecha de la cita ya pasó o es muy próxima")
            return

        hora_texto_recordatorio = (
            f" a las {hora_pautada}" if hora_pautada
            else " (hora sin confirmar)"
        )
        mensaje_recordatorio = (
            f"⏰ Recordatorio de cita con:\n"
            f"👤 {cliente}\n"
            f"📦 {concepto}\n"
            f"📅 Hoy{hora_texto_recordatorio}"
        )

        enviar_notificacion_programada(
            titulo=f"⏰ Recordatorio: {cliente}",
            mensaje=mensaje_recordatorio,
            fecha_hora_envio=fecha_recordatorio,
            prioridad="high",
            tags=["bell", "alarm_clock"]
        )

    except ValueError:
        print(f"⚠️  Formato de fecha inválido: {fecha_pautada}")
    except Exception as e:
        print(f"⚠️  Error programando recordatorio: {e}")


# ============================================================
# PROBAR NOTIFICACIÓN
# ============================================================
def probar_notificacion():
    """
    Envía una notificación de prueba al celular.
    Útil para verificar que todo funciona.
    """
    print("Enviando notificación de prueba...")
    return enviar_notificacion(
        titulo="🧪 Prueba de Aluze",
        mensaje="¡Las notificaciones de Aluze funcionan correctamente!\n\n"
                "Recibirás alertas cuando agendes citas con clientes.",
        prioridad="default",
        tags=["test_tube", "white_check_mark"]
    )