from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.db_utils import *
from app.database import get_db
from app.gateway.vg_selenium import makeReservation
import calendar
from app.utils.fernet_encryption import descifrar_contraseña
import time

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///tasks.db')
}

scheduler = BackgroundScheduler(jobstores=jobstores)

# Programar tarea de keep-alive para evitar que la aplicación se duerma
@scheduler.scheduled_job('cron', hour=5, minute=0, id="keep_alive")
def keep_alive():
    print(f"[{datetime.now()}] Keep-alive ejecutado")


def ejecutar_reserva(id_reserva, hora, centro, clase, fecha_reserva=None, programada=True):
    # Obtener la sesión de la base de datos
    db = next(get_db())
    
    if fecha_reserva is None:
        fecha_reserva = datetime.now()

    # Obtener el email del usuario que realizó la reserva
    usuarioReserva = obtener_usuario_por_reserva(db, id_reserva)
    email_usuario = usuarioReserva.id_usuario
    
    if reserva_activa(db, id_reserva):
    
        # Puede que se quiera reservar con menos de 24 horas de antelación
        
        
        # Uso programada para colocar la fecha correcta de la reserva en la base de datos
        if programada:
            fecha_reserva += timedelta(days=1) # Día siguiente al día de la reserva
        
        fecha_reserva = fecha_reserva.replace(hour=int(hora[:2]), minute=int(hora[3:]), second=0)
    
        #print(f"Ejecutando reserva en centro {centro}: para el día {fecha_reserva.date()}, {clase} a las {hora}")
        
        contraseña_usuario = descifrar_contraseña(usuarioReserva.contraseña)

        insertar_log(db, id_usuario=email_usuario, id_reserva=id_reserva, mensaje=f"Ejecutando reserva en centro {centro}: para el día {fecha_reserva.date()}, {clase} a las {hora}")


        # Intentar hacer la reserva 2 veces
        intento = 1
        while intento <= 2:
            try:
                if makeReservation(email_usuario, contraseña_usuario, fecha_reserva.date(), centro, clase, hora):
                    # Si la reserva tiene éxito, confirmar la reserva en la base de datos
                    insertar_log(db, id_usuario=email_usuario, id_reserva=id_reserva, 
                                mensaje=f"Reserva en centro {centro}: para el día {fecha_reserva.date()}, {clase} a las {hora} realizada con éxito. Intento {intento}.")
                    confirmar_reserva(db, id_reserva, fecha_reserva)
                    break  # Salir del bucle si la reserva es exitosa
                else:
                    raise Exception("Error en la reserva")
            
            except Exception as e:
                print(f"Intento {intento} fallido: {e}")
                insertar_log(db, id_usuario=email_usuario, id_reserva=id_reserva, 
                        mensaje=f"Error al hacer la reserva en centro {centro}: para el día {fecha_reserva.date()}, {clase} a las {hora}. Intento {intento} fallido.")
                time.sleep(5)  # Esperar 5 segundos antes de reintentar
                intento += 1
    
        if intento > 2:
            insertar_log(db, id_usuario=email_usuario, id_reserva=id_reserva, 
                        mensaje=f"Error al hacer la reserva en centro {centro}: para el día {fecha_reserva.date()}, {clase} a las {hora}")
            print(f"Reserva en centro {centro} cancelada tras {intento} intentos fallidos.")

    else:
        # Reserva cancelada
        insertar_log(db, id_usuario=email_usuario, id_reserva=id_reserva, mensaje=f"Reserva en centro {centro}: para el día {fecha_reserva.date()}, {clase} a las {hora} no ejecutada por estar inactiva.")
        #print(f"Reserva en centro {centro}: para el día {fecha_reserva.date()}, {clase} a las {hora} no ejecutada por estar inactiva.")



def proxima_fecha_reserva(fecha_actual:datetime, dia_reserva:int, hora_reserva:str) -> datetime:

    """
    Esta función calcula a partir del día de la semana y la hora, la próxima fecha de reserva partiendo de la fecha actual
    Returns datetime object.
   
    Arguments:
    fecha_actual    - Fecha y hora actual
    dia_reserva     - el dia de la semana ("0: monday", "1: tuesday",...)
    hora_reserva    - hora en formato String ("HH:MM")

    """
  
    dias_diferencia = (dia_reserva - fecha_actual.weekday() + 7) % 7

    proxima_fecha = fecha_actual + timedelta(days=dias_diferencia) 
    proxima_fecha = proxima_fecha.replace(hour=int(hora_reserva[:2]), minute=int(hora_reserva[3:]), second=0) # Ajusto la hora de la reserva

    return proxima_fecha

def eliminar_reserva_programada(id_reserva):
    try:
        # Intentar remover la tarea programada del scheduler
        job = scheduler.get_job(id_reserva)
        if job:
            scheduler.remove_job(id_reserva)
            print(f"Reserva ID {id_reserva} cancelada exitosamente.")
        else:
            print(f"No se encontró tarea programada con ID {id_reserva}. No es necesario cancelar ninguna tarea.")
    except Exception as e:
        # Si ocurre cualquier otro error, se maneja y no interrumpe el flujo
        print(f"Error al cancelar la reserva ID {id_reserva}: {e}")
 

# Función para programar la tarea
def programar_reserva(id_reserva, dia_semana, hora, centro, clase):
    """
    Returns None.
   
    Arguments:
    id_reserva  - identificativo único de la reserva
    dia_semana  - el dia de la semana ("monday", "tuesday",...)
    hora        - hora en formato String ("HH:MM")
    centro      - codigo de centro en formato String ("123")
    clase       - nombre de la clase en formato String ("Body Pump")

    """
   
    
    # Mapear día de la semana al índice (0=Lunes, 6=Domingo)
    dia_idx = list(calendar.day_name).index(dia_semana.capitalize()) 

    # Calcular la próxima reserva
    ahora = datetime.now()
    proxima_fecha = proxima_fecha_reserva(fecha_actual=ahora, dia_reserva=dia_idx, hora_reserva=hora)
    
    # Calcular si la reserva está dentro de las próximas 24 horas
    dentro_de_24_horas = (proxima_fecha > ahora) and ((proxima_fecha - ahora) <= timedelta(hours=24))
    if dentro_de_24_horas:
        # Reserva inmediata
        print("Intento ejecutar reserva inmediata...")
        ejecutar_reserva(id_reserva, hora, centro, clase, fecha_reserva=proxima_fecha, programada=False)

    # Para reservas programadas, la reserva debe hacerse con un día de antelación
    dia_idx = (dia_idx - 1) % 7
    proxima_fecha = proxima_fecha_reserva(fecha_actual=ahora, dia_reserva=dia_idx, hora_reserva=hora)

    # El id de la tarea va a coincidir con el id de la reserva en la base de datos
    id_job = str(id_reserva)
    print("Se ha programado una reserva con id", id_job)

    # Programo la reserva
    print("Fecha próxima reserva:", proxima_fecha)
    scheduler.add_job(
        ejecutar_reserva,
        'cron',
        day_of_week = dia_idx,
        hour = hora.split(":")[0],
        minute = hora.split(":")[1],
        second = 1,  # Añado 1 segundo de margen para evitar problemas de sincronización
        args = [id_reserva, hora, centro, clase],
        misfire_grace_time=60,  # Permite 1 minuto de retraso en caso de que el sistema esté ocupado
        id = id_job,
    )
  

if not scheduler.running:
    scheduler.start()
