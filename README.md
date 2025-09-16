# Integración de Apache Superset Embedding

Una colección completa de herramientas y ejemplos para incrustar dashboards de Apache Superset en aplicaciones externas usando el SDK oficial de embedding.

## Descripción General

Este repositorio proporciona soluciones listas para producción para integrar dashboards de Apache Superset en tus aplicaciones mediante iframe embedding con autenticación automática y descubrimiento dinámico de dashboards.

## Estado: COMPLETAMENTE OPERATIVO

- ✅ **Integración funcionando** - Dashboards embebidos en aplicación externa
- ✅ **CORS configurado** - Conexión desde aplicación verificada  
- ✅ **Guest tokens funcionando** - Autenticación automática operativa
- ✅ **Scripts automatizados** - Para replicar fácilmente
- ✅ **Detección dinámica** - Descubrimiento automático de dashboards

## Configuración Inicial Requerida

### Configuración de Superset

**⚠️ Es necesario configurar estos elementos antes de usar:**

1. **`superset_config_docker.py`** (si usas Docker) o **`superset_config.py`** (instalación manual)
   ```python
   # Cambiar por tu clave secreta única (mínimo 32 caracteres)
   GUEST_TOKEN_JWT_SECRET = "tu-clave-secreta-aqui-minimo-32-caracteres"
   
   # Configurar CORS para permitir conexiones desde tu aplicación
   "origins": [
       "http://localhost:8080", "http://localhost:8080/",
       "http://127.0.0.1:8080", "http://127.0.0.1:8080/",
       # Se pueden agregar más dominios según necesidad
   ]
   ```

2. **`setup_embedding_working.sh`** (opcional, para automatización)
   ```bash
   # Ajustar según tu instalación de Superset
   SUPERSET_URL="http://localhost:8088"
   ```

### Aplicación Principal

**`generic_superset_embedder.html`** - No requiere configuración previa:
- Configuración dinámica de URL desde la interfaz
- Detección automática de entorno
- Configuración de credenciales en tiempo real

## Instalación Completa (15 minutos)

### Opción 1: Instalación con Docker (Recomendado)

```bash
# 1. Clonar repositorio oficial de Superset
git clone https://github.com/apache/superset.git
cd superset

# 2. Copiar configuración de embedding (si tienes los archivos)
cp ../superset_config_docker.py docker/pythonpath_dev/
cp ../docker-compose-non-dev.yml .

# 3. Iniciar Superset
docker-compose -f docker-compose-non-dev.yml up -d

# 4. Verificar funcionamiento (esperar 2-3 minutos)
curl http://localhost:8088/health  # Debe devolver "OK"
```

### Opción 2: Instalación Manual

```bash
# 1. Instalar Superset
pip install apache-superset

# 2. Inicializar base de datos
superset db upgrade

# 3. Crear usuario admin
superset fab create-admin

# 4. Cargar ejemplos (opcional)
superset load_examples

# 5. Inicializar Superset
superset init

# 6. Configurar archivo de configuración
# Crear superset_config.py con la configuración necesaria

# 7. Iniciar servidor
superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger
```

### Configuración de Superset para Embedding

#### Archivo de configuración (superset_config.py)

```python
# Feature flags - CRÍTICOS
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,  # ⚠️ OBLIGATORIO
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# Guest token configuration
GUEST_TOKEN_JWT_SECRET = "tu-clave-secreta-aqui-minimo-32-caracteres"
GUEST_TOKEN_JWT_EXP_SECONDS = 300
GUEST_ROLE_NAME = "Gamma"  # Rol con permisos de lectura

# CORS - URLs con AMBAS versiones (con y sin barra final)
ENABLE_CORS = True
CORS_OPTIONS = {
    "origins": [
        "http://localhost:8080", "http://localhost:8080/",
        "http://127.0.0.1:8080", "http://127.0.0.1:8080/",
        # Agregar tu IP local aquí
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "supports_credentials": True
}

# Seguridad para desarrollo
WTF_CSRF_ENABLED = False
TALISMAN_ENABLED = False
ENABLE_IFRAME_EMBEDDING = True
```

