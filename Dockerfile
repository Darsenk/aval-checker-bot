# ══════════════════════════════════════════════════════════════
# DOCKERFILE OPTIMIZADO PARA KOYEB - PYTHON 3.11
# ══════════════════════════════════════════════════════════════

# Usar Python 3.11 slim (compatible con python-telegram-bot)
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para Chrome y Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Instalar ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1) \
    && wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}" -O /tmp/version \
    && DRIVER_VERSION=$(cat /tmp/version) \
    && wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip /tmp/version \
    && chmod +x /usr/local/bin/chromedriver

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de requirements primero (cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código del bot
COPY AvalBot_ConLicencias.py .

# Crear directorio para persistencia de datos
RUN mkdir -p /app/data

# Exponer puerto 8000 para health check de Koyeb
EXPOSE 8000

# Crear script de inicio optimizado
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Iniciando servicios..."\n\
\n\
# Health check HTTP en background\n\
python3 -m http.server 8000 &\n\
HTTP_PID=$!\n\
echo "✅ Health check servidor iniciado (PID: $HTTP_PID)"\n\
\n\
# Esperar 1 segundo\n\
sleep 1\n\
\n\
# Iniciar bot de Telegram\n\
echo "🤖 Iniciando Aval Bot..."\n\
python3 -u AvalBot_ConLicencias.py\n\
\n\
# Si el bot falla, matar el servidor HTTP\n\
kill $HTTP_PID 2>/dev/null || true\n\
' > /app/start.sh && chmod +x /app/start.sh

# Variable de entorno (se define en Koyeb)
ENV BOT_TOKEN=""

# Usuario no-root para seguridad
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# Comando de inicio
CMD ["/bin/bash", "/app/start.sh"]
