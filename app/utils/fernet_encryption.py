from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# Cargar la clave desde el archivo .env
fernet_key = os.getenv('FERNET_KEY')

# Inicializar el cifrador Fernet con la clave
cipher = Fernet(fernet_key.encode())

# Funciones de cifrado y descifrado
def cifrar_contraseña(contraseña: str) -> str:
    contraseña_bytes = contraseña.encode('utf-8')  # Convertir la contraseña a bytes
    contraseña_cifrada = cipher.encrypt(contraseña_bytes)
    return contraseña_cifrada.decode('utf-8')  # Convertir a string para almacenar en la base de datos

def descifrar_contraseña(contraseña_cifrada: str) -> str:
    contraseña_bytes = contraseña_cifrada.encode('utf-8')  # Convertir de string a bytes
    contraseña_descifrada = cipher.decrypt(contraseña_bytes)
    return contraseña_descifrada.decode('utf-8')  # Convertir a string
