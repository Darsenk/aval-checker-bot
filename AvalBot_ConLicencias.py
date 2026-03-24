#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║        AVAL CHECKER BOT - CON SISTEMA DE LICENCIAS            ║
║                                                               ║
║  Sistema de keys únicas con expiración                       ║
║  Owner puede generar keys para clientes                      ║
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
# SISTEMA DE PROXIES
# ══════════════════════════════════════════════════════════════

class ProxyRotator:
    """Gestiona proxies gratuitos con rotación"""
    
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        self.last_update = 0
        self.update_interval = 3600
        
    def fetch_free_proxies(self):
        """Obtiene proxies gratuitos"""
        all_proxies = []
        
        # OPTIMIZADO: Solo obtener proxies, sin validación inicial
        # La validación se hace bajo demanda cuando se usan
        try:
            r = requests.get(
                'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                timeout=10
            )
            if r.status_code == 200:
                proxies = r.text.strip().split('\r\n')
                all_proxies.extend([p for p in proxies if ':' in p])
        except:
            logger.warning("⚠️ No se pudo obtener proxies de proxyscrape")
        
        try:
            r = requests.get(
                'https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc',
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                for proxy in data.get('data', []):
                    ip = proxy.get('ip')
                    port = proxy.get('port')
                    if ip and port:
                        all_proxies.append(f"{ip}:{port}")
        except:
            logger.warning("⚠️ No se pudo obtener proxies de geonode")
        
        # Eliminar duplicados y limitar a 20 proxies
        all_proxies = list(set(all_proxies))[:20]
        
        logger.info(f"✅ {len(all_proxies)} proxies cargados (validación bajo demanda)")
        return all_proxies
    
    def _test_proxy(self, proxy):
        try:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            r = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=5)
            return r.status_code == 200
        except:
            return False
    
    def update_proxies(self):
        """Actualiza proxies de forma asíncrona"""
        now = time.time()
        if not self.proxies or (now - self.last_update > self.update_interval):
            logger.info("🔄 Actualizando proxies en segundo plano...")
            # Actualizar en thread separado para no bloquear
            def _async_update():
                self.proxies = self.fetch_free_proxies()
                self.last_update = time.time()
                self.current_index = 0
            
            # Si no hay proxies, esperar la primera carga
            if not self.proxies:
                _async_update()
            else:
                # Si ya hay proxies, actualizar en background
                threading.Thread(target=_async_update, daemon=True).start()
    
    def get_next_proxy(self):
        self.update_proxies()
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index % len(self.proxies)]
        self.current_index += 1
        return proxy

proxy_rotator = ProxyRotator()

# ══════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

fake = Faker('es_ES')

# ══════════════════════════════════════════════════════════════
# ESTADO GLOBAL
# ══════════════════════════════════════════════════════════════
class BotState:
    def __init__(self):
        self.checking = {}  # user_id -> bool
        self.stats = {}     # user_id -> stats
        self.url_index = {}
        self.cards_on_current_url = {}

