from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.database import init_db

app = FastAPI()

# Configuración de CORS
origins = [
    "http://localhost:5183",  # Dominio del frontend en desarrollo
    "http://192.168.1.100:8085", # Dominio del frontend en producción
    "https://reservasvg.ddns.net",  # Dominio del frontend en producción
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Lista de dominios permitidos
    allow_credentials=True,  # Permitir cookies/sesiones
    allow_methods=["*"],  # Métodos HTTP permitidos (GET, POST, etc.)
    allow_headers=["*"],  # Headers permitidos
)


init_db() # Inicialización de la base de datos


# Registrar las rutas
app.include_router(router, prefix="/api/v1", tags=["Reservas"])

@app.get("/api/v1")
def read_root():
    return {"message": "¡Bienvenido a la API de reservas!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)