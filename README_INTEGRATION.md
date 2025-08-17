# 📊 Integración Apache Superset con Aplicaciones Externas - Guía Completa

## 🎯 **Objetivo Principal**
Integrar Apache Superset dentro de aplicaciones externas (especialmente Odoo) usando iframes, permitiendo que usuarios autenticados visualicen dashboards sin necesidad de login adicional en Superset.

## ✅ **Estado Actual - ÉXITO COMPLETO**

### **Aplicaciones Funcionando:**
- **Next.js**: http://localhost:3001 ✅
- **Ejemplo HTML/iframe**: http://localhost:8080/iframe-example.html ✅
- **Superset**: http://192.168.1.137:8088 ✅

### **Funcionalidades Implementadas:**
- ✅ Configuración CORS completa con URLs terminadas en `/`
- ✅ Embedding habilitado correctamente
- ✅ Guest tokens funcionando automáticamente
- ✅ Autenticación transparente
- ✅ Dashboards renderizando en tamaño completo
- ✅ SDK oficial de Superset funcionando

## 📋 **Problemas Resueltos y Lecciones Críticas**

### ❌ **Problemas Encontrados:**
1. **CORS URLs sin barra final** → URLs deben terminar obligatoriamente en `/`
2. **Rutas Docker incorrectas** → Archivos de configuración no se montaban correctamente
3. **API endpoints inconsistentes** → Diferencia entre gestión y embedding
4. **iframe tamaño incorrecto** → SDK no configura tamaño automáticamente
5. **Mixing iframe manual vs SDK** → SDK oficial es más robusto

### ✅ **Soluciones Implementadas:**
1. **CORS con barras finales**: `"http://localhost:3000/"` (NUNCA `"http://localhost:3000"`)
2. **Docker volumes corregidos**: Rutas absolutas correctas en docker-compose
3. **UUID vs ID numérico**: Usar UUID para embedding, ID numérico para gestión
4. **Forzar tamaño iframe**: CSS manual después de creación del SDK
5. **SDK oficial siempre**: Abandonar iframe manual por SDK oficial

## 🔧 **Configuración Técnica Completa**

### **1. Configuración Core de Superset para Embedding**

**Archivo:** `superset/docker/pythonpath_dev/superset_config_docker.py`

#### **Cambios Críticos Realizados:**