state = BotState()

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
    """Comando /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Usuario"
    
    # Verificar licencia
    valid, msg = license_mgr.check_license(user_id)
    
    if user_id == OWNER_ID:
        welcome = (
            f"👑 **Bienvenido Owner**\n\n"
            f"ID: `{user_id}`\n\n"
            f"**Comandos de Owner:**\n"
            f"`/genkey <días>` - Generar key\n"
            f"`/listkeys` - Listar keys\n"
            f"`/revoke <key>` - Revocar key\n\n"
            f"**Comandos de usuario:**\n"
            f"`/check CC|MM|YY|CVV` - Checkear\n"
            f"`/status` - Estadísticas\n"
            f"`/proxies` - Info proxies\n"
            f"`/mykey` - Info de tu licencia"
        )
    else:
        welcome = (
            f"🤖 **AVAL CHECKER BOT**\n\n"
            f"Usuario: @{username}\n"
            f"ID: `{user_id}`\n\n"
            f"{msg}\n\n"
            f"**Comandos:**\n"
            f"`/redeem <key>` - Activar licencia\n"
            f"`/check CC|MM|YY|CVV` - Checkear\n"
            f"`/status` - Estadísticas\n"
            f"`/mykey` - Info de licencia\n"
            f"`/help` - Ayuda"
        )
    
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activar key"""
    user_id = update.effective_user.id
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Uso: `/redeem AVAL-XXXX-XXXX-XXXX`",
            parse_mode='Markdown'
        )
        return
    
    key = context.args[0]
    
    success, msg = license_mgr.activate_key(key, user_id)
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def mykey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ver info de licencia"""
    user_id = update.effective_user.id
    
    valid, msg = license_mgr.check_license(user_id)
    
    await update.message.reply_text(
        f"🔑 **Tu Licencia**\n\n{msg}",
        parse_mode='Markdown'
    )

# ══════════════════════════════════════════════════════════════
# RESTO DEL BOT (checker, etc)
# ══════════════════════════════════════════════════════════════

def crear_driver(use_proxy=True):
    """Crea driver con proxy"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--window-size=1920,1080")
    
    if use_proxy:
        proxy = proxy_rotator.get_next_proxy()
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
            logger.info(f"🌐 Proxy: {proxy}")
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    ]
    options.add_argument(f'user-agent={random.choice(user_agents)}')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    stealth(driver,
        languages=["es-ES", "es"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    
    return driver

def get_next_url(user_id):
    """Rota URLs por usuario"""
    if user_id not in state.cards_on_current_url:
        state.cards_on_current_url[user_id] = 0
        state.url_index[user_id] = 0
    
    state.cards_on_current_url[user_id] += 1
    
    if state.cards_on_current_url[user_id] >= CARDS_PER_URL:
        state.url_index[user_id] = (state.url_index[user_id] + 1) % len(AVAL_URLS)
        state.cards_on_current_url[user_id] = 0
    
    return AVAL_URLS[state.url_index[user_id]]

def generate_random_data():
    return {
        'email': f"{fake.first_name().lower()}{random.randint(100,999)}@gmail.com",
        'phone': f"3{random.choice(['10','15','20','25'])}{random.randint(1000000,9999999)}",
        'doc': str(random.randint(10000000, 99999999)),
        'name': fake.first_name(),
        'surname': fake.last_name(),
        'address': f"Calle {random.randint(1,100)} #{random.randint(1,50)}-{random.randint(1,50)}"
    }

@require_license
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checkear tarjeta (requiere licencia)"""
    user_id = update.effective_user.id
    
    text = update.message.text.replace('/check', '').strip()
    
    if not text:
        await update.message.reply_text(
            "❌ Formato: `/check CC|MM|YY|CVV`",
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
        
        await update.message.reply_text(
            f"🔄 Checking: `{masked}`",
            parse_mode='Markdown'
        )
        
        # Simular check (aquí va tu lógica real de Selenium)
        time.sleep(2)
        
        # Resultado simulado
        result = random.choice(['LIVE', 'DEAD', 'ERROR'])
        
        state.stats[user_id]['total'] += 1
        
        if result == 'LIVE':
            state.stats[user_id]['lives'] += 1
            await update.message.reply_text(
                f"✅ **LIVE** - `{masked}`\n"
                f"💳 {cc}|{mm}|{yy}|{cvv}",
                parse_mode='Markdown'
            )
        elif result == 'DEAD':
            state.stats[user_id]['dead'] += 1
            await update.message.reply_text(
                f"❌ **DEAD** - `{masked}`",
                parse_mode='Markdown'
            )
        else:
            state.stats[user_id]['errors'] += 1
            await update.message.reply_text(
                f"⚠️ **ERROR** - `{masked}`",
                parse_mode='Markdown'
            )

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

@require_license
async def proxies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Info de proxies"""
    proxy_rotator.update_proxies()
    
    msg = (
        f"🌐 **PROXIES**\n\n"
        f"✅ Activos: {len(proxy_rotator.proxies)}\n"
        f"🔄 Próximo: {proxy_rotator.current_index % len(proxy_rotator.proxies) + 1 if proxy_rotator.proxies else 0}\n\n"
        f"Actualización automática cada hora"
    )
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ayuda"""
    msg = (
        "📖 **AYUDA**\n\n"
        "**Activar licencia:**\n"
        "`/redeem AVAL-XXXX-XXXX-XXXX`\n\n"
        "**Checkear tarjetas:**\n"
        "`/check 4111111111111111|12|25|123`\n\n"
        "**Ver info:**\n"
        "`/mykey` - Tu licencia\n"
        "`/status` - Tus stats\n"
        "`/proxies` - Proxies activos"
    )
    
    await update.message.reply_text(msg, parse_mode='Markdown')

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    if BOT_TOKEN == "TU_BOT_TOKEN_AQUI":
        print("❌ Configura BOT_TOKEN")
        sys.exit(1)
    
    print("🤖 Iniciando Aval Bot con Sistema de Licencias...")
    print(f"👑 Owner ID: {OWNER_ID}")
    
    # OPTIMIZADO: No bloquear el inicio esperando proxies
    # Se cargan en segundo plano cuando se necesiten
    print("🌐 Proxies se cargarán cuando sean necesarios...")
    
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
    app.add_handler(CommandHandler("proxies", proxies_command))
    app.add_handler(CommandHandler("help", help_command))
    
    print("✅ Bot activo con sistema de licencias")
    print("💡 Usa /genkey para generar keys")
    
    # Cargar proxies en segundo plano después de iniciar
    def load_proxies_async():
        time.sleep(5)  # Esperar 5s después del inicio
        logger.info("🔄 Cargando proxies en segundo plano...")
        proxy_rotator.update_proxies()
        logger.info(f"✅ {len(proxy_rotator.proxies)} proxies listos")
    
    threading.Thread(target=load_proxies_async, daemon=True).start()
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
