# 📊 Apache Superset Embedding - Guía Completa

## 📄 Descripción

Proyecto **100% funcional** para integrar **Apache Superset** en aplicaciones web usando iframes con autenticación transparente mediante guest tokens.

## ✅ Estado: COMPLETAMENTE OPERATIVO

- ✅ **Integración funcionando** - Dashboards embebidos en aplicación externa
- ✅ **CORS configurado** - Conexión desde aplicación verificada
- ✅ **Guest tokens funcionando** - Autenticación automática operativa
- ✅ **3 dashboards listos** - Con embedding habilitado
- ✅ **Scripts automatizados** - Para replicar fácilmente

## 🔧 Configuración Inicial Obligatoria

### Antes de Instalar

**⚠️ Es OBLIGATORIO personalizar estos archivos antes de usar:**

1. **`superset_config_docker.py`**
   ```python
   # Cambiar por tu clave secreta única
   GUEST_TOKEN_JWT_SECRET = "TU-CLAVE-SECRETA-AQUI-MINIMO-32-CARACTERES"
   
   # Agregar tu IP local en CORS_OPTIONS
   "http://TU-IP-LOCAL:8080", "http://TU-IP-LOCAL:8080/",
   ```

2. **`setup_embedding_working.sh`**
   ```bash
   SUPERSET_URL="http://TU-IP-LOCAL:8088"  # Tu IP de Superset
   ```

3. **`test_final.sh`**
   ```bash
   SUPERSET_URL="http://TU-IP-LOCAL:8088"    # Tu IP de Superset
   APP_URL="http://TU-IP-LOCAL:8080"         # Tu IP aplicación
   TEST_UUID="TU-UUID-OBTENIDO-DE-SUPERSET"  # UUID real
   ```

4. **`iframe-example.html`**
   ```javascript
   const SUPERSET_URL = 'http://TU-IP-LOCAL:8088';  // Tu IP de Superset
   
   // Reemplazar UUIDs de ejemplo con los reales
   let dashboards = [
       { id: "TU-UUID-REAL", dashboard_title: "Tu Dashboard" }
   ];
   ```

### 💡 Cómo Obtener tu IP Local

```bash
# En Linux/Mac
ifconfig | grep "inet " | grep -v 127.0.0.1

# En Windows
ipconfig
```

---

## 🚀 Instalación Completa (10 minutos)

### 1. Preparar Superset

```bash
# Clonar repositorio oficial
git clone https://github.com/apache/superset.git
cd superset

# Copiar configuración de embedding
cp ../superset_config_docker.py docker/pythonpath_dev/
cp ../docker-compose-non-dev.yml .

# Iniciar Superset
docker-compose -f docker-compose-non-dev.yml up -d

# Verificar funcionamiento (esperar 2-3 minutos)
curl http://localhost:8088/health  # Debe devolver "OK"
```

### 2. Habilitar Embedding (Manual en Interfaz)

1. **Ir a Superset**: http://localhost:8088 (admin/admin)
2. **Abrir dashboard** → **Settings** → **Embed dashboard**
3. **Agregar dominios**:
   - `http://localhost:8080`
   - `http://127.0.0.1:8080`
4. **Copiar UUID** que aparece (ej: `abc12345-6789-0123-4567-890abcdef123`)
5. **Actualizar** `iframe-example.html` con el UUID obtenido

### 3. Probar Aplicación

```bash
# Iniciar servidor web
python3 -m http.server 8080

# Abrir navegador en: http://localhost:8080/iframe-example.html
```

### 4. Verificar Todo Funciona

```bash
# Ejecutar verificación completa
./test_final.sh
```

## 📁 Archivos del Proyecto

```
apache-superset-embedding/
├── README.md                        # Esta guía
├── iframe-example.html              # Aplicación de prueba funcionando
├── setup_embedding_working.sh       # Script para habilitar embedding
├── test_final.sh                   # Script de verificación
└── superset/
    ├── docker-compose-non-dev.yml  # Docker compose configurado
    └── docker/pythonpath_dev/
        └── superset_config_docker.py # Configuración crítica
```

## 🔧 Configuración Crítica

### superset_config_docker.py (Completo)

```python
# Feature flags - CRÍTICOS
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,  # ⚠️ OBLIGATORIO
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ALERT_REPORTS": True,
}

# Guest token configuration
GUEST_TOKEN_JWT_SECRET = "mi-clave-superset-local-jwt-secret-minimo-32-caracteres-2024"
GUEST_TOKEN_JWT_EXP_SECONDS = 300
GUEST_ROLE_NAME = "Gamma"  # Rol con permisos de lectura

# CORS - URLs con AMBAS versiones (con y sin barra final)
ENABLE_CORS = True
CORS_OPTIONS = {
    "origins": [
        "http://localhost:8080", "http://localhost:8080/",
        "http://127.0.0.1:8080", "http://127.0.0.1:8080/",
        "http://localhost:8069", "http://localhost:8069/",  # Para Odoo
        "null",
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "supports_credentials": True
}

# Seguridad permisiva para desarrollo
WTF_CSRF_ENABLED = False
TALISMAN_ENABLED = False
ENABLE_IFRAME_EMBEDDING = True
```