```python
# ============================================================================
# CONFIGURACIÓN PARA EMBEDDING - CRÍTICA
# ============================================================================

# Feature flags - DEBE incluir EMBEDDED_SUPERSET
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "EMBEDDED_SUPERSET": True,  # ⚠️ CRÍTICO - Sin esto no funciona embedding
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# Guest token configuration - OBLIGATORIO para embedding
GUEST_TOKEN_JWT_SECRET = "mi-clave-superset-local-jwt-secret-minimo-32-caracteres-2024"
GUEST_TOKEN_JWT_EXP_SECONDS = 300  # 5 minutos (ajustable según necesidades)

# ============================================================================
# CONFIGURACIÓN CORS - CRÍTICA PARA APLICACIONES EXTERNAS
# ============================================================================

# Habilitar CORS
ENABLE_CORS = True

# ⚠️ IMPORTANTE: URLs DEBEN terminar en barra final "/"
CORS_OPTIONS = {
    "origins": [
        # Next.js ports
        "http://localhost:3000/", "http://localhost:3001/",
        "http://127.0.0.1:3000/", "http://127.0.0.1:3001/",
        "http://192.168.1.137:3000/", "http://192.168.1.137:3001/",
        
        # Servidores de prueba
        "http://localhost:8000/", "http://localhost:8080/", "http://localhost:9000/",
        "http://127.0.0.1:8000/", "http://127.0.0.1:8080/", "http://127.0.0.1:9000/",
        "http://192.168.1.137:8000/", "http://192.168.1.137:8080/", "http://192.168.1.137:9000/",
        
        # Odoo ports
        "http://localhost:8069/", "http://127.0.0.1:8069/", "http://192.168.1.137:8069/",
        
        # Superset mismo
        "http://192.168.1.137:8088/", "http://localhost:8088/", "http://127.0.0.1:8088/",
        
        # Para development local file://
        "null",
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": [
        "Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin",
        "Access-Control-Allow-Origin", "Access-Control-Allow-Headers", "Access-Control-Allow-Methods"
    ],
    "supports_credentials": True
}

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD PARA EMBEDDING
# ============================================================================

# ⚠️ CSRF - Desactivar para development embedding (CRÍTICO)
WTF_CSRF_ENABLED = False

# Para producción, usar en su lugar:
# WTF_CSRF_ENABLED = True
# WTF_CSRF_EXEMPT_LIST = [
#     'superset.views.core.dashboard_embedded',
#     'superset.security.api.guest_token'
# ]

# ============================================================================
# CONFIGURACIÓN X-FRAME-OPTIONS PARA IFRAMES
# ============================================================================

# ⚠️ Talisman - Desactivar para development (MÁS SIMPLE)
TALISMAN_ENABLED = False

# Para producción, usar configuración específica:
# TALISMAN_ENABLED = True
# TALISMAN_CONFIG = {
#     "frame_options": "ALLOWFROM",
#     "frame_options_allow_from": [
#         "https://tu-odoo-produccion.com/",
#     ],
#     "content_security_policy": False,
#     "strict_transport_security": False,
# }

# ⚠️ Habilitar embedding de iframes
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

# Custom security manager para RLS (Row Level Security)
class CustomSecurityManager(SupersetSecurityManager):
    def get_guest_rls_filters(self, dataset):
        return []
    def get_rls_filters(self, table):
        return []

CUSTOM_SECURITY_MANAGER = CustomSecurityManager

# ============================================================================
# CONFIGURACIÓN ESPECÍFICA PARA EMBEDDED SDK
# ============================================================================

# Asegurar que las URLs públicas estén configuradas
PUBLIC_ROLE_LIKE = "Gamma"

# Configuración adicional para guest tokens
GUEST_TOKEN_COOKIE_NAME = None  # Desactivar cookies para guest tokens
GUEST_TOKEN_COOKIE_DOMAIN = None

# Configuración de URL pública (importante para el SDK)
SUPERSET_WEBSERVER_ADDRESS = '0.0.0.0'
SUPERSET_WEBSERVER_PORT = 8088
```

### **2. Configuración Docker Corregida**

**Archivo:** `superset/docker-compose-non-dev.yml`

#### **Cambios Críticos Realizados:**

```yaml
# ⚠️ ANTES (INCORRECTO):
# - ./superset_config.py:/app/pythonpath_dev/superset_config.py
# - ./superset_config_docker.py:/app/pythonpath/superset_config_docker.py

# ✅ DESPUÉS (CORRECTO):
x-superset-volumes:
  &superset-volumes
  - ./docker:/app/docker
  - superset_home:/app/superset_home
  - ./docker/pythonpath_dev/superset_config_docker.py:/app/pythonpath_dev/superset_config_docker.py
```

**Problema resuelto:** Las rutas anteriores apuntaban a archivos inexistentes en la raíz del proyecto. La nueva configuración apunta correctamente al archivo de configuración dentro del directorio docker.

## 🔑 **Flujo de Autenticación y Embedding Completo**

### **Arquitectura de Integración:**
```
[Usuario] → [App Externa] → [Obtener Access Token] → [Generar Guest Token] → [SDK Embedding] → [Dashboard]
```

### **Paso 1: Habilitar Embedding en Dashboard**
```bash
# 1. Obtener token de administrador
TOKEN=$(curl -s -X POST \
  "http://192.168.1.137:8088/api/v1/security/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin", "provider": "db"}' | jq -r '.access_token')

# 2. Habilitar embedding en dashboard específico (ejemplo: dashboard ID 11)
curl -s -X PUT \
  "http://192.168.1.137:8088/api/v1/dashboard/11/embedded" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"allowed_domains": ["http://localhost:3001/", "http://localhost:8080/", "http://192.168.1.137:3000/"]}'

# 3. Respuesta contiene el UUID crítico para embedding:
# {
#   "result": {
#     "uuid": "1de70455-f2a3-4478-83b6-fc61ad9800bf",
#     "dashboard_id": "11",
#     "allowed_domains": ["http://localhost:3001/", ...]
#   }
# }
```

