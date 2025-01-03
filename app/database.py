from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Column, PrimaryKeyConstraint, String, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import Session


Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(String, primary_key=True)
    contraseña = Column(String, nullable=False) 

class Reserva(Base):
    __tablename__ = "reservas"
    id_reserva = Column(Integer, primary_key=True, autoincrement=True)
    dia_semana = Column(String, nullable=False) 
    hora = Column(String, nullable=False)  
    clase = Column(String, nullable=False)  
    centro = Column(String, nullable=False) 
    fecha_reserva = Column(DateTime, default=None)
    reserva_activa = Column(Boolean, default=True)
    id_usuario = Column(String, ForeignKey('usuarios.id_usuario', ondelete='CASCADE'), nullable=False)

    # Restricción única para evitar duplicados
    __table_args__ = (
        UniqueConstraint("dia_semana", "hora", "clase", "id_usuario", name="uq_reserva_unica"),
    )

    # Relación con usuarios
    usuario = relationship('Usuario', backref='reservas')


DATABASE_URL = "sqlite:///./reservas.db" # Archivo de base de datos

engine = create_engine(DATABASE_URL)

# Verificar si autoflush True o False 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


# Dependencia para obtener la sesión de la base de datos
def get_db() -> Session: # type: ignore
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
