# Usa una imagen oficial y ligera de Python 3.11
FROM python:3.11-slim

# Evita que Python escriba archivos .pyc en disco y asegura 
# que la consola imprima los logs inmediatamente.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establece la ruta base del proyecto para no tener conflictos de imports
ENV PYTHONPATH=/app

# Crea y ubica el entorno del contenedor en /app
WORKDIR /app

# Instalar dependencias esenciales de OS por si algún paquete de Python las requiere
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia estrictamente tu lista de dependencias primero 
# (esto aprovecha el caché de capas de Docker en reconstrucciones)
COPY requirements.txt .

# Instala los paquetes globales dentro del contenedor
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente completo excluyendo lo del .dockerignore
COPY . .

# Expone el puerto 5000 donde vive la app Flask de NequiZ
EXPOSE 5000

# Ejecuta el entry point de flask
CMD ["python", "app.py"]