### **Paso 2: Generar Guest Token (Para cada acceso)**
```bash
# Crear guest token para acceso sin login usando el UUID
curl -s -X POST \
  "http://192.168.1.137:8088/api/v1/security/guest_token/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "username": "guest_user",
      "first_name": "Guest", 
      "last_name": "User"
    },
    "resources": [{
      "type": "dashboard",
      "id": "1de70455-f2a3-4478-83b6-fc61ad9800bf"
    }],
    "rls": []
  }' | jq -r '.token'

# Retorna: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **Paso 3: Integración con SDK Oficial**
```javascript
// Cargar SDK de Superset
import { embedDashboard } from '@superset-ui/embedded-sdk';
// O para HTML: <script src="https://unpkg.com/@superset-ui/embedded-sdk@0.2.0"></script>

// Función para integrar dashboard
async function embedSupersetDashboard() {
  // 1. Obtener guest token (desde tu backend)
  const guestToken = await getGuestTokenFromBackend();
  
  // 2. Configurar container
  const container = document.getElementById('superset-container');
  container.innerHTML = ''; // Limpiar contenido anterior
  
  // 3. Embeber dashboard usando SDK oficial
  await embedDashboard({
    id: "1de70455-f2a3-4478-83b6-fc61ad9800bf", // UUID del dashboard
    supersetDomain: "http://192.168.1.137:8088",
    mountPoint: container,
    fetchGuestToken: () => guestToken,
    dashboardUiConfig: {
      hideTitle: false,
      hideTab: false,
      hideChartControls: false,
    }
  });
  
  // 4. Forzar tamaño correcto del iframe
  setTimeout(() => {
    const iframe = container.querySelector('iframe');
    if (iframe) {
      iframe.style.width = '100%';
      iframe.style.height = '800px';
      iframe.style.border = 'none';
    }
  }, 1000);
}
```

## 🚀 **Pasos para Verificar la Integración**

### **1. Reiniciar Superset con Nueva Configuración**
```bash
cd superset

# Reiniciar servicios para aplicar cambios
docker-compose -f docker-compose-non-dev.yml restart superset

# Verificar que está funcionando
curl http://192.168.1.137:8088/health
# Debe retornar: OK
```

### **2. Configurar Dashboards para Embedding**
```bash
# Ejecutar script automático (desde raíz del proyecto)
./setup_embedding_auto.sh
```

**Output esperado:**
```
🚀 Configurando embedding automático en Superset...
✅ Superset está accesible
✅ Token obtenido exitosamente
📊 Encontrados X dashboards
🔧 Habilitando embedding para: 'Dashboard Name'
   ✅ Embedding habilitado exitosamente
   📋 UUID para embedding: 1de70455-f2a3-4478-83b6-fc61ad9800bf
```

### **3. Probar Aplicaciones de Ejemplo**

#### **Next.js Application:**
```bash
cd superset-test-app
npm install  # Solo primera vez
npm run dev  # Inicia en http://localhost:3001
```

#### **HTML Example:**
```bash
# Iniciar servidor simple (desde raíz)
python3 -m http.server 8080
# Abrir: http://localhost:8080/iframe-example.html
```

### **4. Verificar Funcionamiento Completo**
- ✅ Dashboard aparece en lista desplegable
- ✅ Al seleccionar dashboard, se carga automáticamente
- ✅ Dashboard se muestra en tamaño completo
- ✅ No solicita login adicional
- ✅ Todos los controles del dashboard funcionan

## 🚀 **Roadmap para Integración Odoo**

### **Fase 1: Módulo Odoo Base (1-2 días)**
```python
# models/superset_dashboard.py
class SupersetDashboard(models.Model):
    _name = 'superset.dashboard'
    _description = 'Superset Dashboard Configuration'
    
    name = fields.Char('Dashboard Name', required=True)
    uuid = fields.Char('Superset UUID', required=True)
    dashboard_id = fields.Char('Superset Dashboard ID')
    superset_url = fields.Char('Superset URL', default='http://192.168.1.137:8088')
    allowed_users = fields.Many2many('res.users', string='Allowed Users')
    allowed_groups = fields.Many2many('res.groups', string='Allowed Groups')
    active = fields.Boolean('Active', default=True)
