import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from app.reserva import CENTROS
from datetime import datetime 
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
    
    center_name = next((name for name, code in CENTROS.items() if code == center), None)

    if not center_name:
        center_name = center

    subject = "¡Reserva confirmada! 🎉 💪🏼"

    # Cuerpo del correo en HTML
    body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
            }}
            .container {{
                max-width: 500px;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            }}
            h2 {{
                color: #2c3e50;
            }}
            .details {{
                font-size: 16px;
                line-height: 1.5;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 14px;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>✅ Reserva confirmada</h2>
            <p class="details">
                <strong>📍 Centro:</strong> {center_name} <br>
                <strong>📅 Fecha:</strong> {date} <br>
                <strong>🧘 Clase:</strong> {class_name} <br>
                <strong>⏰ Hora:</strong> {hour}
            </p>
            <p>Gracias por tu reserva 🥰</p>
            <p class="footer">Este es un mensaje generado automáticamente, por favor no respondas.</p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))  # Cambio de 'plain' a 'html'

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
