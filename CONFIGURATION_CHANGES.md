# 📋 Documentación Detallada de Cambios de Configuración

Este documento detalla todos los cambios realizados en los archivos de configuración críticos para habilitar el embedding de Superset.

## 🔧 **Archivo 1: `superset/docker/pythonpath_dev/superset_config_docker.py`**

### **Propósito:**
Archivo de configuración personalizada de Superset que sobrescribe la configuración por defecto para habilitar embedding y CORS.

### **Estado Original:**
El archivo no existía o estaba vacío/mínimo.

### **Cambios Realizados:**

#### **1. Imports y Configuración Base**
```python
from superset.security import SupersetSecurityManager
import logging

# Logging para debug
logging.getLogger("flask_cors").level = logging.DEBUG
```

**Propósito:** Importar clases necesarias y habilitar logging de CORS para debugging.

#### **2. Feature Flags - CRÍTICO**
```python
# Feature flags - Solo las esenciales para embedding
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,  # ⚠️ CRÍTICO - Sin esto no funciona embedding
    "ENABLE_TEMPLATE_PROCESSING": True,  # Útil para dashboards dinámicos
}
```

**Propósito:** 
- `EMBEDDED_SUPERSET` es absolutamente crítico. Sin este flag, Superset rechaza todas las peticiones de embedding.
- `ENABLE_TEMPLATE_PROCESSING` permite usar templates dinámicos en dashboards (opcional pero útil).
- Se eliminaron flags innecesarios como `ALERT_REPORTS` y `DASHBOARD_RBAC` que ya están configurados por defecto.

#### **3. Guest Token Configuration - OBLIGATORIO**
```python
GUEST_TOKEN_JWT_SECRET = "mi-clave-superset-local-jwt-secret-minimo-32-caracteres-2024"
GUEST_TOKEN_JWT_EXP_SECONDS = 300  # 5 minutos
```

**Propósito:** 
- `GUEST_TOKEN_JWT_SECRET`: Clave para firmar tokens JWT. DEBE ser mínimo 32 caracteres.
- `GUEST_TOKEN_JWT_EXP_SECONDS`: Tiempo de vida de los guest tokens (300 segundos = 5 minutos).

#### **4. Configuración CORS - CRÍTICA**
```python
ENABLE_CORS = True

CORS_OPTIONS = {
    "origins": [
        # ⚠️ CRITICAL: URLs MUST end with trailing slash "/"
        "http://localhost:3000/", "http://localhost:3001/",
        "http://127.0.0.1:3000/", "http://127.0.0.1:3001/",
        "http://192.168.1.137:3000/", "http://192.168.1.137:3001/",
        
        # Test servers
        "http://localhost:8000/", "http://localhost:8080/", "http://localhost:9000/",
        "http://127.0.0.1:8000/", "http://127.0.0.1:8080/", "http://127.0.0.1:9000/",
        "http://192.168.1.137:8000/", "http://192.168.1.137:8080/", "http://192.168.1.137:9000/",
        
        # Odoo ports
        "http://localhost:8069/", "http://127.0.0.1:8069/", "http://192.168.1.137:8069/",
        
        # Superset itself
        "http://192.168.1.137:8088/", "http://localhost:8088/", "http://127.0.0.1:8088/",
        
        # For local file:// development
        "null",
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin",
        "Access-Control-Allow-Origin", "Access-Control-Allow-Headers", "Access-Control-Allow-Methods"
    ],
    "supports_credentials": True
}
```

**Problema Crítico Resuelto:** 
- **ANTES:** URLs sin barra final (`"http://localhost:3000"`) → CORS fallaba
- **DESPUÉS:** URLs con barra final (`"http://localhost:3000/"`) → CORS funciona

**Razón:** Superset es estricto con el formato de URLs para CORS. Si la URL de la aplicación externa tiene barra final y la configuración no, falla la validación.

