import requests
from datetime import datetime
class VG_API:

    BASE_URL = "https://gimnasios.vivagym.es"

    # Endpoints
    LOGIN_ENDPOINT = "/api/user/authenticate"
    SEARCH_BOOKING_ENDPOINT = "/api/classes/search-booking-participations"
    CREATE_BOOKING_ENDPOINT = "/api/booking/create-booking"
    CANCEL_BOOKING_ENDPOINT = "/api/booking/cancel-booking"

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.user_id = None
        self.center_id = None
        self.token = None
        self.sessionTimeoutOneMonth = False

    def authenticate(self):
        url = f"{self.BASE_URL}{self.LOGIN_ENDPOINT}"
        data = {
            "email": self.username, 
            "password": self.password, 
            "sessionTimeoutOneMonth": self.sessionTimeoutOneMonth
        }
 
        try:
            start_time = datetime.now()
            response = requests.post(url, json=data, timeout=5)
            response.raise_for_status()
            response_data = response.json()
            end_time = datetime.now()
            print(f"Tiempo de autenticación: {end_time - start_time}")
            # Comprobar que existe el token en la respuesta
            if all(key in response_data for key in ["token", "user"]):
                self.token = response_data["token"]
                self.user_id = response_data["user"]["userId"]
                self.center_id = response_data["user"]["centerId"]
            else:
                print(f"Error en la autenticación: Missing token or user data.")
                return False

        except KeyError as e:
            print(f"Error: Missing expected key in the response: {e}")
            return False
        except requests.exceptions.Timeout:
            print(f"Error en la autenticación: The request timed out.")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error en la autenticación: {e}")
            return False
       
        print("Autenticación exitosa")
        return True


    # Crea una reserva y devuelve el id de la reserva creada o None si no se pudo crear
    def create_booking(self, selectedUserCenterId: int, class_date: str, class_time: str, class_name: str):

        # Compruebo que los parametros son correctos
        print(f"Creando reserva para el día {class_date} a las {class_time} en el centro {selectedUserCenterId} para la clase {class_name}")
        # Buscar el id de la clase
        start_time = datetime.now()
        booking_id = self.find_booking_id(selectedUserCenterId, class_date, class_time, class_name)
        end_time = datetime.now()
        print(f"Tiempo de búsqueda de la clase: {end_time - start_time}")
        if not booking_id:
            print(f"Error en la creación de la reserva: No se encontró la clase {class_name} para el día {class_date} a las {class_time}")
            return None

        data = {
            "selectedUserId": self.user_id,
            "selectedUserCenterId": selectedUserCenterId,
            "bookingCenterId": self.center_id,
            "bookingId": booking_id
        }
        url = f"{self.BASE_URL}{self.CREATE_BOOKING_ENDPOINT}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            start_time
            response = requests.post(url=url, headers=headers, json=data, timeout=5)
            response.raise_for_status()
            response_data = response.json()
            end_time = datetime.now()
            print(f"Tiempo de creación de la reserva: {end_time - start_time}")
            return response_data.get("id")

        except requests.exceptions.Timeout:
            print(f"Error en la creación de la reserva: The request timed out.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error en la creación de la reserva: {e}")
            return None

    # Cancela una reserva y devuelve True si se canceló correctamente o False si no se pudo cancelar
    def cancel_booking(self, selected_user_center_id: int, participation_id: int):
        data = {
            "selectedUserId": self.user_id,
            "selectedUserCenterId": selected_user_center_id,
            "participationCenterId": self.center_id,
            "participationId": participation_id
        }

        url = f"{self.BASE_URL}{self.CANCEL_BOOKING_ENDPOINT}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.post(url=url, headers=headers, json=data, timeout=5)
            response.raise_for_status()
            return True
        except requests.exceptions.Timeout:
            print(f"Error en la cancelación de la reserva: The request timed out.")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error en la cancelación de la reserva: {e}")
            return False


    # Busca las clases disponibles para un centro y un rango de fechas
    def search_booking_participations(self, center: int, date_from: str, date_to: str):
        data = {
            "centers": [center],
            "dateFrom": date_from,
            "dateTo": date_to
        }
        url = f"{self.BASE_URL}{self.SEARCH_BOOKING_ENDPOINT}"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.post(url=url, headers=headers, json=data, timeout=5)
            response.raise_for_status()
            response_data = response.json()
            return response_data
        except requests.exceptions.Timeout:
            print(f"Error en la búsqueda de reservas: The request timed out.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error en la búsqueda de reservas: {e}")
            return None

    # Busca el id de una clase en un centro en una fecha y hora específica
    def find_booking_id(self, center:int, date: str, time: str, class_name: str):
        # Busco las reservas de un usuario en un centro en un rango de fechas
        print(f"Buscando reservas en el centro {center} para el día {date} a las {time} para la clase {class_name}")
        response = self.search_booking_participations(center, date, date)
        if response and isinstance(response, list):
            return next(
                (elem.get("booking", {}).get("id") for elem in response 
                if elem.get("booking", {}).get("name") == class_name 
                and elem.get("booking", {}).get("startTime") == time), None)
        return None


# Crear un objeto de la clase VG_API
# from datetime import datetime, timedelta
# time1 = datetime.now()
api = VG_API("diego-995@hotmail.com", "Masiero1-vg")
api.authenticate()
res = api.create_booking(selectedUserCenterId=134, class_date="2025-04-06", class_time="10:30", class_name="Virtual Cycling")
# time2 = datetime.now()
# print(f"Reserva creada con id: {res}")
# print(f"Tiempo de ejecución: {time2 - time1}")
#res = api.cancel_booking(selected_user_center_id=134, participation_id=626548)
print(res)

