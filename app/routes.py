
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.reserva import CreateReserva, UpdateEstadoReserva
from app.usuario import CreateUsuario
from sqlalchemy.orm import Session
from app.database import Reserva, Usuario, get_db
from app.tasks import programar_reserva, eliminar_reserva_programada
from app.db_utils import *
from app.gateway.vg_selenium import checkLogin
from app.utils.jwt_auth import create_token, verify_token, get_current_user, oauth2_scheme
from typing import Optional
from fastapi.responses import JSONResponse
from fastapi import Cookie
from fastapi import Form

from fastapi.security import OAuth2PasswordRequestForm

from app.utils.fernet_encryption import cifrar_contraseña, descifrar_contraseña

router = APIRouter()


@router.post("/refresh/")
def refresh_token(refresh_token: str = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No se encontró el refresh token")

    try:
        payload = verify_token(refresh_token)
        id_usuario = payload.get("sub")

        if not id_usuario:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Generar un nuevo access token
        new_access_token = create_token({"sub": id_usuario}, 15)

        return {"access_token": new_access_token, "token_type": "bearer"}
    
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")


@router.post("/login/")
def login_usuario(
    #usuario: CreateUsuario,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Intenta autenticar con vivaGym.
    Crea el usuario en la base de datos si no existe.
    """
    keep_session = "keep_session" in form_data.scopes
 
    # Crea un objeto usuario con los datos del formulario
    usuario = CreateUsuario(username=form_data.username, password=form_data.password)

    # Comprueba si el usuario ya existe en la base de datos
    usuario_bd = db.get(Usuario, usuario.username)

    if usuario_bd:
        contraseña_descifrada = descifrar_contraseña(usuario_bd.contraseña)
        # Comprueba que la contraseña no haya cambiado. Si ha cambiado, actualizo la base de datos.
        if usuario.password != contraseña_descifrada:
            vivagym_auth = checkLogin(usuario) # Comprueba la conexión con vivaGym antes de actualizar la contraseña
            if not vivagym_auth:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se ha conseguido autenticar el usuario."
                )
            try:
                actualizar_contraseña_usuario(db, usuario_bd, usuario.password)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error inesperado al intentar actualizar la contraseña del usuario: {str(e)}"
                )
    else: # Si no existe el usuario en la BBDD, se lanza el error correspondiente.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se ha conseguido autenticar el usuario."
        )

        # El login de nuevos usuarios queda deshabilitado por el momento
        """ vivagym_auth = checkLogin(usuario)
        if not vivagym_auth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se ha conseguido autenticar el usuario."
            )
             
        contraseña_cifrada = cifrar_contraseña(usuario.password)
        nuevo_usuario = Usuario(
            id_usuario=usuario.username,
            contraseña=contraseña_cifrada
        )

        try:
            guardar_en_db(db, nuevo_usuario)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inesperado al guardar los datos del usuario en la base de datos: {str(e)}"
            ) """

    # Generar tokens JWT para el usuario
    
    # Si "mantener sesión iniciada" está activado, el refresh token dura más
    access_token_expires = 15 
    refresh_token_expires = 43200 if keep_session else 1440  # 30 días o 1 día

    access_token = create_token({"sub": usuario.username}, access_token_expires)
    refresh_token = create_token({"sub": usuario.username}, refresh_token_expires)


    response = JSONResponse({
        "message": "Autenticación exitosa",
        "usuario": {"id_usuario": usuario.username},
        "access_token": access_token,
        "token_type": "bearer"
    })

    # Guardar refresh token en una cookie segura
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True, # False en desarrollo, True en producción
        samesite="Lax"
    )
    
    return response

@router.post("/usuario/reserva")
def añadir_reserva_usuario(
    reserva: CreateReserva,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user) # Devuelve el usuario logueado
):

    """
    Crea nueva reserva para el usuario logueado.
    """

    # Obtengo el id del usuario logueado
    logged_user_id = current_user.id_usuario
    
    print("Usuario logueado:", logged_user_id)
    nueva_reserva = Reserva(
        dia_semana=reserva.dia_semana,
        hora=reserva.hora,
        centro=reserva.centro,
        clase=reserva.clase,
        id_usuario=logged_user_id,
    )

    try:
        guardar_en_db(db, nueva_reserva)

        programar_reserva(
            nueva_reserva.id_reserva, 
            nueva_reserva.dia_semana, 
            nueva_reserva.hora, 
            nueva_reserva.centro, 
            nueva_reserva.clase
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado en la consulta: {str(e)}"
        )
    

    return {
        "message": "Reserva creada exitosamente",
        "reserva": {
            "id_usuario": nueva_reserva.id_usuario,
            "dia_semana": nueva_reserva.dia_semana,
            "hora": nueva_reserva.hora,
            "centro": nueva_reserva.centro,
            "clase": nueva_reserva.clase,
        }
    }

@router.put("/usuario/reserva/{id_reserva}")
def modifica_estado_reserva(
    id_reserva: int,
    estado_reserva: UpdateEstadoReserva,  # Datos de la solicitud
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Modifica el estado de una reserva específica para el usuario logueado.
    """
    # Buscar la reserva en la base de datos
    reserva = db.get(Reserva, id_reserva)

    # Verificar si la reserva existe
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )

    # Verificar si la reserva pertenece al usuario logueado
    if reserva.id_usuario != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar esta reserva"
        )

    try:
        # Actualizar el estado de la reserva
        reserva.reserva_activa = estado_reserva.estado
        db.commit()
        db.refresh(reserva)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al modificar la reserva: {str(e)}"
        )

    return {"message": "Estado de la reserva modificado exitosamente"}

    

