# 📊 Apache Superset Embedding - Integración HTML/JavaScript

## 📄 Descripción

Proyecto para integrar **Apache Superset** en aplicaciones web usando iframes con autenticación transparente mediante guest tokens. 

## ✅ Estado Actual

- **✅ 100% Funcional** - Ejemplo HTML funcionando
- **✅ Problema CORS resuelto** - URLs con barra final obligatoria
- **✅ SDK oficial** - Integración con `@superset-ui/embedded-sdk`
- **✅ Documentación clara** - Guías simplificadas

## 🚀 Demo Rápida

```bash
# 1. Iniciar Superset
cd superset
docker-compose -f docker-compose-non-dev.yml up -d

# 2. Configurar embedding
./setup_embedding.sh

# 3. Abrir ejemplo
python3 -m http.server 8080
# → http://localhost:8080/iframe-example.html
```

## 📁 Estructura del Proyecto

```
apache-superset-embedding/
├── README.md                                    # 📖 Esta guía principal
├── README_INTEGRATION.md                        # 📋 Documentación técnica
├── iframe-example.html                          # 🚀 Ejemplo HTML funcionando
├── setup_embedding.sh                           # 🔧 Script configuración automática
└── superset/                                    # 📁 Repositorio Apache Superset
    ├── docker-compose-non-dev.yml               
    └── docker/pythonpath_dev/
        └── superset_config_docker.py            # ⚡ Configuración embedding
```

## ⚠️ Problema CORS Crítico - RESUELTO

### **El Problema:**
```javascript
// ❌ ERROR: CORS blocked from 'http://localhost:8080'
Access to fetch at 'http://192.168.1.137:8088/health' has been blocked by CORS policy
```

### **La Solución:**
**URLs DEBEN terminar en barra final `/`**

```python
# ❌ INCORRECTO (causa errores CORS):
CORS_OPTIONS = {
    "origins": ["http://localhost:8080"]  # Sin barra final
}

# ✅ CORRECTO (funciona perfectamente):
CORS_OPTIONS = {
    "origins": ["http://localhost:8080/"]  # CON barra final
}
```

**Configuración completa en `superset/docker/pythonpath_dev/superset_config_docker.py`:**

```python
CORS_OPTIONS = {
    "origins": [
        # ⚠️ IMPORTANTE: URLs CON barra final "/"
        "http://localhost:8000/", "http://localhost:8080/", "http://localhost:9000/",
        "http://127.0.0.1:8000/", "http://127.0.0.1:8080/", "http://127.0.0.1:9000/",
        "http://192.168.1.137:8080/", "http://192.168.1.137:9000/",
        
        # Odoo ports
        "http://localhost:8069/", "http://127.0.0.1:8069/", "http://192.168.1.137:8069/",
        
        # Para desarrollo local
        "null",
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "supports_credentials": True
}
```

## 🔧 Configuración Crítica

### 1. Feature Flags (Obligatorio)
```python
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,  # ⚠️ CRÍTICO - Sin esto no funciona
}
```

### 2. Guest Tokens
```python
GUEST_TOKEN_JWT_SECRET = "mi-clave-superset-local-jwt-secret-minimo-32-caracteres-2024"
GUEST_TOKEN_JWT_EXP_SECONDS = 300  # 5 minutos
```

### 3. Seguridad Development
```python
WTF_CSRF_ENABLED = False  # ⚠️ Solo para development
TALISMAN_ENABLED = False  # ⚠️ Solo para development
ENABLE_IFRAME_EMBEDDING = True
```

## 🛠️ Instalación

### Prerequisitos
- Docker y Docker Compose
- `jq`, `curl`, `git`

### Instalación Completa

```bash
# 1. Clonar repositorio oficial Superset
git clone https://github.com/apache/superset.git
cd superset

# 2. Aplicar configuración embedding (copiar desde este proyecto)
cp ../superset_config_docker.py docker/pythonpath_dev/
cp ../docker-compose-non-dev.yml .

# 3. Iniciar Superset
docker-compose -f docker-compose-non-dev.yml up -d

# 4. Esperar a que esté listo
timeout 300 bash -c 'until curl -f http://192.168.1.137:8088/health; do sleep 5; done'

# 5. Configurar embedding
cd ..
./setup_embedding.sh

# 6. Probar ejemplo
python3 -m http.server 8080
# Abrir: http://localhost:8080/iframe-example.html
```

## 🎯 Implementación JavaScript

### Flujo Básico:
```javascript
// 1. Obtener access token admin
const response = await fetch('http://192.168.1.137:8088/api/v1/security/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'admin',
        password: 'admin',
        provider: 'db'
    })
});
const accessToken = (await response.json()).access_token;

// 2. Generar guest token
const guestResponse = await fetch('http://192.168.1.137:8088/api/v1/security/guest_token/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        user: { username: 'guest_user', first_name: 'Guest', last_name: 'User' },
        resources: [{ type: 'dashboard', id: 'dashboard-uuid' }],
        rls: []
    })
});
const guestToken = (await guestResponse.json()).token;

// 3. Embeber con SDK oficial
await supersetEmbeddedSdk.embedDashboard({
    id: "dashboard-uuid",
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

## ⚠️ Problemas Comunes

### Error CORS:
```
Access to fetch blocked by CORS policy: No 'Access-Control-Allow-Origin' header
```
**Solución:** Verificar URLs en CORS_OPTIONS terminen en `/`

### Dashboard no aparece:
1. Verificar embedding habilitado en dashboard
2. Usar UUID correcto (no ID numérico)
3. Verificar guest token válido

### Cambios no aplican:
```bash
cd superset
docker-compose -f docker-compose-non-dev.yml restart
```

## 📚 Documentación

| Archivo | Descripción |
|---------|-------------|
| `README_INTEGRATION.md` | 📋 Guía técnica completa |
| `iframe-example.html` | 🚀 Ejemplo HTML funcional |
| `setup_embedding.sh` | 🔧 Script configuración automática |

## 🔐 Producción

Para producción, activar seguridad en `superset_config_docker.py`:

```python
# Activar CSRF con excepciones
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = [
    'superset.views.core.dashboard_embedded',
    'superset.security.api.guest_token'
]

# CORS restrictivo
CORS_OPTIONS = {
    "origins": ["https://tu-dominio-produccion.com/"],
}

# Secret ultra seguro (64+ caracteres)
GUEST_TOKEN_JWT_SECRET = "clave-ultra-segura-64-caracteres-minimo"
```

## 🏆 Estado

**✅ FUNCIONANDO COMPLETAMENTE**

- ✅ Problema CORS resuelto
- ✅ SDK oficial integrado  
- ✅ Ejemplo HTML operativo
- ✅ Documentación clara
- ✅ Listo para Odoo

---

**Fecha:** 17 de Agosto, 2025  
**Estado:** ✅ Completado y documentado  
**Ejemplo:** `iframe-example.html` disponible y funcionando