#### **5. Seguridad para Embedding**
```python
# ⚠️ CSRF - Disabled for development embedding (CRITICAL)
WTF_CSRF_ENABLED = False

# Para producción usar:
# WTF_CSRF_ENABLED = True
# WTF_CSRF_EXEMPT_LIST = [
#     'superset.views.core.dashboard_embedded',
#     'superset.security.api.guest_token'
# ]
```

**Propósito:** CSRF debe estar desactivado para development o configurado con excepciones específicas para production.

#### **6. X-Frame-Options para iframes**
```python
# ⚠️ Talisman - Disabled for development
TALISMAN_ENABLED = False

# Para producción:
# TALISMAN_ENABLED = True
# TALISMAN_CONFIG = {
#     "frame_options": "ALLOWFROM",
#     "frame_options_allow_from": ["https://tu-dominio.com/"],
# }

ENABLE_IFRAME_EMBEDDING = True
```

**Propósito:** 
- `TALISMAN_ENABLED = False`: Desactiva protecciones X-Frame-Options para development
- `ENABLE_IFRAME_EMBEDDING = True`: Habilita específicamente el embedding en iframes

#### **7. Configuración de Roles y Permisos**
```python
PUBLIC_ROLE_LIKE_GAMMA = True
GUEST_ROLE_NAME = "Public"

GUEST_TOKEN_HEADER_NAME = "X-GuestToken"
GUEST_TOKEN_AUDIENCE = "superset"

class CustomSecurityManager(SupersetSecurityManager):
    def get_guest_rls_filters(self, dataset):
        return []
    def get_rls_filters(self, table):
        return []

CUSTOM_SECURITY_MANAGER = CustomSecurityManager
```

**Propósito:** Configurar permisos para guest users y Row Level Security (RLS).

#### **8. Configuración Específica para SDK**
```python
PUBLIC_ROLE_LIKE = "Gamma"
GUEST_TOKEN_COOKIE_NAME = None  # Disable cookies for guest tokens
GUEST_TOKEN_COOKIE_DOMAIN = None

SUPERSET_WEBSERVER_ADDRESS = '0.0.0.0'
SUPERSET_WEBSERVER_PORT = 8088
```

**Propósito:** Configuraciones adicionales para que el SDK funcione correctamente.

#### **9. Logging para Debug**
```python
cors_logger = logging.getLogger("flask_cors")
cors_logger.setLevel(logging.DEBUG)

if not cors_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    cors_logger.addHandler(handler)
```

**Propósito:** Logging detallado para debugging de problemas CORS.

#### **10. Configuración Environment Tag (Ocultar tag "Development")**
```python
# Ocultar completamente el tag "Development" ya que usamos docker-compose-non-dev.yml
ENVIRONMENT_TAG_CONFIG = {"variable": "SUPERSET_ENV", "values": {}}
```

**Propósito:** 
- Ocultar el tag "Development" que aparece por defecto en la interfaz de Superset
- Al usar `docker-compose-non-dev.yml` no tiene sentido mostrar un tag de development
- El tag aparece por la funcionalidad "Environment Tag" introducida en Superset 2.1.0, no por el nombre del archivo Docker

#### **11. Información de Debug**
```python
print("=" * 60)
print("🚀 SUPERSET EMBEDDING CONFIGURATION LOADED")
print("=" * 60)
print(f"✅ EMBEDDED_SUPERSET: {FEATURE_FLAGS.get('EMBEDDED_SUPERSET', False)}")
print(f"✅ CORS Enabled: {ENABLE_CORS}")
print(f"✅ CSRF Enabled: {WTF_CSRF_ENABLED}")
print(f"✅ Talisman Enabled: {TALISMAN_ENABLED}")
print(f"✅ Iframe Embedding: {ENABLE_IFRAME_EMBEDDING}")
print(f"✅ Guest Token Secret: {'SET' if GUEST_TOKEN_JWT_SECRET else 'NOT SET'}")
print("=" * 60)
```

**Propósito:** Confirmación visual en logs de que la configuración se cargó correctamente.

---

## 🐳 **Archivo 2: `superset/docker-compose-non-dev.yml`**

