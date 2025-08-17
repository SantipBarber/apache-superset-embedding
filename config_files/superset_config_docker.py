from superset.security import SupersetSecurityManager
import logging


# Logging para debug
logging.getLogger("flask_cors").level = logging.DEBUG

# ============================================================================
# CONFIGURACIÓN PARA EMBEDDING - CRÍTICA
# ============================================================================

# Feature flags - Solo las esenciales para embedding
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,  # CRÍTICO para embedding
    "ENABLE_TEMPLATE_PROCESSING": True,  # Útil para dashboards dinámicos
}

# Guest token configuration - OBLIGATORIO para embedding
GUEST_TOKEN_JWT_SECRET = "mi-clave-superset-local-jwt-secret-minimo-32-caracteres-2024"
GUEST_TOKEN_JWT_EXP_SECONDS = 300  # 5 minutos

# ============================================================================
# CONFIGURACIÓN CORS - CRÍTICA PARA APLICACIONES EXTERNAS
# ============================================================================

# Habilitar CORS
ENABLE_CORS = True

# Configuración CORS detallada
CORS_OPTIONS = {
    "origins": [
        # Desarrollo local - Next.js (con y sin barra final)
        "http://localhost:3000",          
        "http://localhost:3000/",         # Con barra final
        "http://localhost:3001",          
        "http://localhost:3001/",         # Con barra final
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3000/",         # Con barra final
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3001/",         # Con barra final
        "http://192.168.1.137:3000",      
        "http://192.168.1.137:3000/",     # Con barra final
        "http://192.168.1.137:3001",      
        "http://192.168.1.137:3001/",     # Con barra final
        # Desarrollo local - Servidores de prueba
        "http://localhost:8000",
        "http://localhost:8000/",         # Con barra final
        "http://localhost:8080",
        "http://localhost:8080/",         # Con barra final
        "http://localhost:9000",
        "http://localhost:9000/",         # Con barra final
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8000/",         # Con barra final
        "http://127.0.0.1:8080", 
        "http://127.0.0.1:8080/",         # Con barra final
        "http://127.0.0.1:9000",
        "http://127.0.0.1:9000/",         # Con barra final
        "http://192.168.1.137:8000",
        "http://192.168.1.137:8000/",     # Con barra final
        "http://192.168.1.137:8080",
        "http://192.168.1.137:8080/",     # Con barra final
        "http://192.168.1.137:9000",
        "http://192.168.1.137:9000/",     # Con barra final
        # Odoo local
        "http://localhost:8069",
        "http://localhost:8069/",         # Con barra final
        "http://127.0.0.1:8069",
        "http://127.0.0.1:8069/",         # Con barra final
        "http://192.168.1.137:8069",
        "http://192.168.1.137:8069/",     # Con barra final
        # Superset mismo
        "http://192.168.1.137:8088",
        "http://192.168.1.137:8088/",     # Con barra final
        "http://localhost:8088",
        "http://localhost:8088/",         # Con barra final
        "http://127.0.0.1:8088",
        "http://127.0.0.1:8088/",         # Con barra final
        # Desarrollo - permitir null origin para file://
        "null",
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Methods"
    ],
    "supports_credentials": True
}

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD PARA EMBEDDING
# ============================================================================

# CSRF - Desactivar para embedding (CRÍTICO)
WTF_CSRF_ENABLED = False

# Alternativamente, si necesitas CSRF activado, exenta las rutas de embedding:
# WTF_CSRF_ENABLED = True
# WTF_CSRF_EXEMPT_LIST = [
#     'superset.views.core.dashboard_embedded',
#     'superset.security.api.guest_token'
# ]

# ============================================================================
# CONFIGURACIÓN X-FRAME-OPTIONS PARA IFRAMES
# ============================================================================

# Opción 1: Desactivar Talisman completamente (MÁS SIMPLE para desarrollo)
TALISMAN_ENABLED = False

# Opción 2: Configurar Talisman para permitir iframes específicos
# TALISMAN_ENABLED = True
# TALISMAN_CONFIG = {
#     "frame_options": "ALLOWFROM",
#     "frame_options_allow_from": [
#         "http://localhost:3000",
#         "http://192.168.1.137:3000",
#         "http://localhost:8069",
#         "http://192.168.1.137:8069",
#     ],
#     "content_security_policy": False,
#     "strict_transport_security": False,
# }