```

### **Fase 2: Controlador de Proxy (1 semana)**
```python
# controllers/superset_controller.py
import requests
import json
from odoo import http
from odoo.http import request

class SupersetController(http.Controller):
    
    @http.route('/superset/dashboard/<uuid>', type='http', auth='user', website=True)
    def dashboard_embedded(self, uuid, **kwargs):
        # 1. Verificar permisos del usuario actual
        dashboard = request.env['superset.dashboard'].sudo().search([('uuid', '=', uuid)])
        if not dashboard or not self._check_user_permissions(dashboard):
            return request.render('superset.access_denied')
        
        # 2. Obtener credenciales Superset del usuario
        superset_config = self._get_user_superset_config()
        
        # 3. Generar guest token
        guest_token = self._generate_guest_token(uuid, superset_config)
        
        # 4. Renderizar vista con embedding
        return request.render('superset.dashboard_embedded', {
            'dashboard_uuid': uuid,
            'guest_token': guest_token,
            'superset_url': dashboard.superset_url,
            'dashboard_name': dashboard.name
        })
    
    def _generate_guest_token(self, dashboard_uuid, config):
        # Implementar misma lógica que aplicaciones de prueba
        access_token = self._get_admin_access_token(config)
        
        guest_token_response = requests.post(
            f"{config['superset_url']}/api/v1/security/guest_token/",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            json={
                'user': {
                    'username': f'odoo_user_{request.env.user.id}',
                    'first_name': request.env.user.name.split()[0],
                    'last_name': ' '.join(request.env.user.name.split()[1:])
                },
                'resources': [{'type': 'dashboard', 'id': dashboard_uuid}],
                'rls': self._get_user_rls_rules()
            }
        )
        return guest_token_response.json()['token']
```

### **Fase 3: Vista de Integración (1 semana)**
```xml
<!-- views/superset_dashboard_view.xml -->
<odoo>
    <template id="dashboard_embedded" name="Superset Dashboard Embedded">
        <t t-call="website.layout">
            <div class="container-fluid">
                <div class="row">
                    <div class="col-12">
                        <h2 t-esc="dashboard_name"/>
                        <div id="superset-container" style="width: 100%; height: 800px;"></div>
                    </div>
                </div>
            </div>
            
            <!-- Cargar SDK de Superset -->
            <script src="https://unpkg.com/@superset-ui/embedded-sdk@0.2.0"></script>
            
            <script type="text/javascript">
                document.addEventListener('DOMContentLoaded', async function() {
                    const container = document.getElementById('superset-container');
                    
                    // Usar exactamente la misma implementación que Next.js/HTML
                    await supersetEmbeddedSdk.embedDashboard({
                        id: "<t t-esc="dashboard_uuid"/>",
                        supersetDomain: "<t t-esc="superset_url"/>",
                        mountPoint: container,
                        fetchGuestToken: () => "<t t-esc="guest_token"/>",
                        dashboardUiConfig: {
                            hideTitle: false,
                            hideTab: false,
                            hideChartControls: false,
                        }
                    });
                    
                    // Forzar tamaño correcto (igual que aplicaciones de prueba)
                    setTimeout(() => {
                        const iframe = container.querySelector('iframe');
                        if (iframe) {
                            iframe.style.width = '100%';
                            iframe.style.height = '800px';
                            iframe.style.border = 'none';
                        }
                    }, 1000);
                });
            </script>
        </t>
    </template>
