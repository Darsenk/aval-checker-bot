FROM python:3.11-slim

# Evitar errores interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Variables Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
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

# Instalar Google Chrome (sin apt-key)
RUN mkdir -p /etc/apt/keyrings \
    && wget -qO /etc/apt/keyrings/google.gpg https://dl.google.com/linux/linux_signing_key.pub \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 🔥 FIX REAL: ChromeDriver EXACTO según versión instalada
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    echo "Chrome version: $CHROME_VERSION" && \
    wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf /tmp/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements primero (cache)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Puerto para Koyeb
EXPOSE 8000

# Ejecutar bot
CMD ["python3", "-u", "AvalBot_ConLicencias.py"]
