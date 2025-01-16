import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Cargar las variables de entorno
load_dotenv()

# Obtener datos para envio de notificaciones por correo
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')
SEND_TO_EMAIL = os.getenv('SEND_TO_EMAIL')

# Funcion para notificar reserva por correo electronico
def send_email(email, center, date, class_name, hour):
    subject = "Reserva Confirmada"
    body = f"""
    Se ha confirmado la reserva:
    
    Centro: {center}
    Fecha: {date}
    Clase: {class_name}
    Hora: {hour}
    """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print("Correo de confirmacion enviado.")
    except Exception as e:
        print("Error al enviar el correo:", e)

# Llamada de prueba a la fun
#send_email("Centro Deportivo", "2024-10-20", "Yoga", "15:10")
