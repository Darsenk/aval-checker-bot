# Usar imagen base de Selenium con Chrome
FROM selenium/standalone-chrome:latest

# Cambiar a usuario root para instalar cosas
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
COPY AvalBot_ConProxies.py .

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Exponer puerto (Koyeb lo requiere)
EXPOSE 8080

# Crear un script de inicio
RUN echo '#!/bin/bash\n\
python3 AvalBot_ConProxies.py &\n\
python3 -m http.server 8080\n\
' > /app/start.sh && chmod +x /app/start.sh

# Ejecutar el script
CMD ["/bin/bash", "/app/start.sh"]
