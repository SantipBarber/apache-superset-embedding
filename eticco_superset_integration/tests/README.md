# Tests del Módulo Superset Integration

Este directorio contiene los tests para el módulo `eticco_superset_integration`, diseñados para ejecutarse tanto en entornos de desarrollo como en pipelines de CI/CD.

> **📍 Ubicación**: Los scripts de tests están dentro del módulo para máxima portabilidad.

## 📋 Estructura de Tests

```
eticco_superset_integration/
├── tests/
│   ├── __init__.py                    # Inicialización del paquete
│   ├── test_superset_utils.py         # Tests para superset.utils  
│   ├── test_analytics_hub.py          # Tests para superset.analytics.hub
│   ├── test_configuration_flow.py     # Tests para flujo de configuración
│   ├── test_integration.py            # Tests de integración completa
│   └── README.md                      # Esta documentación
└── run_odoo_tests.sh                  # Script de tests con Odoo
```

## 🚀 Ejecución

```bash
cd eticco_superset_integration/
./run_odoo_tests.sh
```

## 🧪 Tests Incluidos

### 1. **test_superset_utils.py** (12 tests)
- ✅ Configuración y validación
- ✅ Autenticación y manejo de tokens
- ✅ Sistema de cache inteligente
- ✅ Manejo robusto de errores
- ✅ Estadísticas de dashboards

### 2. **test_analytics_hub.py** (18 tests)  
- ✅ Creación y gestión de registros
- ✅ Selección dinámica de dashboards
- ✅ Campos computados
- ✅ Carga automática de dashboards
- ✅ Integración JavaScript/OWL

### 3. **test_configuration_flow.py** (15 tests)
- ✅ Validación de configuración
- ✅ Pruebas de conexión con Superset
- ✅ Creación automática de menús
- ✅ Flujo Settings → Analytics
- ✅ Performance y cache

### 4. **test_integration.py** (10 tests)
- ✅ Flujos end-to-end completos
- ✅ Integración entre todos los componentes
- ✅ Casos de error complejos
- ✅ Workflows de usuario real
- ✅ Performance de navegación

## 📊 Cobertura

**Total: 55 tests** cubriendo:
- 🎯 **Funcionalidad**: 100% de métodos públicos
- 🎯 **Casos de error**: Todos los scenarios
- 🎯 **Integración**: Flujos completos
- 🎯 **Performance**: Cache y optimizaciones

## ⚙️ Configuración del Entorno

### Tests con Odoo Real

**Ventajas**: Test completo con ORM de Odoo, base de datos real, validación exhaustiva

```bash
# Requiere Odoo instalado
./run_odoo_tests.sh                    # Todos los tests
./run_odoo_tests.sh test_superset_utils.py  # Test específico
./run_odoo_tests.sh -d mi_test_db      # DB personalizada
./run_odoo_tests.sh --no-cleanup       # Mantener DB para debug
./run_odoo_tests.sh --help             # Ver todas las opciones
```

## 🔧 Script de Tests

### `run_odoo_tests.sh` - Tests con Odoo Real

Script Bash que usa Odoo real para tests de integración:

**Características**:  
- Base de datos real PostgreSQL
- ORM completo de Odoo
- Instalación real del módulo
- Verificación exhaustiva

**Opciones disponibles**:
```bash
-d, --database      Nombre de DB de test
-a, --addons-path   Ruta de addons  
-o, --odoo-bin      Ejecutable de Odoo
--no-cleanup        Mantener DB después
```

## 🐛 Debugging Tests

### Ver logs detallados:
```bash
./run_odoo_tests.sh --log-level=debug
```

### Mantener DB para inspección:
```bash 
./run_odoo_tests.sh --no-cleanup
# Conectar después: psql superset_test_db
```

### Tests individuales:
```bash
./run_odoo_tests.sh test_superset_utils.py
```

### Mock debugging (standalone):
```bash
python run_tests.py utils  # Ver output detallado
```

## 🚨 CI/CD Integration

### GitHub Actions
```yaml
name: Test Superset Module
on: [push, pull_request]
jobs:
  test-with-odoo:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: odoo
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python  
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install Odoo
        run: pip install odoo
      - name: Run Tests
        run: |
          cd eticco_superset_integration
          ./run_odoo_tests.sh
```

## 🏃‍♂️ Workflow Recomendado

### Desarrollo y Testing:
```bash
# Tests completos antes de commit
./run_odoo_tests.sh

# Si falla, debug específico:
./run_odoo_tests.sh test_specific.py --no-cleanup
```

### En CI/CD:
```bash
# Pipeline de tests
./run_odoo_tests.sh
```

## 📈 Performance de Tests

### Tiempos Típicos:
- **Tests completos**: ~30 segundos (55 tests)
- **Test individual**: ~5 segundos

### Optimizaciones:
- Mocks inteligentes para APIs externas
- Cache de configuración en tests
- Setup/teardown mínimo
- Paralelización cuando es posible

## 🤝 Añadir Nuevos Tests

### Estructura de Test:
```python
from odoo.tests.common import TransactionCase
from unittest.mock import patch, Mock

class TestMiNuevaFuncionalidad(TransactionCase):
    
    def setUp(self):
        super().setUp()
        # Setup específico
        
    def test_funcionalidad_basica(self):
        """Test: Descripción clara de lo que se prueba"""
        # Arrange
        datos = {'campo': 'valor'}
        
        # Act  
        resultado = self.metodo_a_probar(datos)
        
        # Assert
        self.assertEqual(resultado, 'esperado')
        
    @patch('requests.get')
    def test_con_mocks(self, mock_get):
        """Test: Funcionalidad que usa APIs externas"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        resultado = self.metodo_con_api()
        
        self.assertTrue(resultado)
        mock_get.assert_called_once()
```

### Ejecutar tu nuevo test:
```bash
# Test específico
./run_odoo_tests.sh test_mi_nueva_funcionalidad.py

# Todos los tests
./run_odoo_tests.sh
```

---

💡 **Tip**: Usa `./run_odoo_tests.sh test_specific.py --no-cleanup` para debug detallado de tests individuales.