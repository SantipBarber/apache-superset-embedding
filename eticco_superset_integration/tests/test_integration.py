# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from unittest.mock import patch, Mock
import json


class TestSupersetIntegration(TransactionCase):
    """Tests de integración completa del módulo Superset"""

    def setUp(self):
        super().setUp()
        self.ConfigSettings = self.env['res.config.settings']
        self.AnalyticsHub = self.env['superset.analytics.hub']
        self.Utils = self.env['superset.utils']
        
        # Configuración completa de prueba
        self.config = self.ConfigSettings.create({
            'superset_url': 'http://localhost:8088',
            'superset_username': 'admin',
            'superset_password': 'admin',
            'superset_timeout': 30,
            'superset_debug_mode': True,
            'superset_cache_tokens': True,
            'superset_menu_name': 'Analytics Integration Test'
        })
        
        self.hub = self.AnalyticsHub.create({
            'display_name': 'Integration Test Hub'
        })

    def test_full_configuration_workflow(self):
        """Test: Flujo completo de configuración"""
        # 1. Guardar configuración
        self.config.execute()
        
        # 2. Verificar parámetros
        config = self.Utils.get_superset_config()
        self.assertEqual(config['url'], 'http://localhost:8088')
        self.assertEqual(config['username'], 'admin')
        self.assertTrue(config['debug_mode'])
        self.assertTrue(config['cache_tokens'])

    @patch('requests.post')
    @patch('requests.get') 
    def test_complete_dashboard_selection_flow(self, mock_get, mock_post):
        """Test: Flujo completo de selección de dashboard"""
        # Mock authentication
        mock_login = Mock()
        mock_login.status_code = 200
        mock_login.json.return_value = {'access_token': 'integration_test_token'}
        mock_post.return_value = mock_login
        
        # Mock dashboards response
        mock_dashboards = Mock()
        mock_dashboards.status_code = 200
        mock_dashboards.json.return_value = {
            'result': [
                {
                    'id': 1,
                    'uuid': 'dashboard-1-uuid',
                    'dashboard_title': 'Integration Test Dashboard',
                    'description': 'Test dashboard for integration',
                    'published': True,
                    'owners': [{'username': 'admin'}]
                }
            ]
        }
        
        # Mock embedding response
        mock_embedding = Mock()
        mock_embedding.status_code = 200
        mock_embedding.json.return_value = {
            'result': {'uuid': 'embedding-uuid-123'}
        }
        
        mock_get.side_effect = [mock_dashboards, mock_embedding]
        
        # Ejecutar flujo
        with patch.object(self.Utils, 'get_access_token', return_value='integration_test_token'):
            selection = self.hub._get_dashboard_selection()
        
        # Verificaciones
        self.assertGreater(len(selection), 0)
        dashboard_option = selection[0]
        self.assertEqual(dashboard_option[0], 'dashboard-1-uuid')
        self.assertIn('Integration Test Dashboard', dashboard_option[1])

    @patch('requests.get')
    @patch('requests.post')
    def test_complete_dashboard_loading_flow(self, mock_post, mock_get):
        """Test: Flujo completo de carga de dashboard"""
        # Establecer dashboard seleccionado
        self.hub.selected_dashboard = 'test-dashboard-uuid'
        
        # Mock dashboards API
        mock_dashboards_response = Mock()
        mock_dashboards_response.status_code = 200
        mock_dashboards_response.json.return_value = {
            'result': [{
                'uuid': 'test-dashboard-uuid',
                'id': 123,
                'dashboard_title': 'Complete Test Dashboard',
                'description': 'Integration test dashboard'
            }]
        }
        
        # Mock embedding API
        mock_embedding_response = Mock()
        mock_embedding_response.status_code = 200
        mock_embedding_response.json.return_value = {
            'result': {'uuid': 'embedding-uuid-456'}
        }
        
        # Mock guest token API
        mock_guest_token_response = Mock()
        mock_guest_token_response.status_code = 200
        mock_guest_token_response.json.return_value = {'token': 'guest-token-789'}
        
        mock_get.side_effect = [mock_dashboards_response, mock_embedding_response]
        mock_post.return_value = mock_guest_token_response
        
        # Ejecutar flujo completo
        with patch.object(self.Utils, 'get_access_token', return_value='access_token'):
            with patch.object(self.Utils, 'get_superset_config', return_value={
                'url': 'http://localhost:8088',
                'timeout': 30,
                'debug_mode': False
            }):
                result = self.hub.get_dashboard_data_for_js()
        
        # Verificaciones
        self.assertNotIn('error', result)
        self.assertEqual(result['embedding_uuid'], 'embedding-uuid-456')
        self.assertEqual(result['guest_token'], 'guest-token-789')
        self.assertEqual(result['superset_domain'], 'http://localhost:8088')
        self.assertEqual(result['dashboard_title'], 'Complete Test Dashboard')
        self.assertTrue(self.hub.dashboard_loaded)

    def test_error_handling_integration(self):
        """Test: Manejo integrado de errores"""
        # Test configuración inválida
        invalid_config = {
            'url': '',
            'username': 'admin',
            'password': 'admin'
        }
        
        with self.assertRaises(Exception):
            self.Utils.validate_config(invalid_config)
        
        # Test dashboard no encontrado
        self.hub.selected_dashboard = 'non-existent-uuid'
        
        with patch.object(self.Utils, 'get_superset_config', return_value={
            'url': 'http://localhost:8088', 'timeout': 30
        }):
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'result': []}  # Sin dashboards
                mock_get.return_value = mock_response
                
                with patch.object(self.Utils, 'get_access_token', return_value='token'):
                    result = self.hub.get_dashboard_data_for_js()
        
        self.assertIn('error', result)
        self.assertIn('no encontrado', result['error'])

    def test_cache_integration(self):
        """Test: Integración del sistema de cache"""
        # Test cache de tokens
        cache_key = 'test_integration_token'
        test_token = 'cached_integration_token'
        
        self.Utils._cache_token(cache_key, test_token)
        cached_token = self.Utils._get_cached_token(cache_key)
        
        self.assertEqual(cached_token, test_token)
        
        # Test cache de estadísticas
        with patch.object(self.Utils, 'is_configured', return_value=True):
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'result': [
                        {'id': 1, 'published': True},
                        {'id': 2, 'published': True}
                    ]
                }
                
                mock_embedding_response = Mock()
                mock_embedding_response.status_code = 200
                mock_embedding_response.json.return_value = {
                    'result': {'uuid': 'test-uuid'}
                }
                
                mock_get.side_effect = [mock_response, mock_embedding_response, mock_embedding_response]
                
                with patch.object(self.Utils, 'get_access_token', return_value='token'):
                    with patch.object(self.Utils, 'get_superset_config', return_value={
                        'url': 'http://localhost:8088', 'timeout': 30
                    }):
                        # Primera llamada - debería hacer HTTP
                        stats1 = self.Utils.get_dashboard_stats_cached()
                        
                        # Segunda llamada - debería usar cache
                        stats2 = self.Utils.get_dashboard_stats_cached()
                
                # Ambas deberían retornar los mismos datos
                self.assertEqual(stats1['with_embedding'], stats2['with_embedding'])
                self.assertTrue(stats1['has_configuration'])

    def test_menu_creation_integration(self):
        """Test: Integración de creación de menús"""
        # Crear menú padre de prueba
        parent_menu = self.env['ir.ui.menu'].create({
            'name': 'Integration Test Parent',
            'parent_id': False
        })
        
        self.config.superset_menu_parent = parent_menu.id
        result = self.config.create_dashboard_menu()
        
        # Verificar creación exitosa
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertIn('creado', result['params']['title'])
        
        # Verificar que el menú existe y tiene acción correcta
        created_menu = self.env['ir.ui.menu'].search([
            ('name', '=', 'Analytics Integration Test'),
            ('parent_id', '=', parent_menu.id)
        ])
        
        self.assertTrue(created_menu.exists())
        self.assertIn('superset.analytics.hub', created_menu.action)

    def test_field_computation_integration(self):
        """Test: Integración de campos computados"""
        # Mock de estadísticas para campos computados
        with patch.object(self.Utils, 'get_dashboard_stats_cached') as mock_stats:
            mock_stats.return_value = {
                'has_configuration': True,
                'total_dashboards': 8,
                'with_embedding': 5
            }
            
            # Computar estado del sistema
            self.hub._compute_system_status()
        
        # Verificar campos computados
        self.assertTrue(self.hub.has_configuration)
        self.assertEqual(self.hub.available_dashboards_count, 5)

    @patch('requests.get')
    def test_dashboard_info_computation_integration(self, mock_get):
        """Test: Integración de cálculo de información de dashboard"""
        self.hub.selected_dashboard = 'integration-test-uuid'
        
        # Mock respuestas
        mock_dashboards_response = Mock()
        mock_dashboards_response.status_code = 200
        mock_dashboards_response.json.return_value = {
            'result': [{
                'uuid': 'integration-test-uuid',
                'id': 999,
                'dashboard_title': 'Integration Dashboard Info Test',
                'description': 'Test description for integration',
                'owners': [{'username': 'admin'}, {'username': 'user1'}]
            }]
        }
        
        mock_embedding_response = Mock()
        mock_embedding_response.status_code = 200
        mock_embedding_response.json.return_value = {
            'result': {'uuid': 'embedding-integration-uuid'}
        }
        
        mock_get.side_effect = [mock_dashboards_response, mock_embedding_response]
        
        # Ejecutar cálculo de información
        with patch.object(self.Utils, 'get_access_token', return_value='token'):
            with patch.object(self.Utils, 'get_superset_config', return_value={
                'url': 'http://localhost:8088', 'timeout': 30
            }):
                self.hub._compute_dashboard_info()
        
        # Verificar información calculada
        self.assertEqual(self.hub.current_dashboard_title, 'Integration Dashboard Info Test')
        self.assertEqual(self.hub.current_dashboard_id, 999)
        self.assertEqual(self.hub.current_embedding_uuid, 'embedding-integration-uuid')
        self.assertIn('Integration Dashboard Info Test', self.hub.current_dashboard_info)
        self.assertIn('✅ Habilitado', self.hub.current_dashboard_info)
        self.assertIn('admin, user1', self.hub.current_dashboard_info)

    def test_refresh_integration_flow(self):
        """Test: Flujo integrado de refrescos"""
        # Configurar estado inicial
        self.hub.selected_dashboard = 'test-uuid'
        self.hub.dashboard_loaded = True
        
        # Test refresh de opciones
        with patch.object(self.hub, '_compute_system_status'):
            with patch.object(self.hub, '_get_dashboard_selection') as mock_selection:
                mock_selection.return_value = [
                    ('uuid1', 'Dashboard 1'),
                    ('uuid2', 'Dashboard 2'),
                    ('error', 'Error dashboard')  # Este no debe contar
                ]
                
                result = self.hub.refresh_dashboard_options()
        
        self.assertTrue(result['options_refreshed'])
        self.assertEqual(result['available_options'], 2)  # Solo los válidos
        
        # Test force refresh
        result2 = self.hub.force_refresh_configuration()
        self.assertEqual(result2['type'], 'ir.actions.client')
        self.assertEqual(result2['tag'], 'reload')

    def test_end_to_end_user_workflow(self):
        """Test: Flujo end-to-end del usuario"""
        # 1. Usuario configura Superset en Settings
        self.config.execute()
        
        # 2. Usuario va al menú Analytics
        with patch.object(self.Utils, 'get_dashboard_stats_cached') as mock_stats:
            mock_stats.return_value = {
                'has_configuration': True,
                'total_dashboards': 3,
                'with_embedding': 2
            }
            
            self.hub._compute_system_status()
        
        # 3. Usuario ve dashboards disponibles
        with patch.object(self.hub, '_get_dashboard_selection') as mock_selection:
            mock_selection.return_value = [
                ('uuid1', '📊 Sales Dashboard'),
                ('uuid2', '📊 Analytics Dashboard')
            ]
            
            selection = self.hub._get_dashboard_selection()
        
        # 4. Usuario selecciona dashboard
        self.hub.selected_dashboard = 'uuid1'
        self.hub._onchange_selected_dashboard()
        
        # 5. Sistema carga dashboard automáticamente
        with patch.object(self.hub, 'get_dashboard_data_for_js') as mock_js_data:
            mock_js_data.return_value = {
                'embedding_uuid': 'final-embedding-uuid',
                'guest_token': 'final-guest-token',
                'superset_domain': 'http://localhost:8088',
                'dashboard_title': 'Sales Dashboard',
                'dashboard_id': 1
            }
            
            js_data = self.hub.get_dashboard_data_for_js()
        
        # Verificaciones del flujo completo
        self.assertTrue(self.hub.has_configuration)
        self.assertGreater(self.hub.available_dashboards_count, 0)
        self.assertEqual(len(selection), 2)
        self.assertTrue(self.hub.dashboard_loaded)
        self.assertIn('embedding_uuid', js_data)
        self.assertIn('guest_token', js_data)