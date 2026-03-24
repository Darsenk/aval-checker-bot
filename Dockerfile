# Usar imagen base de Selenium con Chrome
FROM selenium/standalone-chrome:latest

# Cambiar a usuario root para instalar dependencias
USER root

# Instalar Python y pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos
COPY requirements.txt .
COPY AvalBot_ConLicencias.py .

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Exponer puerto 8000 (Koyeb lo requiere)
EXPOSE 8000

# Crear script de inicio con health check
RUN echo '#!/bin/bash\n\
# Iniciar servidor HTTP para health check en segundo plano\n\
python3 -m http.server 8000 &\n\
# Esperar 2 segundos para que el servidor inicie\n\
sleep 2\n\
# Iniciar el bot (bloqueante)\n\
python3 AvalBot_ConLicencias.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Variable de entorno para el token (la defines en Koyeb)
ENV BOT_TOKEN=""

# Ejecutar el script
CMD ["/bin/bash", "/app/start.sh"]