@router.delete("/usuario/reserva/{id_reserva}")
def borrar_reserva_usuario(
    id_reserva: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)  # Usuario logueado
):
    """
    Elimina una reserva específica para el usuario logueado.
    """
    # Buscar la reserva en la base de datos
    reserva = db.get(Reserva, id_reserva)

    # Verificar si la reserva existe
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )

    # Verificar si la reserva pertenece al usuario logueado
    if reserva.id_usuario != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar esta reserva"
        )

    try:
        # Elimino la reserva del scheduler
        eliminar_reserva_programada(id_reserva)

        # Elimino la reserva de la base de datos
        elimina_reserva(db, id_reserva)
    
    except HTTPException as e:
        # Si elimina_reserva lanza una HTTPException se propaga
        raise e
    
    except Exception as e:
        # Captura cualquier otro error no esperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al eliminar la reserva: {str(e)}"
        )


    return {"message": "Reserva eliminada exitosamente"}
    

@router.get("/usuario/reservas")
def listar_reservas_usuario(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user) # Devuelve el usuario logueado
):
    """
    Obtiene todas las reservas activas asociadas al usuario logueado.
    """
    # Recuperar las reservas activas del usuario
    #reservas = [reserva for reserva in current_user.reservas if reserva.reserva_activa == 1]

    usuario = db.get(Usuario, current_user.id_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    reservas = usuario.reservas
   
    if not reservas:
        return {
            "message": "No se encontraron reservas para el usuario",
            "reservas": []
        }

    reservas_formateadas = [
        {
            "id_reserva": reserva.id_reserva,
            "dia_semana": reserva.dia_semana,
            "hora": reserva.hora,
            "centro": reserva.centro,
            "clase": reserva.clase,
            "activa": reserva.reserva_activa,
            "fecha_reserva": reserva.fecha_reserva,
            "confirmada": reserva_confirmada(reserva)
        }
        for reserva in reservas
    ]

    return {
        "message": "Reservas encontradas",
        "reservas": reservas_formateadas
    }


@router.get("/reservas/")
def listar_reservas(db: Session = Depends(get_db)):
    reservas = db.query(Reserva).all()
    return reservas


