# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /backend

# Copia los archivos necesarios
COPY . /backend

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Establecer variables de entorno para evitar preguntas interactivas
ENV DEBIAN_FRONTEND=noninteractive

# Actualizar el sistema e instalar Chromium, ChromeDriver y otras dependencias necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configura la zona horaria a Europa/Madrid
ENV TZ=Europe/Madrid
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Verificar las versiones instaladas
RUN chromium --version && chromedriver --version

# Expone el puerto en el que el backend escucha
EXPOSE 80

# Comando para ejecutar la aplicación
CMD ["python", "-m", "app.main"]
