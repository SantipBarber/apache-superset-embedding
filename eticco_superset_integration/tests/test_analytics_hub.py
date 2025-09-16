# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from unittest.mock import patch, Mock
import requests


class TestAnalyticsHub(TransactionCase):
    """Tests para el modelo superset.analytics.hub"""

    def setUp(self):
        super().setUp()
        self.AnalyticsHub = self.env['superset.analytics.hub']
        
        # Crear registro de prueba
        self.hub = self.AnalyticsHub.create({
            'display_name': 'Test Analytics Hub'
        })
        
        # Configurar parámetros de Superset para tests
        self.env['ir.config_parameter'].sudo().set_param('superset.url', 'http://localhost:8088')
        self.env['ir.config_parameter'].sudo().set_param('superset.username', 'admin')
        self.env['ir.config_parameter'].sudo().set_param('superset.password', 'admin')

    def test_create_hub_record(self):
        """Test: Crear registro de Analytics Hub"""
        self.assertTrue(self.hub.exists())
        self.assertEqual(self.hub.display_name, 'Test Analytics Hub')
        self.assertFalse(self.hub.dashboard_loaded)

    @patch.object(None, 'get_dashboard_stats_cached')
    def test_compute_system_status_configured(self, mock_stats):
        """Test: Calcular estado del sistema cuando está configurado"""
        # Mock de estadísticas
        mock_stats.return_value = {
            'has_configuration': True,
            'total_dashboards': 5,
            'with_embedding': 3
        }
        
        # Simular campo computado
        with patch.object(self.env['superset.utils'], 'get_dashboard_stats_cached', return_value=mock_stats.return_value):
            self.hub._compute_system_status()
        
        self.assertTrue(self.hub.has_configuration)
        self.assertEqual(self.hub.available_dashboards_count, 3)

    @patch.object(None, 'get_dashboard_stats_cached')
    def test_compute_system_status_not_configured(self, mock_stats):
        """Test: Calcular estado del sistema cuando no está configurado"""
        # Mock de estadísticas para sistema no configurado
        mock_stats.return_value = {
            'has_configuration': False,
            'total_dashboards': 0,
            'with_embedding': 0
        }
        
        with patch.object(self.env['superset.utils'], 'get_dashboard_stats_cached', return_value=mock_stats.return_value):
            self.hub._compute_system_status()
        
        self.assertFalse(self.hub.has_configuration)
        self.assertEqual(self.hub.available_dashboards_count, 0)

    def test_reset_dashboard_info(self):
        """Test: Resetear información del dashboard"""
        # Establecer algunos valores primero
        self.hub.current_dashboard_title = 'Test Dashboard'
        self.hub.current_dashboard_id = 123
        self.hub.current_embedding_uuid = 'test-uuid'
        self.hub.current_dashboard_info = 'Test info'
        
        # Resetear
        self.hub._reset_dashboard_info()
        
        # Verificar reset
        self.assertEqual(self.hub.current_dashboard_title, '')
        self.assertFalse(self.hub.current_dashboard_id)
        self.assertFalse(self.hub.current_embedding_uuid)
        self.assertEqual(self.hub.current_dashboard_info, '')

    @patch('requests.get')
    def test_get_dashboard_selection_no_config(self, mock_get):
        """Test: Obtener selección cuando no hay configuración"""
        # Limpiar configuración
        self.env['ir.config_parameter'].sudo().set_param('superset.url', '')
        
        selection = self.hub._get_dashboard_selection()
        
        self.assertEqual(len(selection), 1)
        self.assertEqual(selection[0][0], 'no_config')
        self.assertIn('Configurar Superset', selection[0][1])

    @patch('requests.get')
    @patch.object(None, 'get_access_token')
    def test_get_dashboard_selection_success(self, mock_get_token, mock_get):
        """Test: Obtener selección de dashboards exitosamente"""
        # Mock token
        mock_get_token.return_value = 'test_token'
        
        # Mock respuesta de dashboards
        mock_dashboards_response = Mock()
        mock_dashboards_response.status_code = 200
        mock_dashboards_response.json.return_value = {
            'result': [
                {
                    'id': 1,
                    'uuid': 'dashboard-uuid-1',
                    'dashboard_title': 'Sales Dashboard',
                    'published': True
                },
                {
                    'id': 2,
                    'uuid': 'dashboard-uuid-2', 
                    'dashboard_title': 'Analytics Dashboard',
                    'published': True
                }
            ]
        }
        
        # Mock respuesta de embedding
        mock_embedding_response = Mock()
        mock_embedding_response.status_code = 200
        mock_embedding_response.json.return_value = {
            'result': {'uuid': 'embedding-uuid'}
        }
        
        # Configurar mock_get para retornar respuestas apropiadas
        mock_get.side_effect = [
            mock_dashboards_response,  # Primera llamada: obtener dashboards
            mock_embedding_response,   # Segunda llamada: embedding para dashboard 1
            mock_embedding_response    # Tercera llamada: embedding para dashboard 2
        ]
        
        with patch.object(self.env['superset.utils'], 'get_access_token', return_value='test_token'):
            selection = self.hub._get_dashboard_selection()
        
        self.assertEqual(len(selection), 2)
        self.assertEqual(selection[0][0], 'dashboard-uuid-1')
        self.assertIn('Sales Dashboard', selection[0][1])

    @patch('requests.get')  
    def test_get_dashboard_selection_no_dashboards(self, mock_get):
        """Test: No hay dashboards disponibles"""
        # Mock respuesta sin dashboards
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': []}
        mock_get.return_value = mock_response
        
        with patch.object(self.env['superset.utils'], 'get_access_token', return_value='test_token'):
            selection = self.hub._get_dashboard_selection()
        
        self.assertEqual(len(selection), 1)
        self.assertEqual(selection[0][0], 'no_dashboards')

    def test_onchange_selected_dashboard_valid(self):
        """Test: Cambio a dashboard válido"""
        self.hub.selected_dashboard = 'test-uuid-123'
        self.hub._onchange_selected_dashboard()
        
        self.assertTrue(self.hub.dashboard_loaded)

    def test_onchange_selected_dashboard_invalid(self):
        """Test: Cambio a dashboard inválido"""
        self.hub.selected_dashboard = 'no_config'
        self.hub._onchange_selected_dashboard()
        
        self.assertFalse(self.hub.dashboard_loaded)

    def test_action_load_dashboard_no_selection(self):
        """Test: Cargar dashboard sin selección"""
        self.hub.selected_dashboard = False
        
        with self.assertRaises(UserError) as context:
            self.hub.action_load_dashboard()
        
        self.assertIn('Selecciona un dashboard válido', str(context.exception))

    def test_action_refresh_dashboards(self):
        """Test: Refrescar dashboards"""
        # Establecer algunos valores primero
        self.hub.selected_dashboard = 'test-uuid'
        self.hub.dashboard_loaded = True
        
        result = self.hub.action_refresh_dashboards()
        
        # Verificar que se limpiaron los valores
        self.assertFalse(self.hub.selected_dashboard)
        self.assertFalse(self.hub.dashboard_loaded)
        
        # Verificar tipo de acción retornada
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'reload')

    def test_action_open_settings(self):
        """Test: Abrir configuración de Superset"""
        result = self.hub.action_open_settings()
        
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'res.config.settings')
        self.assertEqual(result['view_mode'], 'form')
        self.assertEqual(result['target'], 'new')
        self.assertIn('hub_id', result['context'])

    def test_get_embedding_url_no_dashboard(self):
        """Test: URL de embedding sin dashboard"""
        self.hub.dashboard_loaded = False
        
        url = self.hub.get_embedding_url()
        self.assertIsNone(url)

    def test_get_embedding_url_with_dashboard(self):
        """Test: URL de embedding con dashboard"""
        self.hub.dashboard_loaded = True
        self.hub.current_dashboard_id = 123
        
        url = self.hub.get_embedding_url()
        self.assertEqual(url, '/superset/dashboard/123')

    @patch('requests.get')
    @patch('requests.post')
    def test_get_dashboard_data_for_js_success(self, mock_post, mock_get):
        """Test: Obtener datos para JavaScript exitosamente"""
        self.hub.selected_dashboard = 'test-dashboard-uuid'
        
        # Mock respuesta de dashboards
        mock_dashboards_response = Mock()
        mock_dashboards_response.status_code = 200
        mock_dashboards_response.json.return_value = {
            'result': [{
                'uuid': 'test-dashboard-uuid',
                'id': 123,
                'dashboard_title': 'Test Dashboard'
            }]
        }
        
        # Mock respuesta de embedding
        mock_embedding_response = Mock()
        mock_embedding_response.status_code = 200
        mock_embedding_response.json.return_value = {
            'result': {'uuid': 'embedding-uuid-123'}
        }
        
        # Mock respuesta de guest token
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {'token': 'guest-token-123'}
        
        mock_get.side_effect = [mock_dashboards_response, mock_embedding_response]
        mock_post.return_value = mock_token_response
        
        with patch.object(self.env['superset.utils'], 'get_access_token', return_value='access_token'):
            with patch.object(self.env['superset.utils'], 'get_superset_config', return_value={'url': 'http://localhost:8088', 'timeout': 30}):
                result = self.hub.get_dashboard_data_for_js()
        
        self.assertIn('embedding_uuid', result)
        self.assertIn('guest_token', result)
        self.assertIn('superset_domain', result)
        self.assertEqual(result['embedding_uuid'], 'embedding-uuid-123')
        self.assertEqual(result['guest_token'], 'guest-token-123')

    def test_get_dashboard_data_for_js_no_selection(self):
        """Test: Datos para JavaScript sin selección"""
        self.hub.selected_dashboard = False
        
        result = self.hub.get_dashboard_data_for_js()
        
        self.assertIn('error', result)
        self.assertIn('No hay dashboard seleccionado', result['error'])

    def test_refresh_dashboard_options(self):
        """Test: Refrescar opciones de dashboard"""
        with patch.object(self.hub, '_compute_system_status'):
            with patch.object(self.hub, '_get_dashboard_selection', return_value=[('uuid1', 'Dashboard 1'), ('uuid2', 'Dashboard 2')]):
                result = self.hub.refresh_dashboard_options()
        
        self.assertTrue(result['options_refreshed'])
        self.assertEqual(result['available_options'], 2)
        self.assertIn('has_configuration', result)
        self.assertIn('configuration_status', result)

    def test_force_refresh_configuration(self):
        """Test: Forzar refresco de configuración"""
        result = self.hub.force_refresh_configuration()
        
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'reload')

    def test_get_default_hub(self):
        """Test: Obtener hub por defecto"""
        # Limpiar hubs existentes
        self.env['superset.analytics.hub'].search([]).unlink()
        
        # Obtener hub por defecto (debería crear uno nuevo)
        hub = self.AnalyticsHub.get_default_hub()
        
        self.assertTrue(hub.exists())
        self.assertEqual(hub.display_name, 'Analytics Dashboard')

    def test_get_default_hub_existing(self):
        """Test: Obtener hub por defecto existente"""
        # Ya existe self.hub del setUp
        hub = self.AnalyticsHub.get_default_hub()
        
        # Debería retornar el existente
        self.assertEqual(hub.id, self.hub.id)