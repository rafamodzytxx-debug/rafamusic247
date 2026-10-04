FROM python:3.11-slim

# Evitar prompts interactivos y buffering
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Instalar FFmpeg y librerías necesarias para audio en Discord
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libopus0 \
    nodejs \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del bot
COPY . .

# Comando de inicio para Railway
CMD ["python", "-u", "bot.py"]
