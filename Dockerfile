# Imagen base ligera
FROM python:3.11-slim

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Variables útiles
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema (optimizado)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    curl \
    unzip \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libdrm2 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libxcomposite1 \
    libxfixes3 \
    libxext6 \
    libxrender1 \
    libxi6 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome (método moderno)
RUN mkdir -p /etc/apt/keyrings \
    && wget -qO /etc/apt/keyrings/google.gpg https://dl.google.com/linux/linux_signing_key.pub \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements primero (mejor cache)
COPY requirements.txt .

# Instalar dependencias Python optimizado
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Puerto (si usas web, opcional)
EXPOSE 8000

# Comando de ejecución (ajústalo a tu app)
CMD ["python", "main.py"]