# Habilitar embedding de iframes
ENABLE_IFRAME_EMBEDDING = True

# ============================================================================
# CONFIGURACIÓN DE ROLES Y PERMISOS
# ============================================================================

# Configuración del rol público
PUBLIC_ROLE_LIKE_GAMMA = True
GUEST_ROLE_NAME = "Public"

# Permisos adicionales para guest tokens
GUEST_TOKEN_HEADER_NAME = "X-GuestToken"
GUEST_TOKEN_AUDIENCE = "superset"


class CustomSecurityManager(SupersetSecurityManager):
    def get_guest_rls_filters(self, dataset):
        return []
    def get_rls_filters(self, table):
        return []

CUSTOM_SECURITY_MANAGER = CustomSecurityManager

# ============================================================================
# CONFIGURACIÓN ADICIONAL PARA DESARROLLO
# ============================================================================

# Headers de seguridad adicionales
SEND_FILE_MAX_AGE_DEFAULT = 0

# Configuración de cache más permisiva para desarrollo
CACHE_CONFIG = {
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 60
}

# ============================================================================
# CONFIGURACIÓN ESPECÍFICA PARA EMBEDDED SDK
# ============================================================================

# Asegurar que las URLs públicas estén configuradas
PUBLIC_ROLE_LIKE = "Gamma"

# Configuración adicional para guest tokens
GUEST_TOKEN_COOKIE_NAME = None  # Desactivar cookies para guest tokens
GUEST_TOKEN_COOKIE_DOMAIN = None

# Configuración de URL pública (importante para el SDK)
import socket
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

# Usar la IP configurada para asegurar consistencia
SUPERSET_WEBSERVER_ADDRESS = '0.0.0.0'
SUPERSET_WEBSERVER_PORT = 8088

# ============================================================================
# CONFIGURACIÓN DEL TAG DE ENVIRONMENT (PERSONALIZAR TAG "Development")
# ============================================================================

# Ocultar completamente el tag "Development" ya que usamos docker-compose-non-dev.yml
ENVIRONMENT_TAG_CONFIG = {"variable": "SUPERSET_ENV", "values": {}}

# ============================================================================
# CONFIGURACIÓN DE LOGGING PARA DEBUG
# ============================================================================


# Configurar logger de Flask-CORS
cors_logger = logging.getLogger("flask_cors")
cors_logger.setLevel(logging.DEBUG)

# Handler para consola
if not cors_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    cors_logger.addHandler(handler)

# ============================================================================
# OVERRIDE DE CONFIGURACIONES ESPECÍFICAS DEL DOCKER ORIGINAL
# ============================================================================

# Sobrescribir cualquier configuración conflictiva del archivo original
# que pueda interferir con el embedding

print("=" * 60)
print("🚀 SUPERSET EMBEDDING CONFIGURATION LOADED")
print("=" * 60)
print(f"✅ EMBEDDED_SUPERSET: {FEATURE_FLAGS.get('EMBEDDED_SUPERSET', False)}")
print(f"✅ CORS Enabled: {ENABLE_CORS}")
print(f"✅ CSRF Enabled: {WTF_CSRF_ENABLED}")
print(f"✅ Talisman Enabled: {TALISMAN_ENABLED}")
print(f"✅ Iframe Embedding: {ENABLE_IFRAME_EMBEDDING}")
print(f"✅ Guest Token Secret: {'SET' if GUEST_TOKEN_JWT_SECRET else 'NOT SET'}")
# Mostrar información del Environment Tag
env_tag_values = ENVIRONMENT_TAG_CONFIG.get('values', {})
if not env_tag_values:
    print("✅ Environment Tag: OCULTO (sin tag 'Development')")
else:
    env_tag_text = env_tag_values.get('development', {}).get('text', 'Default')
    print(f"✅ Environment Tag: '{env_tag_text}'")
print("=" * 60)

# ============================================================================
# NOTAS IMPORTANTES:
# ============================================================================
# 1. Este archivo se importa DESPUÉS de superset_config.py
# 2. Las configuraciones aquí SOBRESCRIBEN las del archivo original
# 3. Para producción, configura TALISMAN_ENABLED = True con dominios específicos
# 4. Para producción, activa WTF_CSRF_ENABLED = True con excepciones específicas
# 5. El GUEST_TOKEN_JWT_SECRET debe ser único y seguro en producción
