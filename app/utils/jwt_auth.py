import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from typing import Annotated
from pydantic import BaseModel
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from app.database import get_db
from app.database import Usuario
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os


# Clave secreta para firmar los tokens 
load_dotenv()
SECRET_KEY = os.getenv('JWT_KEY')

# Algoritmo usado para firmar el token
ALGORITHM = "HS256"

# Tiempo de expiración del token (en minutos)
ACCESS_TOKEN_EXPIRE_MINUTES = 1

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# Modelo del token para la respuesta de la API
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

def get_user_on_db(username: str):
    # Obtener la sesión de la base de datos
    db = next(get_db())
    usuario = db.get(Usuario, username)
    return usuario
    
def create_token(data: dict, expires_delta: int):
    """
    Genera un token de acceso con datos específicos y una fecha de expiración.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """
    Verifica la validez de un token y devuelve los datos decodificados.
    """
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
   
    user = get_user_on_db(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
