# 🔑 AVAL CHECKER BOT - CON SISTEMA DE LICENCIAS

Bot de Telegram con sistema completo de licencias y gestión de usuarios.

## ✨ CARACTERÍSTICAS

✅ **Sistema de licencias completo**
- Keys únicas alfanuméricas
- Vinculadas a Telegram ID (no se pueden compartir)
- Expiración automática
- Owner puede generar/revocar keys

✅ **Sistema de proxies gratuitos**
- Rotación automática
- Actualización cada hora
- Cambio de IP por tarjeta

✅ **Multi-usuario**
- Estadísticas por usuario
- Licencias independientes
- Owner con acceso total

## 📦 ARCHIVOS

```
├── AvalBot_ConLicencias.py      # Bot con sistema de licencias
├── Dockerfile                   # Config Docker para Koyeb
├── requirements.txt             # Dependencias
├── .dockerignore               # Archivos a ignorar
└── GUIA_SISTEMA_LICENCIAS.txt  # Guía completa
```

## 🚀 DEPLOYMENT RÁPIDO

### 1. GitHub
```bash
# Sube estos archivos a GitHub:
- AvalBot_ConLicencias.py
- Dockerfile
- requirements.txt
- .dockerignore
```

### 2. Koyeb
1. Ve a https://koyeb.com
2. Sign up with GitHub
3. Create App → GitHub
4. Selecciona tu repo
5. Builder: Dockerfile
6. Environment Variable:
   - Name: `BOT_TOKEN`
   - Value: `8764142166:AAHILjxlNWOe-463WVH8bDYx_Z6fxRp9qWY`
7. Deploy

### 3. Espera 5 minutos
- Status: Healthy ✅
- ¡Bot online 24/7!

## 👑 COMANDOS OWNER (ID: 7448403516)

```
/genkey <días>    - Generar key de licencia
                    Ejemplos:
                    /genkey 1  → 1 día
                    /genkey 7  → 7 días
                    /genkey 30 → 30 días

/listkeys         - Ver todas las keys

/revoke <key>     - Revocar una key
                    Ejemplo:
                    /revoke AVAL-X7K9-M2P4-Q8W1
```

## 👤 COMANDOS USUARIO

```
/start            - Iniciar bot

/redeem <key>     - Activar licencia
                    Ejemplo:
                    /redeem AVAL-X7K9-M2P4-Q8W1

/mykey            - Ver info de licencia

/check CC|MM|YY|CVV - Checkear tarjeta
                      Requiere licencia activa

/status           - Ver estadísticas

/proxies          - Info de proxies
```

## 💼 FLUJO DE VENTA

### Como Owner:

1. Cliente te contacta
2. Generas key: `/genkey 7`
3. Bot te da: `AVAL-X7K9-M2P4-Q8W1`
4. Le envías la key al cliente
5. Cliente activa: `/redeem AVAL-X7K9-M2P4-Q8W1`
6. ✅ Listo, cliente puede usar el bot por 7 días

## 🔒 SEGURIDAD

✅ Keys únicas e irrepetibles
✅ Vinculadas a Telegram ID
✅ No se pueden compartir
✅ Expiración automática
✅ Owner puede revocar en cualquier momento

## 📊 FORMATO DE KEYS

```
AVAL-XXXX-XXXX-XXXX

Ejemplos:
AVAL-X7K9-M2P4-Q8W1
AVAL-A3B7-Z9Q2-K5M8
AVAL-P1L4-W6R3-T2Y9
```

## 📁 BASE DE DATOS

El bot crea automáticamente:

```
licenses.json  - Base de datos de keys
lives.txt      - Tarjetas LIVE
deads.txt      - Tarjetas DEAD
```

## 💰 PRECIOS SUGERIDOS

```
1 día    → $2 USD
7 días   → $10 USD
30 días  → $30 USD
```
(Tú defines tus precios)

## ❓ FAQ

**Q: ¿Puedo compartir mi key?**
A: ❌ No. La key se vincula al primer usuario que la active.

**Q: ¿Qué pasa si expira?**
A: No podrás usar `/check`. Necesitas nueva key.

**Q: ¿El owner necesita key?**
A: ❌ No. El owner tiene acceso total siempre.

**Q: ¿Cuántas keys puedo generar?**
A: ✅ Ilimitadas.

## 🛠️ PERSONALIZACIÓN

### Cambiar Owner ID:
Línea 72:
```python
OWNER_ID = 7448403516  # Tu ID
```

### Agregar más URLs:
Líneas 75-81:
```python
AVAL_URLS = [
    "https://...",
    # Agrega más aquí
]
```

## 📊 EJEMPLO DE USO

### Owner genera key:
```
Owner: /genkey 7

Bot: ✅ Key generada
     🔑 AVAL-X7K9-M2P4-Q8W1
     ⏰ Duración: 7 días
```

### Cliente activa:
```
Cliente: /redeem AVAL-X7K9-M2P4-Q8W1

Bot: ✅ Licencia activada por 7 días
```

### Cliente usa:
```
Cliente: /check 4111111111111111|12|25|123

Bot: 🔄 Checking...
     ✅ LIVE - 4111****1111
```

## 🔄 RENOVACIONES

Cliente quiere renovar:
1. `/genkey 30` (owner)
2. Envías nueva key al cliente
3. `/redeem AVAL-NUEVA-KEY` (cliente)
4. ✅ Extendida por 30 días más

## 📈 ESTADÍSTICAS

Cada usuario ve sus propias stats:
```
/status

📊 TUS ESTADÍSTICAS

✅ Lives: 15
❌ Dead: 42
⚠️ Errors: 3
📈 Total: 60
```

## 🆘 SOPORTE

Si un cliente tiene problemas:

1. Verifica que activó bien: `/mykey`
2. Lista keys activas: `/listkeys`
3. Si necesita nueva: `/genkey <días>`

## 🎯 PRÓXIMOS PASOS

1. ✅ Deploy en Koyeb
2. ✅ Prueba con `/start`
3. ✅ Genera tu primera key con `/genkey 7`
4. ✅ Prueba activarla
5. ✅ Empieza a vender

---

**¿Todo listo?** ¡Empieza a generar keys y vender licencias! 💰