### **Propósito:**
Archivo Docker Compose que define los servicios y configuración de contenedores para Superset.

### **Cambio Crítico Realizado:**

#### **Sección `x-superset-volumes`**

**ANTES (INCORRECTO):**
```yaml
x-superset-volumes:
  &superset-volumes
  - ./docker:/app/docker
  - superset_home:/app/superset_home
  - ./superset_config.py:/app/pythonpath_dev/superset_config.py
  - ./superset_config_docker.py:/app/pythonpath/superset_config_docker.py
```

**DESPUÉS (CORRECTO):**
```yaml
x-superset-volumes:
  &superset-volumes
  - ./docker:/app/docker
  - superset_home:/app/superset_home
  - ./docker/pythonpath_dev/superset_config_docker.py:/app/pythonpath_dev/superset_config_docker.py
```

### **Problema Resuelto:**

#### **1. Archivos Inexistentes**
- **Problema:** Las rutas `./superset_config.py` y `./superset_config_docker.py` apuntaban a archivos en la raíz del proyecto que no existían.
- **Solución:** Usar la ruta correcta `./docker/pythonpath_dev/superset_config_docker.py` que apunta al archivo real.

#### **2. Montaje de Volúmenes Incorrecto**
- **Problema:** Docker no podía montar los archivos porque no existían, causando errores silenciosos.
- **Resultado:** La configuración personalizada no se cargaba, usando solo configuración por defecto.
- **Solución:** Montar el archivo existente en la ruta correcta dentro del contenedor.

#### **3. Ruta de Destino Corregida**
- **Problema:** Montaje a `/app/pythonpath/` (sin `_dev`)
- **Solución:** Montaje a `/app/pythonpath_dev/` (con `_dev`) que es donde Superset busca configuraciones de desarrollo.

---

## 🔍 **Verificación de Cambios**

### **Cómo Verificar que los Cambios Funcionan:**

#### **1. Verificar Configuración Cargada:**
```bash
docker-compose -f docker-compose-non-dev.yml logs superset | grep "EMBEDDING"
```
**Output esperado:**
```
🚀 SUPERSET EMBEDDING CONFIGURATION LOADED
✅ EMBEDDED_SUPERSET: True
✅ CORS Enabled: True
```

#### **2. Verificar CORS Funcionando:**
```bash
curl -I -H "Origin: http://localhost:3000/" http://192.168.1.137:8088/health
```
**Output esperado:** Header `Access-Control-Allow-Origin: http://localhost:3000/`

#### **3. Verificar Guest Tokens:**
```bash
TOKEN=$(curl -s -X POST "http://192.168.1.137:8088/api/v1/security/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin", "provider": "db"}' | jq -r '.access_token')

curl -s -X POST "http://192.168.1.137:8088/api/v1/security/guest_token/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user": {"username": "test"}, "resources": [{"type": "dashboard", "id": "uuid"}], "rls": []}' | jq .
```
**Output esperado:** JSON con campo `"token": "eyJ..."`

---

## ⚠️ **Advertencias Importantes**

### **Para Desarrollo:**
1. **CSRF desactivado** - Solo para development
2. **Talisman desactivado** - Solo para development  
3. **CORS muy permisivo** - Incluye localhost e IPs locales

### **Para Producción:**
1. **Activar CSRF** con excepciones específicas
2. **Activar Talisman** con dominios específicos
3. **CORS restrictivo** solo para dominios de producción
4. **GUEST_TOKEN_JWT_SECRET** debe ser ultra seguro (64+ caracteres)
5. **URLs HTTPS** obligatorias en producción

### **Comandos para Aplicar Cambios:**
```bash
# Reiniciar para aplicar cambios
cd superset
docker-compose -f docker-compose-non-dev.yml restart superset

# Verificar que funciona
curl http://192.168.1.137:8088/health
```

---

**Fecha de Documentación:** 17 de Agosto, 2025  
**Estado:** ✅ Cambios aplicados y funcionando  
**Verificado:** Aplicaciones Next.js e iframe-example.html funcionando al 100%