# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from unittest.mock import patch, Mock
import time


class TestSupersetUtils(TransactionCase):
    """Tests para el modelo superset.utils"""

    def setUp(self):
        super().setUp()
        self.utils = self.env['superset.utils']
        
        # Configuración de prueba
        self.test_config = {
            'url': 'http://localhost:8088',
            'username': 'test_user',
            'password': 'test_pass',
            'timeout': 30
        }

    def test_get_superset_config(self):
        """Test: Obtener configuración de Superset"""
        # Configurar parámetros de prueba
        self.env['ir.config_parameter'].sudo().set_param('superset.url', 'http://test:8088')
        self.env['ir.config_parameter'].sudo().set_param('superset.username', 'testuser')
        self.env['ir.config_parameter'].sudo().set_param('superset.password', 'testpass')
        
        config = self.utils.get_superset_config()
        
        self.assertEqual(config['url'], 'http://test:8088')
        self.assertEqual(config['username'], 'testuser')
        self.assertEqual(config['password'], 'testpass')
        self.assertIsInstance(config['timeout'], int)

    def test_validate_config_success(self):
        """Test: Validar configuración correcta"""
        try:
            self.utils.validate_config(self.test_config)
            # Si no lanza excepción, la validación es exitosa
        except ValidationError:
            self.fail("validate_config() lanzó ValidationError con config válida")

    def test_validate_config_missing_url(self):
        """Test: Validar configuración sin URL"""
        config = self.test_config.copy()
        config['url'] = ''
        
        with self.assertRaises(ValidationError):
            self.utils.validate_config(config)

    def test_validate_config_invalid_url(self):
        """Test: Validar configuración con URL inválida"""
        config = self.test_config.copy()
        config['url'] = 'invalid-url'
        
        with self.assertRaises(ValidationError):
            self.utils.validate_config(config)

    def test_is_configured_true(self):
        """Test: Verificar configuración básica existente"""
        # Configurar parámetros de prueba
        self.env['ir.config_parameter'].sudo().set_param('superset.url', 'http://test:8088')
        self.env['ir.config_parameter'].sudo().set_param('superset.username', 'testuser')
        self.env['ir.config_parameter'].sudo().set_param('superset.password', 'testpass')
        
        result = self.utils.is_configured()
        self.assertTrue(result)

    def test_is_configured_false(self):
        """Test: Verificar configuración básica faltante"""
        # Limpiar parámetros
        self.env['ir.config_parameter'].sudo().set_param('superset.url', '')
        self.env['ir.config_parameter'].sudo().set_param('superset.username', '')
        self.env['ir.config_parameter'].sudo().set_param('superset.password', '')
        
        result = self.utils.is_configured()
        self.assertFalse(result)

    @patch('requests.post')
    def test_fetch_new_token_success(self, mock_post):
        """Test: Obtener nuevo token exitosamente"""
        # Mock de respuesta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'test_token_123'}
        mock_post.return_value = mock_response
        
        token = self.utils._fetch_new_token(self.test_config)
        
        self.assertEqual(token, 'test_token_123')
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_fetch_new_token_unauthorized(self, mock_post):
        """Test: Manejo de credenciales incorrectas"""
        # Mock de respuesta 401
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        with self.assertRaises(UserError) as context:
            self.utils._fetch_new_token(self.test_config)
        
        self.assertIn('Credenciales incorrectas', str(context.exception))

    def test_cache_functionality(self):
        """Test: Funcionalidad de cache"""
        cache_key = 'test_key'
        test_token = 'cached_token_123'
        
        # Probar guardado en cache
        self.utils._cache_token(cache_key, test_token)
        
        # Probar recuperación de cache
        cached_token = self.utils._get_cached_token(cache_key)
        self.assertEqual(cached_token, test_token)

    def test_cache_expiration(self):
        """Test: Expiración de cache"""
        cache_key = 'test_key_expiry'
        test_token = 'expiring_token'
        
        # Forzar expiración modificando directamente el cache
        self.utils._cache_token(cache_key, test_token)
        
        # Modificar tiempo de expiración para simular expiración
        if hasattr(self.utils, '_token_cache'):
            self.utils._token_cache[cache_key]['expires'] = time.time() - 1
        
        # Debería retornar None por estar expirado
        cached_token = self.utils._get_cached_token(cache_key)
        self.assertIsNone(cached_token)

    def test_clear_token_cache(self):
        """Test: Limpiar cache de tokens"""
        # Añadir algo al cache primero
        self.utils._cache_token('test_key', 'test_token')
        
        # Limpiar cache
        result = self.utils.clear_token_cache()
        
        self.assertTrue(result['success'])
        
        # Verificar que el cache está limpio
        cached_token = self.utils._get_cached_token('test_key')
        self.assertIsNone(cached_token)

    @patch('requests.get')
    @patch.object(utils := None, 'get_access_token')
    def test_get_dashboard_stats_cached_success(self, mock_get_token, mock_get):
        """Test: Obtener estadísticas de dashboards con cache"""
        # Configurar mocks
        mock_get_token.return_value = 'test_token'
        
        # Mock de respuesta de dashboards
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': [
                {'id': 1, 'published': True},
                {'id': 2, 'published': True},
                {'id': 3, 'published': False},  # No publicado
            ]
        }
        
        # Mock de respuestas de embedding
        mock_embedding_response = Mock()
        mock_embedding_response.status_code = 200
        mock_embedding_response.json.return_value = {
            'result': {'uuid': 'test-embedding-uuid'}
        }
        
        mock_get.side_effect = [mock_response, mock_embedding_response, mock_embedding_response]
        
        # Configurar parámetros para que is_configured() retorne True
        self.env['ir.config_parameter'].sudo().set_param('superset.url', 'http://test:8088')
        self.env['ir.config_parameter'].sudo().set_param('superset.username', 'testuser')
        self.env['ir.config_parameter'].sudo().set_param('superset.password', 'testpass')
        
        # Ejecutar test
        with patch.object(self.utils, 'get_access_token', return_value='test_token'):
            stats = self.utils.get_dashboard_stats_cached()
        
        self.assertTrue(stats['has_configuration'])
        self.assertEqual(stats['total_dashboards'], 2)  # Solo los publicados
        self.assertEqual(stats['with_embedding'], 2)

    def test_get_dashboard_stats_cached_not_configured(self):
        """Test: Estadísticas cuando no está configurado"""
        # Limpiar configuración
        self.env['ir.config_parameter'].sudo().set_param('superset.url', '')
        
        stats = self.utils.get_dashboard_stats_cached()
        
        self.assertFalse(stats['has_configuration'])
        self.assertEqual(stats['total_dashboards'], 0)
        self.assertEqual(stats['with_embedding'], 0)