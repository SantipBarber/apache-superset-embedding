# 📊 Integración Apache Superset con HTML/JavaScript

## 🎯 Objetivo
Integrar Apache Superset dentro de aplicaciones web usando iframes y el SDK oficial, permitiendo que usuarios visualicen dashboards sin login adicional.

## ✅ Estado Actual - FUNCIONANDO

### Aplicaciones Disponibles:
- **Ejemplo HTML**: `iframe-example.html` ✅
- **Superset**: http://192.168.1.137:8088 ✅

## 🔧 Configuración Crítica

### 1. Archivo: `superset/docker/pythonpath_dev/superset_config_docker.py`

**⚠️ PROBLEMA CRÍTICO CORS RESUELTO:**
- **URLs DEBEN terminar en barra final `/`**
- **Ejemplo correcto:** `"http://localhost:8080/"` 
- **Ejemplo incorrecto:** `"http://localhost:8080"` (causa errores CORS)

```python
# Feature flags - DEBE incluir EMBEDDED_SUPERSET
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,  # ⚠️ CRÍTICO
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# Guest token configuration
GUEST_TOKEN_JWT_SECRET = "mi-clave-superset-local-jwt-secret-minimo-32-caracteres-2024"
GUEST_TOKEN_JWT_EXP_SECONDS = 300  # 5 minutos

# CORS - CRÍTICO: URLs con barra final
ENABLE_CORS = True
CORS_OPTIONS = {
    "origins": [
        # ⚠️ IMPORTANTE: URLs CON barra final "/"
        "http://localhost:8000/", "http://localhost:8080/", "http://localhost:9000/",
        "http://127.0.0.1:8000/", "http://127.0.0.1:8080/", "http://127.0.0.1:9000/",
        "http://192.168.1.137:8080/", "http://192.168.1.137:9000/",
        
        # Odoo ports
        "http://localhost:8069/", "http://127.0.0.1:8069/", "http://192.168.1.137:8069/",
        
        # Para file:// local
        "null",
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "supports_credentials": True
}

# Seguridad para development
WTF_CSRF_ENABLED = False  # ⚠️ Solo para development
TALISMAN_ENABLED = False  # ⚠️ Solo para development
ENABLE_IFRAME_EMBEDDING = True
```

### 2. Archivo: `superset/docker-compose-non-dev.yml`

```yaml
x-superset-volumes:
  &superset-volumes
  - ./docker:/app/docker
  - superset_home:/app/superset_home
  - ./docker/pythonpath_dev/superset_config_docker.py:/app/pythonpath_dev/superset_config_docker.py
```

## 🚀 Pasos para Usar

### 1. Iniciar Superset
```bash
cd superset
docker-compose -f docker-compose-non-dev.yml up -d

# Verificar funcionamiento
curl http://192.168.1.137:8088/health
```

### 2. Configurar Dashboard para Embedding
```bash
# Ejecutar script automático
./setup_embedding.sh
```

### 3. Probar Integración HTML
```bash
# Iniciar servidor web simple
python3 -m http.server 8080

# Abrir navegador en:
# http://localhost:8080/iframe-example.html
```

## 🔑 Implementación Técnica

### Flujo de Autenticación:
```
[Usuario] → [App Web] → [Obtener Access Token] → [Generar Guest Token] → [SDK Embedding] → [Dashboard]
```

### Código JavaScript Básico:
```javascript
// 1. Obtener access token de admin
const response = await fetch('http://192.168.1.137:8088/api/v1/security/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'admin',
        password: 'admin', 
        provider: 'db'
    })
});
const data = await response.json();
const accessToken = data.access_token;

// 2. Generar guest token para dashboard
const guestResponse = await fetch('http://192.168.1.137:8088/api/v1/security/guest_token/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        user: {
            username: 'guest_user',
            first_name: 'Guest',
            last_name: 'User'
        },
        resources: [{
            type: 'dashboard',
            id: 'dashboard-uuid-aqui'
        }],
        rls: []
    })
});
const guestToken = await guestResponse.json().token;

// 3. Embeber dashboard con SDK
await supersetEmbeddedSdk.embedDashboard({
    id: "dashboard-uuid-aqui",
    supersetDomain: "http://192.168.1.137:8088",
    mountPoint: document.getElementById('superset-container'),
    fetchGuestToken: () => guestToken,
    dashboardUiConfig: {
        hideTitle: false,
        hideTab: false,
        hideChartControls: false,
    }
});

// 4. Ajustar tamaño iframe
setTimeout(() => {
    const iframe = container.querySelector('iframe');
    if (iframe) {
        iframe.style.width = '100%';
        iframe.style.height = '600px';
        iframe.style.border = 'none';
    }
}, 1000);
```

## ⚠️ Problemas Comunes y Soluciones

### Error CORS:
```
Access to fetch at 'http://192.168.1.137:8088/health' from origin 'http://localhost:8080' 
has been blocked by CORS policy
```

**Solución:** Verificar que URLs en CORS_OPTIONS terminen en `/`:
- ✅ Correcto: `"http://localhost:8080/"`
- ❌ Incorrecto: `"http://localhost:8080"`

### Dashboard no aparece:
1. Verificar que el dashboard tenga embedding habilitado
2. Usar UUID correcto (no ID numérico)
3. Verificar guest token válido

### Reiniciar tras cambios de configuración:
```bash
cd superset
docker-compose -f docker-compose-non-dev.yml restart
```

## 📋 Archivos del Proyecto

### ✅ Archivos Útiles:
- `README.md` - Documentación principal
- `README_INTEGRATION.md` - Esta guía técnica
- `setup_embedding.sh` - Script configuración automática
- `iframe-example.html` - Ejemplo HTML funcional
- `superset/docker/pythonpath_dev/superset_config_docker.py` - Configuración core

### 🔜 Para Integración Odoo:
El mismo patrón funciona en Odoo:
1. Crear controlador que genere guest tokens
2. Usar SDK en templates Odoo
3. Configurar permisos por usuario/grupo

---

**Fecha:** 17 de Agosto, 2025  
**Estado:** ✅ Funcionando completamente  
**Ejemplo:** `iframe-example.html` disponible y operativo