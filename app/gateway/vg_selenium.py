from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from app.usuario import CreateUsuario
from app.gateway.correo import send_email
from app.database import Usuario, Reserva
from datetime import datetime
from time import sleep
    


def checkLogin(usuario: CreateUsuario) -> bool:
    driver = None
    email = usuario.username
    password = usuario.password

    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ejecutar en modo headless
        chrome_options.add_argument("--no-sandbox")  # Necesario en entornos Docker
        chrome_options.add_argument("--disable-dev-shm-usage")  # Para evitar errores relacionados con /dev/shm
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")  # Opcional si no se utiliza GPU
     
        driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=chrome_options)
        
        # Realiza el proceso de login
        driver.get("https://gimnasios.vivagym.es/login")

        # Esperar a que los campos de email y contraseña estén presentes
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))

        # Encontrar el campo de email y contraseña
        email_input = driver.find_element(By.ID, "email")
        password_input = driver.find_element(By.ID, "password")

        # Rellenar los campos con las credenciales
        email_input.send_keys(email)  
        password_input.send_keys(password)  

        # Hacer clic en el botón de login
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[data-cy="login-button"]')
        login_button.click()

        # Esperar a que el elemento de bienvenida esté presente (lo que indica un login exitoso)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-cy="dashboard-welcome"]')))

        # Si llegamos aquí, significa que el login fue exitoso
        print("Login exitoso.")
        return True

    except Exception as e:
        print("Error al efectuar el login", e)
        return False

    finally:
        # Cierra el driver
        if driver:
            driver.quit()

def makeReservation(email, password, fecha_reserva, centro, clase, hora):
    driver = None

    # Obtengo los datos de la reserva
    booking_center = centro
    booking_date = fecha_reserva
    booking_class = clase

    # Doy el formato requerido a la hora de la reserva. 09:00 -> 9:00
    horas, minutos = hora.split(":")
    booking_hour = f"{int(horas)}:{minutos}"

    #print(f"email: {email}, password: {password} - Centro: {booking_center}, Fecha: {booking_date}, Clase: {booking_class}, Hora: {booking_hour}")


    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ejecutar en modo headless
        chrome_options.add_argument("--no-sandbox")  # Necesario en entornos Docker
        chrome_options.add_argument("--disable-dev-shm-usage")  # Para evitar errores relacionados con /dev/shm
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")  # Opcional si no se utiliza GPU
        driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=chrome_options)

        # Abre la página web
        driver.get(f"https://gimnasios.vivagym.es/booking?centers={booking_center}&date={booking_date}")

        # Esperar a que los campos de email y contraseña estén presentes
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))

        # Encontrar el campo de email y contraseña
        email_input = driver.find_element(By.ID, "email")
        password_input = driver.find_element(By.ID, "password")

        # Rellenar los campos con tus credenciales
        email_input.send_keys(email)  
        password_input.send_keys(password)  

        # Hacer clic en el botón de login
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[data-cy="login-button"]')
        login_button.click()

        
        # Buscar todos los elementos con el ID que contiene 'participation-entry'
        participation_entries = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[id^="participation-entry"]'))
        )
        

        # Iterar por cada entrada y comprobar las condiciones
        participation_id = 0
        for entry in participation_entries:
            booking_name = entry.find_element(By.CSS_SELECTOR, '[data-cy="booking-name"]').text
            start_time = entry.find_element(By.CSS_SELECTOR, '[data-cy="start-time"]').text
    
            if booking_name == booking_class and start_time == booking_hour:
                # Obtener el ID del elemento que cumple las condiciones
                participation_id = entry.get_attribute("id")
                break

        # Validar que se haya encontrado una clase con el ID correcto
        if participation_id == 0:
            raise Exception("No se encontró una clase que cumpla las condiciones.")

        # Realizar la reserva
        participation_entry = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, participation_id))
        )
        
        print("Se ha encontrado la clase a reservar")

        # Hacer clic en el botón que abre el desplegable de la clase a reservar
        chevron_button = participation_entry.find_element(By.CSS_SELECTOR, 'div[data-cy="entry-chevron"]')
        chevron_button.click()

        # Esperar a que aparezca el botón de reserva
        print("Solicitando reserva...")
        booking_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-cy="book-button"]'))
        )
        booking_btn.click()

        print("Se ha solicitado la reserva. Esperando modal de confirmación")

        # Esperar a que el modal de confirmación aparezca
        confirmar_modal = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-cy="book-class-confirm-button"]'))
        )

        # Hacer click en el botón del modal para confirmar la reserva
        print("Se ha abierto el modal de confirmación. Confirmando reserva...")
        confirmar_modal.click()

        print("¡Reserva confirmada!")
        
        # Enviar correo de confirmacion
        send_email(email, booking_center, booking_date, booking_class, booking_hour)

        return True


    except Exception as e:
        print("Error al efectuar la reserva", e)
        return False

    finally:
        # Cierra el driver
        if driver:
            driver.quit() 
     
        
