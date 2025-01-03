from pydantic import BaseModel

class CreateUsuario(BaseModel):
    username: str
    password: str