## Habilitar Embedding en Dashboards

### Método 1: Interfaz de Superset (Manual)

1. **Ir a Superset**: http://localhost:8088 (admin/admin)
2. **Abrir dashboard** → **Settings** → **Embed dashboard**
3. **Agregar dominios permitidos**:
   - `http://localhost:8080`
   - `http://127.0.0.1:8080`
   - Tu IP local con puerto 8080
4. **Guardar configuración**
5. **Copiar UUID de embedding** que aparece

### Método 2: Script Automatizado

```bash
# Configurar script con tu URL de Superset
vim setup_embedding_working.sh

# Listar dashboards disponibles
./setup_embedding_working.sh

# Habilitar embedding para dashboard específico
./setup_embedding_working.sh enable <dashboard_id>
```

## Uso de las Aplicaciones

### Aplicación Principal (Recomendado)

**`generic_superset_embedder.html`** - Aplicación completa con configuración dinámica

```bash
# Iniciar servidor web
python3 -m http.server 8080

# Abrir: http://localhost:8080/generic_superset_embedder.html
```

**Funcionalidades:**
- Configuración dinámica de URL de Superset desde la interfaz
- Detección automática de entorno (desarrollo/producción)
- Descubrimiento automático de dashboards con embedding habilitado
- Manejo avanzado de errores y debugging
- Interfaz moderna y responsive
- No requiere configuración previa de URLs o UUIDs

**Flujo de uso:**
1. Abrir la aplicación en el navegador
2. Introducir URL de Superset (ej: `http://localhost:8088`)
3. Introducir credenciales de administrador
4. Hacer clic en "Conectar y Cargar Dashboards"
5. Seleccionar dashboard de la lista
6. Hacer clic en "Cargar Dashboard"

### Ejemplos y Pruebas de Concepto

**`iframe-example.html`** - Ejemplo básico para aprendizaje
- Configuración hardcodeada en el código
- Útil para entender el flujo básico
- Requiere modificar URLs y UUIDs manualmente

## Estructura del Repositorio

```
apache-superset-embedding/
├── README.md                          # Esta guía
├── generic_superset_embedder.html     # Aplicación principal
├── iframe-example.html                # Ejemplo básico
├── setup_embedding_working.sh         # Script de configuración
└── test_final.sh                      # Script de verificación
```

### Archivos que se crean durante la instalación:

Después de clonar el repositorio oficial de Superset:

```
superset/
├── docker/
│   └── pythonpath_dev/
│       └── superset_config_docker.py  # Configuración para Docker (copiar/crear)
└── docker-compose-non-dev.yml         # Docker compose modificado (copiar/crear)
```

## Archivos Principales

| Archivo | Descripción | Uso Recomendado |
|---------|-------------|-----------------|
| `generic_superset_embedder.html` | **Aplicación principal** - Configuración dinámica completa | Producción y desarrollo diario |
| `iframe-example.html` | Ejemplo básico para aprendizaje | Prueba de concepto y comprensión del flujo |

## Scripts de Utilidad

| Script | Función | Comando |
|--------|---------|---------|
| `setup_embedding_working.sh` | Configurar embedding automáticamente | `./setup_embedding_working.sh [enable <id>]` |
| `test_final.sh` | Verificar integración completa | `./test_final.sh` |

## Verificación del Setup

```bash
# Ejecutar verificación completa
./test_final.sh
```

**Debe mostrar:**
- ✅ Superset funcionando
- ✅ CORS configurado  
- ✅ Login funcionando
- ✅ Guest tokens funcionando

