# Eticco Superset Integration

Módulo de Odoo para la integración con Apache Superset. Permite visualizar dashboards embebidos con gestión automática de tokens y configuración centralizada.

## Arquitectura

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

## Configuración

1. **Settings → Superset Integration**:
   - URL de Superset
   - Usuario/contraseña admin
   - Timeout (30s recomendado)

2. **Probar conexión** y crear menú de Analytics

## Testing

```bash
# Tests completos
./run_odoo_tests.sh

# Tests de errores específicos
python test_production_error_scenarios.py
```

## Estructura de Código

**`superset_utils.py`**: Utilidades centralizadas
- Configuración, autenticación y tokens
- Cache inteligente y manejo de errores
- Llamadas optimizadas al servidor

**`superset_analytics_hub.py`**: Hub principal
- Selección y embedding de dashboards
- Interfaz de usuario

**`res_config_settings.py`**: Configuración
- Settings de Odoo y validaciones
- Pruebas de conexión y creación de menús

## Seguridad

- Tokens temporales con expiración automática
- Validación robusta de entradas
- Credenciales seguras en `ir.config_parameter`
- Cache limitado con expiración

## Troubleshooting

**Errores comunes**:
- Conexión: Verificar URL y conectividad
- Autenticación: Comprobar credenciales admin
- Timeout: Aumentar timeout en configuración
- Dashboard no encontrado: Verificar permisos y embedding habilitado

**Debug**: Settings → "Limpiar Cache de Superset" o revisar logs de Odoo

## API Principal

**`superset.utils`**:
- `get_superset_config()` - Configuración
- `get_access_token()` - Token de acceso
- `test_superset_connection()` - Probar conexión
- `clear_token_cache()` - Limpiar cache

**`superset.analytics.hub`**:
- `get_dashboard_data_for_js()` - Datos para frontend
- `refresh_dashboard_options()` - Refrescar opciones

**`res.config.settings`**:
- `create_dashboard_menu()` - Crear menú de dashboards