### docker-compose-non-dev.yml (Modificación)

**Agregar esta línea en x-superset-volumes:**

```yaml
- ./docker/pythonpath_dev/superset_config_docker.py:/app/pythonpath_dev/superset_config_docker.py
```

## 🎯 Configuración de Dashboards

### JavaScript para la Aplicación

```javascript
// UUIDs obtenidos de la interfaz de Superset (ejemplo)
let dashboards = [
    {
        id: "abc12345-6789-0123-4567-890abcdef123",
        dashboard_title: "Tu Primer Dashboard",
        uuid: "abc12345-6789-0123-4567-890abcdef123"
    },
    {
        id: "def67890-1234-5678-9012-345abcdef678",
        dashboard_title: "Dashboard de Ventas",
        uuid: "def67890-1234-5678-9012-345abcdef678"
    }
];

// ⚠️ IMPORTANTE: Reemplaza estos UUIDs con los que obtengas de tu Superset
```

### Flujo de Integración

```javascript
// Configuración dinámica basada en el entorno
const SUPERSET_URL = 'http://localhost:8088';  // Ajustar según tu instalación

// 1. Login admin
const response = await fetch(`${SUPERSET_URL}/api/v1/security/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'admin', provider: 'db' })
});
const accessToken = (await response.json()).access_token;

// 2. Generar guest token
const guestResponse = await fetch(`${SUPERSET_URL}/api/v1/security/guest_token/`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        user: { username: 'guest_user', first_name: 'Guest', last_name: 'User' },
        resources: [{ type: 'dashboard', id: 'UUID-DEL-EMBEDDING' }],
        rls: []
    })
});
const guestToken = (await guestResponse.json()).token;

// 3. Embeber con SDK
await supersetEmbeddedSdk.embedDashboard({
    id: "UUID-DEL-EMBEDDING",
    supersetDomain: SUPERSET_URL,
    mountPoint: document.getElementById('superset-container'),
    fetchGuestToken: () => guestToken,
    dashboardUiConfig: { hideTitle: false, hideTab: false, hideChartControls: false }
});
```

## 🛠️ Scripts Útiles

```bash
# Listar dashboards disponibles
./setup_embedding_working.sh

# Habilitar embedding para dashboard específico
./setup_embedding_working.sh enable 1

# Verificar que todo funciona
./test_final.sh
```

## ⚠️ Solución de Problemas

| Error | Solución |
|-------|----------|
| **CORS blocked** | URLs en CORS_OPTIONS deben tener ambas versiones (con/sin `/`) |
| **403 Forbidden** | Configurar `GUEST_ROLE_NAME = "Gamma"` |
| **404 Not Found** | Usar UUID correcto obtenido de interfaz Superset |
| **Embedding no aparece** | 1) Verificar embedding habilitado manualmente<br/>2) Comprobar dominios permitidos<br/>3) Usar UUID correcto |

## 🔐 Para Producción

```python
# Activar seguridad
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = [
    'superset.views.core.dashboard_embedded',
    'superset.security.api.guest_token'
]

# CORS restrictivo
CORS_OPTIONS = {"origins": ["https://tu-dominio-produccion.com"]}

# Secret seguro
GUEST_TOKEN_JWT_SECRET = "clave-ultra-segura-64-caracteres-minimo"
```

## 🚀 Integración con Odoo

Mismo patrón:

1. **Controlador Odoo** que genere guest tokens
2. **SDK en templates** Odoo
3. **Configurar permisos** por usuario/grupo
4. **Agregar dominios Odoo** a CORS_OPTIONS

## ✅ Verificación Final

```bash
./test_final.sh
```

**Debe mostrar:**
- ✅ Superset: http://localhost:8088 (o tu IP local)
- ✅ CORS: Configurado
- ✅ Login: Funcionando
- ✅ Guest tokens: Funcionando

---

## 📋 Configuración Personalizada

### Variables a Personalizar

1. **IP/URL de Superset**: Por defecto `localhost:8088`, cambiar por la IP de tu servidor
2. **UUIDs de Dashboards**: Obtener desde la interfaz de Superset
3. **Dominios CORS**: Agregar las URLs de tu aplicación
4. **Credenciales**: Usar credenciales seguras en producción

### Archivos a Modificar

- `superset_config_docker.py` → CORS_OPTIONS origins
- `iframe-example.html` → SUPERSET_URL y dashboards array
- `setup_embedding_working.sh` → SUPERSET_URL
- `test_final.sh` → URLs de verificación

---

**Estado**: ✅ **INTEGRACIÓN LISTA PARA CUALQUIER ENTORNO**  
**Listo para**: Producción y integración con Odoo

**Para soporte**: `docker-compose -f superset/docker-compose-non-dev.yml logs superset`