## Resolución de Problemas Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| **CORS blocked** | URLs no agregadas a CORS_OPTIONS | Agregar URLs con y sin `/` final |
| **403 Forbidden** | Rol de guest mal configurado | Configurar `GUEST_ROLE_NAME = "Gamma"` |
| **404 Not Found** | UUID incorrecto | Usar UUID de embedding desde interfaz |
| **Dashboard no carga** | Embedding no habilitado | Habilitar desde Settings → Embed dashboard |
| **Connection refused** | Superset no iniciado | Verificar `curl http://localhost:8088/health` |

## Características Avanzadas

### Detección Automática de Entorno

La aplicación principal detecta automáticamente:
- Entorno de desarrollo vs producción
- URLs apropiadas según el contexto
- Dashboards disponibles con embedding

### Debug y Diagnósticos

- Panel de debug integrado
- Logs detallados en consola
- Información de configuración exportable
- Verificación de conectividad automática

### Configuración Dinámica

- Sin necesidad de hardcodear UUIDs
- Configuración de credenciales desde interfaz
- Detección automática de dashboards habilitados
- Validación de configuración en tiempo real

## Configuración para Producción

```python
# Seguridad activada
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = [
    'superset.views.core.dashboard_embedded',
    'superset.security.api.guest_token'
]

# CORS restrictivo
CORS_OPTIONS = {
    "origins": ["https://tu-dominio-produccion.com"]
}

# Secret seguro (mínimo 32 caracteres)
GUEST_TOKEN_JWT_SECRET = "clave-ultra-segura-64-caracteres-minimo"
```

## Integración con Otras Aplicaciones

### Con Odoo

1. Crear controlador Odoo que genere guest tokens
2. Usar SDK en templates QWeb
3. Configurar permisos por usuario/grupo
4. Agregar dominios de Odoo a CORS_OPTIONS

### Con React/Angular/Vue

```javascript
import { embedDashboard } from "@superset-ui/embedded-sdk";

embedDashboard({
    id: "embedding-uuid",
    supersetDomain: "http://localhost:8088", // Configurar según tu entorno
    mountPoint: document.getElementById("dashboard-container"),
    fetchGuestToken: () => obtenerGuestTokenDesdeBackend(),
    dashboardUiConfig: {
        hideTitle: false,
        hideTab: false,
        hideChartControls: false
    }
});
```

**Nota**: En `generic_superset_embedder.html` esto se maneja automáticamente tomando la URL del formulario.

## API Reference

### Endpoints Utilizados

- `GET /health` - Verificación de estado
- `POST /api/v1/security/login` - Autenticación admin
- `GET /api/v1/dashboard/` - Listar dashboards
- `GET /api/v1/dashboard/{id}/embedded` - Obtener UUID de embedding
- `POST /api/v1/security/guest_token/` - Generar guest token

### Flujo de Autenticación

1. **Login admin** → Obtener access token
2. **Verificar embedding** → Comprobar UUID de embedding disponible
3. **Generar guest token** → Usando embedding UUID
4. **Embeber dashboard** → Con guest token y embedding UUID

## Soporte de Navegadores

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Contribuciones

1. Fork del repositorio
2. Crear rama de feature
3. Realizar cambios
4. Probar con `test_final.sh`
5. Enviar pull request

## Recursos Adicionales

- [Apache Superset Documentation](https://superset.apache.org/)
- [Embedded SDK Documentation](https://github.com/apache/superset/tree/master/superset-embedded-sdk)
- [Superset Community](https://superset.apache.org/community)

## Soporte

- [Issues](https://github.com/SantipBarber/apache-superset-embedding/issues) para bugs
- [Discussions](https://github.com/SantipBarber/apache-superset-embedding/discussions) para preguntas
- [Documentación oficial](https://superset.apache.org/docs/intro) para problemas de Superset

---

**Estado**: ✅ **INTEGRACIÓN LISTA PARA CUALQUIER ENTORNO**  
**Nota**: Proyecto no oficial de la comunidad. Para soporte oficial consultar [Apache Superset](https://github.com/apache/superset).