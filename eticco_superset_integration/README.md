# 📊 Eticco Superset Integration

Módulo de Odoo 17 para integrar dashboards de Apache Superset de forma nativa y segura.

## 🎯 Características Principales

✅ **Integración nativa** con Apache Superset  
✅ **Interface única** para selección y visualización  
✅ **Auto-detección** de dashboards con embedding habilitado  
✅ **Cache inteligente** para mejor performance  
✅ **Configuración centralizada** en Settings de Odoo  
✅ **Gestión automática** de tokens de acceso  
✅ **Menús dinámicos** configurables  
✅ **Tests completos** incluidos  
✅ **Manejo profesional de errores** con 8+ tipos de error específicos  
✅ **Mensajes contextuales** con emojis y acciones de recuperación  
✅ **Indicadores de carga** y estados visuales  
✅ **Lógica centralizada** en `superset_utils.py` para operaciones comunes  

## 🏗️ Arquitectura

```
eticco_superset_integration/
├── models/
│   ├── res_config_settings.py    # Configuración en Settings
│   ├── superset_analytics_hub.py # Hub principal de Analytics  
│   └── superset_utils.py         # Utilidades centralizadas
├── views/
│   ├── superset_config_views.xml # Vista de configuración
│   └── superset_analytics_hub_views.xml # Vista del hub
├── static/src/
│   ├── fields/                   # Componentes OWL
│   └── scss/                     # Estilos CSS
├── tests/                        # Tests completos
├── security/                     # Permisos y seguridad
└── data/                        # Datos iniciales
```

## 🚀 Instalación

### 1. Requisitos Previos

- **Odoo 17** instalado y funcionando
- **Apache Superset** configurado con embedding habilitado
- **PostgreSQL** (para Odoo)
- **Python 3.8+** con requests

### 2. Instalación del Módulo

```bash
# Copiar módulo al addons path
cp -r eticco_superset_integration /path/to/odoo/addons/

# Instalar en Odoo
odoo-bin -d tu_database -i eticco_superset_integration --stop-after-init

# O instalar desde la UI de Odoo
# Apps → Update Apps List → Buscar "Superset Integration" → Install
```

## ⚙️ Configuración

### 1. Configurar Superset

Acceder a **Settings → Superset Integration**:

- **URL de Superset**: `http://tu-servidor-superset:8088`
- **Usuario**: Usuario admin de Superset
- **Contraseña**: Contraseña del usuario admin
- **Timeout**: 30 segundos (recomendado)

### 2. Probar Conexión

1. Hacer clic en **"Probar Conexión"**
2. Verificar que aparezcan los dashboards encontrados
3. Usar **"Ver Dashboards"** para inspeccionar cuáles tienen embedding

### 3. Crear Menú

1. Seleccionar **"Menú Padre"** donde quieres el menú de Analytics
2. Personalizar **"Nombre del Menú"** (por defecto: "Analytics")
3. Hacer clic en **"Crear Menú de Dashboards"**

## 🎮 Uso

### Para Usuarios Finales

1. **Navegar al menú Analytics** creado
2. **Seleccionar dashboard** del dropdown
3. **Ver automáticamente** el dashboard embebido
4. **Cambiar entre dashboards** sin recargar página

### Flujo Simple
```
Settings → Configure → Analytics Menu → Select → View
     ↓         ↓           ↓           ↓        ↓
   1 click  1 click    1 click    1 click   Auto
```

## 🧪 Testing

El módulo incluye tests completos para garantizar calidad:

### Ejecutar Tests

**En Entorno Odoo Real** (requiere Odoo instalado):
```bash
cd eticco_superset_integration/

# Tests completos con Odoo
./run_odoo_tests.sh

# Test específico
./run_odoo_tests.sh test_superset_utils.py

# Con configuración personalizada
./run_odoo_tests.sh -d mi_test_db -a /path/to/addons

# Ver ayuda completa
./run_odoo_tests.sh --help
```

**Tests de Escenarios de Error** (sin requerer Odoo):
```bash
cd eticco_superset_integration/

# Simular escenarios de error en producción
python test_production_error_scenarios.py

# Con configuración personalizada
python test_production_error_scenarios.py http://localhost:8069 mi_db
```

Ver documentación completa en [`eticco_superset_integration/tests/README.md`](tests/README.md).

## 🔧 Desarrollo

### Estructura de Código

**`superset_utils.py`**: Lógica centralizada y utilidades comunes
- Configuración y validación centralizadas
- Autenticación y manejo de tokens
- Cache inteligente con expiración
- Sistema profesional de manejo de errores con 8+ tipos
- Llamadas optimizadas al servidor Superset
- Obtención y procesamiento de información de dashboards

**`superset_analytics_hub.py`**: Hub principal  
- Selección de dashboards
- Embedding y visualización
- Interfaz de usuario
- Estados y flujos

**`res_config_settings.py`**: Configuración
- Settings de Odoo
- Validaciones
- Pruebas de conexión
- Creación de menús

### Añadir Funcionalidades

1. **Extender utilidades**:
   ```python
   # En superset_utils.py
   @api.model
   def mi_nueva_utilidad(self):
       # Nueva funcionalidad
   ```

2. **Añadir campos al hub**:
   ```python
   # En superset_analytics_hub.py
   mi_campo = fields.Char('Mi Campo')
   ```

3. **Crear tests**:
   ```python
   # En tests/test_mi_funcionalidad.py
   def test_mi_nueva_feature(self):
       # Test de la nueva funcionalidad
   ```

## 🛡️ Seguridad

### Mejores Prácticas Implementadas

- **Tokens temporales**: Los guest tokens expiran automáticamente
- **Validación robusta**: Todas las entradas se validan
- **Manejo seguro** de credenciales en ir.config_parameter
- **Logging controlado**: No se loggean datos sensibles
- **Cache limitado**: Cache de tokens con expiración

