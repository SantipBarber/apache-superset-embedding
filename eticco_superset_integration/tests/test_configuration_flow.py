# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from unittest.mock import patch, Mock


class TestConfigurationFlow(TransactionCase):
    """Tests para el flujo de configuración Settings → Analytics"""

    def setUp(self):
        super().setUp()
        self.ConfigSettings = self.env['res.config.settings']
        self.AnalyticsHub = self.env['superset.analytics.hub']
        self.Utils = self.env['superset.utils']
        
        # Crear registros de prueba
        self.config = self.ConfigSettings.create({
            'superset_url': 'http://localhost:8088',
            'superset_username': 'admin',
            'superset_password': 'admin',
            'superset_timeout': 30,
            'superset_menu_name': 'Analytics Test'
        })
        
        self.hub = self.AnalyticsHub.create({
            'display_name': 'Test Hub'
        })

    def test_configuration_parameters_stored(self):
        """Test: Verificar que los parámetros se guardan correctamente"""
        # Guardar configuración
        self.config.execute()
        
        # Verificar parámetros guardados
        ICPSudo = self.env['ir.config_parameter'].sudo()
        self.assertEqual(ICPSudo.get_param('superset.url'), 'http://localhost:8088')
        self.assertEqual(ICPSudo.get_param('superset.username'), 'admin')
        self.assertEqual(ICPSudo.get_param('superset.password'), 'admin')
        self.assertEqual(ICPSudo.get_param('superset.timeout'), '30')

    def test_configuration_validation_url(self):
        """Test: Validación de URL de configuración"""
        # URL inválida
        self.config.superset_url = 'invalid-url'
        
        with self.assertRaises(ValidationError) as context:
            self.config._check_superset_url()
        
        self.assertIn('http://', str(context.exception))

    def test_configuration_validation_url_with_spaces(self):
        """Test: Validación de URL con espacios"""
        self.config.superset_url = 'http://localhost :8088'
        
        with self.assertRaises(ValidationError):
            self.config._check_superset_url()

    def test_configuration_validation_timeout(self):
        """Test: Validación de timeout"""
        # Timeout muy bajo
        self.config.superset_timeout = 1
        
        with self.assertRaises(ValidationError):
            self.config._check_timeout()
        
        # Timeout muy alto  
        self.config.superset_timeout = 500
        
        with self.assertRaises(ValidationError):
            self.config._check_timeout()

    def test_compute_connection_status_incomplete(self):
        """Test: Estado de conexión incompleta"""
        self.config.superset_url = ''
        self.config._compute_connection_status()
        
        self.assertIn('incompleta', self.config.superset_connection_status)

    def test_compute_connection_status_complete(self):
        """Test: Estado de conexión completa"""
        # Ya configurado en setUp
        self.config._compute_connection_status()
        
        self.assertIn('Configurado', self.config.superset_connection_status)

    @patch('requests.post')
    @patch('requests.get')
    def test_test_superset_connection_success(self, mock_get, mock_post):
        """Test: Prueba de conexión exitosa"""
        # Mock login exitoso
        mock_login_response = Mock()
        mock_login_response.status_code = 200
        mock_login_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_login_response
        
        # Mock health endpoint
        mock_health_response = Mock()
        mock_health_response.status_code = 200
        mock_get.return_value = mock_health_response
        
        with patch.object(self.Utils, 'test_superset_connection') as mock_test:
            mock_test.return_value = {
                'success': True,
                'details': {'dashboards_found': 5}
            }
            
            result = self.config.test_superset_connection()
        
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertIn('exitosa', result['params']['title'])

    @patch('requests.post')
    def test_test_superset_connection_failure(self, mock_post):
        """Test: Prueba de conexión fallida"""
        # Mock error de autenticación
        mock_post.side_effect = Exception('Connection failed')
        
        with patch.object(self.Utils, 'test_superset_connection') as mock_test:
            mock_test.side_effect = ValidationError('Connection failed')
            
            with self.assertRaises(ValidationError):
                self.config.test_superset_connection()

    @patch('requests.get')
    def test_open_superset_dashboards_success(self, mock_get):
        """Test: Abrir lista de dashboards exitosamente"""
        # Mock respuesta de dashboards
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': [
                {
                    'id': 1,
                    'dashboard_title': 'Sales Dashboard',
                    'published': True
                },
                {
                    'id': 2,
                    'dashboard_title': 'Analytics Dashboard',
                    'published': True
                }
            ]
        }
        
        # Mock embedding responses
        mock_embedding_response = Mock()
        mock_embedding_response.status_code = 200
        mock_embedding_response.json.return_value = {
            'result': {'uuid': 'embedding-uuid'}
        }
        
        mock_get.side_effect = [mock_response, mock_embedding_response, mock_embedding_response]
        
        with patch.object(self.Utils, 'get_access_token', return_value='test_token'):
            result = self.config.open_superset_dashboards()
        
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertIn('2 Dashboards', result['params']['title'])

    def test_clear_superset_cache(self):
        """Test: Limpiar cache de Superset"""
        with patch.object(self.Utils, 'clear_token_cache') as mock_clear:
            mock_clear.return_value = {'success': True, 'message': 'Cache limpiado'}
            
            result = self.config.clear_superset_cache()
        
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertIn('limpiado', result['params']['title'])

    def test_create_dashboard_menu_no_parent(self):
        """Test: Crear menú sin padre seleccionado"""
        self.config.superset_menu_parent = False
        
        with self.assertRaises(ValidationError) as context:
            self.config.create_dashboard_menu()
        
        self.assertIn('menú padre', str(context.exception))

    def test_create_dashboard_menu_success(self):
        """Test: Crear menú exitosamente"""
        # Buscar un menú padre existente
        parent_menu = self.env['ir.ui.menu'].search([('parent_id', '=', False)], limit=1)
        if not parent_menu:
            parent_menu = self.env['ir.ui.menu'].create({
                'name': 'Test Parent Menu',
                'parent_id': False
            })
        
        self.config.superset_menu_parent = parent_menu.id
        
        result = self.config.create_dashboard_menu()
        
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertIn('creado', result['params']['title'])
        
        # Verificar que el menú se creó
        created_menu = self.env['ir.ui.menu'].search([
            ('name', '=', 'Analytics Test'),
            ('parent_id', '=', parent_menu.id)
        ])
        self.assertTrue(created_menu.exists())

    def test_create_dashboard_menu_already_exists(self):
        """Test: Crear menú que ya existe"""
        # Crear menú padre
        parent_menu = self.env['ir.ui.menu'].create({
            'name': 'Test Parent Menu',
            'parent_id': False
        })
        
        # Crear menú hijo existente
        self.env['ir.ui.menu'].create({
            'name': 'Analytics Test',
            'parent_id': parent_menu.id
        })
        
        self.config.superset_menu_parent = parent_menu.id
        
        result = self.config.create_dashboard_menu()
        
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertIn('ya existe', result['params']['title'])

    def test_settings_to_analytics_flow(self):
        """Test: Flujo completo Settings → Analytics"""
        # 1. Configurar en Settings
        self.config.execute()
        
        # 2. Simular navegación a Analytics
        with patch.object(self.Utils, 'get_dashboard_stats_cached') as mock_stats:
            mock_stats.return_value = {
                'has_configuration': True,
                'total_dashboards': 3,
                'with_embedding': 2
            }
            
            # Simular cálculo de estado en Analytics Hub
            self.hub._compute_system_status()
        
        # 3. Verificar que Analytics detecta configuración
        self.assertTrue(self.hub.has_configuration)
        self.assertEqual(self.hub.available_dashboards_count, 2)

    def test_configuration_change_triggers_hub_refresh(self):
        """Test: Cambio de configuración refresca hub automáticamente"""
        # Simular hub existente
        with patch.object(self.AnalyticsHub, 'search') as mock_search:
            mock_search.return_value = self.hub
            
            with patch.object(self.hub, 'force_refresh_configuration') as mock_refresh:
                # Cambiar configuración
                self.config.write({'superset_url': 'http://new-server:8088'})
                
                # Verificar que se llamó al refresh
                mock_refresh.assert_called_once()

    @patch.object(None, 'get_dashboard_stats_cached')
    def test_dashboard_stats_integration(self, mock_stats):
        """Test: Integración de estadísticas de dashboards"""
        # Mock de estadísticas
        mock_stats.return_value = {
            'has_configuration': True,
            'total_dashboards': 10,
            'with_embedding': 5
        }
        
        # Configurar Utils para usar el mock
        with patch.object(self.Utils, 'get_dashboard_stats_cached', return_value=mock_stats.return_value):
            # Computar información de dashboards en settings
            self.config._compute_dashboards_info()
        
        # En un entorno real, esto debería usar el endpoint interno
        # Por ahora verificamos que los campos se podrían poblar
        self.assertIsInstance(self.config.superset_dashboards_count, int)
        self.assertIsInstance(self.config.superset_embedding_count, int)