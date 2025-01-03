from pydantic import BaseModel, Field, field_validator
from fastapi import HTTPException, status
from typing import Optional

CENTROS = {
    "platero": "134"
}

CLASES = ["Body Pump", "Cycling", "Body Combat", "GAP", "Virtual Cycling", "Zumba", "Yoga", "Body Balance"]


class CreateReserva(BaseModel):
    dia_semana: str
    hora: str = Field(..., description="Hora en formato HH:MM")
    centro: str
    clase: str
   

    # Validar que la hora tenga el formato HH:MM
    @field_validator("hora")
    @classmethod
    def validar_hora(cls, value):
        import re
        if not re.match(r"^\d{2}:\d{2}$", value):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La hora debe estar en formato HH:MM"
            )
        return value
    
    # Validar la clase
    @field_validator("clase")
    @classmethod
    def validar_clase(cls, value):
        if value not in CLASES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Clase desconocida: {value}. Clases válidas: {CLASES}"
            )
        return value

    # Validador para centro
    @field_validator("centro")
    @classmethod
    def traducir_centro(cls, value):
        if value not in CENTROS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Centro desconocido: {value}. Centros válidos: {list(CENTROS.keys())}"
            )
        return CENTROS[value]
    

class UpdateEstadoReserva(BaseModel):
    estado: bool