### Configuración de Superset

Asegurar configuración segura en Superset:

```python
# En superset_config.py
ENABLE_EMBEDDED_SUPERSET = True
EMBEDDED_SUPERSET = {
    'ALLOWED_DOMAINS': ['tu-dominio-odoo.com'],
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_SAMESITE': 'None',
}
```

## 🐛 Troubleshooting y Manejo de Errores

### Sistema Profesional de Manejo de Errores

El módulo implementa manejo profesional de errores con **8+ tipos específicos**, mensajes contextuales con emojis y acciones de recuperación inteligentes:

| Tipo Error | Emoji | Mensaje Usuario | Acción Sugerida |
|------------|--------|-----------------|-----------------|
| `connection_error` | 🌐 | No se puede conectar al servidor | Verificar servidor |
| `timeout_error` | ⏰ | Conexión lenta | Reintentar más tarde |
| `auth_error` | 🔒 | Credenciales incorrectas | Ir a Ajustes |
| `permission_error` | 🔒 | Sin permisos suficientes | Contactar admin |
| `server_error` | ⚠️ | Error interno del servidor | Contactar admin |
| `dashboard_not_found` | 📊 | Dashboard no encontrado | Seleccionar otro |
| `embedding_disabled` | 📊 | Embedding deshabilitado | Contactar admin |
| `config_error` | ⚙️ | Configuración incompleta | Ir a Ajustes |

### Problemas Comunes

**🌐 "No se puede conectar al servidor"**
- Verificar que Superset esté online y accesible
- Comprobar URL de conexión en Settings → Superset Integration
- Verificar firewall/proxy/conectividad de red

**🔒 "Credenciales incorrectas"**
- Verificar usuario y contraseña en Settings
- Comprobar que el usuario existe en Superset
- Verificar que tiene permisos de administrador

**⏰ "Timeout de conexión"**
- Aumentar timeout en configuración (>30 segundos)
- Verificar latencia de red al servidor Superset
- Probar en horarios de menor carga

**📊 "Dashboard no encontrado"**
- Verificar que el dashboard existe en Superset
- Comprobar que está publicado
- Verificar permisos de acceso

**📊 "Embedding deshabilitado"**
- Habilitar embedding en la configuración del dashboard
- Verificar configuración de `ENABLE_EMBEDDED_SUPERSET = True`
- Comprobar UUIDs de embedding generados

### Debug Mode

Activar modo debug en Settings para logs detallados:
```python
# Logs aparecen en /var/log/odoo/odoo.log
SUPERSET DEBUG: Token obtenido exitosamente
SUPERSET DEBUG: Dashboard cargado: Sales Analytics
```

### Limpiar Cache

Si hay problemas de cache:
1. Settings → **"Limpiar Cache de Superset"**
2. O reiniciar Odoo
3. O desde Python: `self.env['superset.utils'].clear_token_cache()`

## 📚 API Reference

### Modelos Principales

#### `superset.utils`
```python
get_superset_config()              # Obtener configuración
validate_config(config)            # Validar configuración  
get_access_token(config)          # Obtener token de acceso
is_configured()                   # Verificar si está configurado
get_system_status(force_refresh)  # Estado del sistema con cache (5min)
test_superset_connection(config)  # Probar conexión robusta
clear_token_cache()               # Limpiar cache de tokens
```

#### `superset.analytics.hub`
```python
get_dashboard_data_for_js()       # Datos para JavaScript/OWL
refresh_dashboard_options()       # Refrescar opciones
force_refresh_configuration()     # Forzar recálculo
get_default_hub()                # Obtener hub por defecto
```

#### `res.config.settings`
```python
test_superset_connection()        # Probar conexión
open_superset_dashboards()       # Ver dashboards disponibles
create_dashboard_menu()          # Crear menú de dashboards
clear_superset_cache()           # Limpiar cache
```

## 📈 Performance

### Optimizaciones Implementadas

- **Cache de tokens**: 4 minutos de duración
- **Cache de estado del sistema**: 5 minutos de duración  
- **Lazy loading**: Campos computados solo cuando necesarios
- **Batch requests**: Múltiples dashboards en una llamada
- **Connection pooling**: Reutilización de conexiones HTTP

### Métricas Típicas

- **Primera carga**: ~500ms (incluye autenticación)
- **Cambio de dashboard**: ~250ms (usa cache)
- **Navegación repetida**: <100ms (cache completo)

## 🤝 Contribución

### Para Contribuir

1. **Fork** el repositorio
2. **Crear branch** para tu feature: `git checkout -b feature/mi-mejora`
3. **Escribir tests** para la nueva funcionalidad
4. **Probar** con `./run_odoo_tests.sh`
5. **Commit**: `git commit -m "feat: añadir mi mejora"`
6. **Push**: `git push origin feature/mi-mejora`
7. **Pull Request** con descripción detallada

### Estándares de Código

- **PEP 8** para Python
- **Docstrings** en todos los métodos públicos
- **Tests** para toda funcionalidad nueva
- **Logging** apropiado para debugging
- **Manejo de errores** robusto

## 📄 Licencia

Este módulo se distribuye bajo la licencia LGPL-3, compatible con Odoo.

## 📞 Soporte

- **Issues**: Crear issue en el repositorio
- **Documentación**: Ver `eticco_superset_integration/tests/README.md` para detalles técnicos
- **Tests**: Ejecutar `./run_odoo_tests.sh` (con Odoo) o `python test_production_error_scenarios.py` (standalone)

---

**Versión**: 1.0.0  
**Compatibilidad**: Odoo 17.0+  
**Mantenido por**: Equipo Eticco  
**Última actualización**: 2025-01-27