</odoo>
```

### **Fase 4: Configuración de Usuarios (2-4 semanas)**
```python
# models/res_users.py
class ResUsers(models.Model):
    _inherit = 'res.users'
    
    superset_username = fields.Char('Superset Username')
    superset_token = fields.Text('Superset Token', groups='base.group_system')
    allowed_dashboards = fields.Many2many('superset.dashboard', string='Allowed Dashboards')
    
    def get_superset_permissions(self):
        """Retorna dashboards que el usuario puede ver basado en grupos Odoo"""
        user_groups = self.groups_id
        return self.env['superset.dashboard'].search([
            '|', 
            ('allowed_users', 'in', self.id),
            ('allowed_groups', 'in', user_groups.ids)
        ])
```

## 📊 **Configuración de Producción**

### **Seguridad Reforzada:**
```python
# superset_config_docker.py para PRODUCCIÓN

# ⚠️ CRÍTICO: Activar CSRF con excepciones específicas
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = [
    'superset.views.core.dashboard_embedded',
    'superset.security.api.guest_token'
]

# ⚠️ CRÍTICO: Talisman configurado para dominios específicos
TALISMAN_ENABLED = True
TALISMAN_CONFIG = {
    "frame_options": "ALLOWFROM",
    "frame_options_allow_from": [
        "https://tu-odoo-produccion.com/",
        "https://tu-dominio-corporativo.com/",
    ],
    "content_security_policy": False,
    "strict_transport_security": True,
}

# ⚠️ CRÍTICO: Secret JWT super seguro (mínimo 64 caracteres)
GUEST_TOKEN_JWT_SECRET = "clave-super-ultra-segura-produccion-64-caracteres-minimo-cambiar-obligatorio"

# ⚠️ CRÍTICO: CORS restrictivo solo para dominios de producción
CORS_OPTIONS = {
    "origins": [
        "https://tu-odoo-produccion.com/",
        "https://tu-dominio-corporativo.com/",
        # NO incluir localhost ni IPs en producción
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
    "supports_credentials": True
}
```

## 📋 **Archivos Esenciales del Proyecto**

### **✅ Archivos que SÍ sirven (mantener):**
- `README_INTEGRATION.md` - Esta documentación completa
- `setup_embedding_auto.sh` - Script automático para configurar embedding
- `superset/docker-compose-non-dev.yml` - Configuración Docker corregida
- `superset/docker/pythonpath_dev/superset_config_docker.py` - Configuración core
- `superset-test-app/` - Aplicación Next.js de referencia completa
- `iframe-example.html` - Ejemplo HTML funcional

### **❌ Archivos que NO sirven (eliminar):**
- `create_test_dashboard.py` - Script fallido para crear dashboards
- `serve_example.py` - Servidor simple (usar `python3 -m http.server` en su lugar)
- `superset/setup_embedding.sh` - Script obsoleto menos robusto

## 🎯 **Próximos Pasos Inmediatos**

### **Para Desarrollo (Inmediato):**
1. ✅ **Crear más dashboards** en Superset y configurar embedding
2. ✅ **Probar con diferentes usuarios** y permisos
3. ✅ **Documentar UUIDs** de todos los dashboards disponibles

### **Para Producción (Medio Plazo):**
1. 🔐 **Configurar HTTPS** en Superset
2. 🔐 **Implementar autenticación robusta** Odoo ↔ Superset
3. 🔐 **Sistema de permisos granular** por usuario/grupo
4. 🔐 **Auditoria y logging** de accesos a dashboards

## 🏆 **Conclusión y Estado Final**

**✅ OBJETIVO COMPLETADO:** Integración funcional al 100%

**🔑 Componentes Clave Funcionando:**
- ✅ Configuración CORS con URLs terminadas en `/` 
- ✅ Guest tokens generándose automáticamente
- ✅ SDK oficial embebiendo dashboards correctamente
- ✅ Aplicaciones de prueba funcionando perfectamente
- ✅ Arquitectura escalable lista para Odoo

**🚀 Listo para:** Implementación real en Odoo usando patrones probados

---

**Fecha:** 17 de Agosto, 2025  
**Estado:** ✅ Completado exitosamente  
**Aplicaciones:** 2/2 funcionando al 100%  
**Documentación:** Completa y actualizada  
**Próximo milestone:** Módulo Odoo funcional