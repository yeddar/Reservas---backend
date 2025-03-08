from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import Reserva, Usuario, Log
from datetime import timedelta

def insertar_log(db: Session, id_usuario, id_reserva, mensaje):
    log = Log(id_usuario=id_usuario, id_reserva=id_reserva, mensaje=mensaje)
    db.add(log)
    db.commit()  
    db.refresh(log)  # Para obtener el objeto con la id generada
    return log


def reserva_confirmada(reserva: Reserva) -> bool:
    """
    Comprueba si una reserva está confirmada:
    - Faltan 24 horas o menos para la fecha de la reserva.
    - O ha pasado menos de 1 hora desde la fecha de la reserva.
    """
    if reserva.fecha_reserva is None:
        return False  # Si no hay fecha de reserva, no está confirmada

    ahora = datetime.now()
    tiempo_restante = reserva.fecha_reserva - ahora
    tiempo_pasado = ahora - reserva.fecha_reserva

    return (timedelta(0) <= tiempo_restante <= timedelta(days=1)) or (tiempo_pasado < timedelta(hours=1))



def elimina_reserva(db: Session, id_reserva: int) -> bool:
    """
    Elimina una reserva de la base de datos.
    
    Args:
        db (Session): Sesión de base de datos.
        id_reserva (int): ID de la reserva a eliminar.
    
    Returns:
        bool: True si la reserva se eliminó correctamente, False si ocurrió un error.
    
    Raises:
        HTTPException: Si no se encuentra una reserva con el ID especificado.
    """
    # Buscar la reserva en la base de datos
    print(f"Buscando reserva con ID {id_reserva}...")
    reserva = db.get(Reserva, id_reserva)
    
    if reserva is None:
        print(f"No se encontró reserva con ID {id_reserva}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reserva con ID {id_reserva} no encontrada."
        )

    print(f"Reserva encontrada: {reserva}")

    try:
        # Eliminar la reserva
        db.delete(reserva)
        db.commit()
        print(f"Reserva con ID {id_reserva} eliminada exitosamente.")
        return True
    
    except Exception as e:
        # Manejar cualquier error que ocurra durante la eliminación
        db.rollback()
        print(f"Error al eliminar la reserva: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la reserva: {str(e)}"
        )
    
def obtener_reserva(db: Session, id_reserva: int) -> Reserva:
    # Obtener la reserva por ID
    reserva = db.get(Reserva, id_reserva)
    if reserva is None:
        raise ValueError("La reserva no existe")
    return reserva

def obtener_usuario_por_reserva(db: Session, id_reserva: int) -> Usuario:
    # Obtener la reserva por ID
    reserva = obtener_reserva(db, id_reserva)

    # Acceder al usuario relacionado
    usuario_reserva = reserva.usuario
    return usuario_reserva

def reserva_activa(db: Session, id_reserva: int):
    """
        Consulta el estado de la reserva
    """
    reserva = db.get(Reserva, id_reserva)

    if reserva is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reserva con ID {id_reserva} no encontrada."
        )

    return  bool(reserva.reserva_activa)

def cambia_estado_reserva(db: Session, id_reserva: int):
    """
        Modifica estado de la reserva
    """
    reserva = db.get(Reserva, id_reserva)
    if reserva is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reserva con ID {id_reserva} no encontrada."
        )

    if reserva.reserva_activa:
        reserva.reserva_activa = False
    else:
        reserva.reserva_activa = True
        
    try:
        db.commit()
        db.refresh(reserva)
    except Exception:
        db.rollback() # Deshace los cambios
        return False
  
    return True

def confirmar_reserva(db: Session, id_reserva: int, fecha_reserva: datetime) -> bool:
    """
    Establece la fecha y hora de la clase. Esto sirve para saber si 
    la reserva se ha efectuado correctamente o no.
    """
    reserva = db.get(Reserva, id_reserva)
    if reserva is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reserva con ID {id_reserva} no encontrada"
        )

    # La fecha de reserva es la fecha y hora en la que tendrá lugar la clase. Esto es así para luego poder calcular de forma más sencilla.
    reserva.fecha_reserva = fecha_reserva

    try:
        # Guardar los cambios en la base de datos
        db.commit()
        db.refresh(reserva)
        return True
    
    except Exception:
        db.rollback() # Deshace los cambios
        return False



# Esta función guarda el objeto que recibe como parámetro en la base de datos.
# Trata de evitar código repetido.
def guardar_en_db(db: Session, obj: object):
    db.add(obj)
    try:   
        db.commit()
        db.refresh(obj)  # Refresca el objeto para obtener datos actualizados de la base de datos
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar en la base de datos: {str(e)}"
        )

# Modifica la contraseña en la base de datos.
def actualizar_contraseña_usuario(db: Session, usuario: Usuario, nueva_contraseña: str):
    print("Actualizar contraseña usuario:", nueva_contraseña)
    usuario.contraseña = nueva_contraseña
    try:
        db.commit()
        db.refresh(usuario)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al guardar el objeto en la base de datos"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )
