# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import logging
import functools
import time

_logger = logging.getLogger(__name__)


class SupersetUtils(models.AbstractModel):
    """Utilidades comunes para integración con Superset"""
    _name = 'superset.utils'
    _description = 'Utilidades Superset'

    @api.model
    def get_superset_config(self):
        """Obtener configuración de Superset de manera centralizada"""
        ICPSudo = self.env['ir.config_parameter'].sudo()
        config = {
            'url': ICPSudo.get_param('superset.url', '').rstrip('/'),
            'username': ICPSudo.get_param('superset.username', ''),
            'password': ICPSudo.get_param('superset.password', ''),
            'timeout': int(ICPSudo.get_param('superset.timeout', '30')),
            'debug_mode': ICPSudo.get_param('superset.debug_mode', 'False').lower() == 'true',
            'cache_tokens': ICPSudo.get_param('superset.cache_tokens', 'True').lower() == 'true',
        }
        return config

    @api.model
    def validate_config(self, config=None):
        """Validar configuración de Superset"""
        if not config:
            config = self.get_superset_config()
            
        errors = []
        
        if not config.get('url'):
            errors.append('URL de Superset no configurada')
        elif not config['url'].startswith(('http://', 'https://')):
            errors.append('URL debe empezar con http:// o https://')
            
        if not config.get('username'):
            errors.append('Usuario no configurado')
            
        if not config.get('password'):
            errors.append('Contraseña no configurada')
            
        if config.get('timeout', 0) < 5:
            errors.append('Timeout debe ser mayor a 5 segundos')
            
        if errors:
            raise ValidationError(_('Configuración inválida: %s') % ', '.join(errors))
            
        return True


    @api.model
    def get_access_token(self, config=None, force_refresh=False):
        """Obtener token de acceso con cache inteligente"""
        if not config:
            config = self.get_superset_config()
            
        self.validate_config(config)
        
        cache_key = f"superset_token_{hash(config['url'] + config['username'])}"
        
        if config.get('cache_tokens') and not force_refresh:
            cached_token = self._get_cached_token(cache_key)
            if cached_token:
                return cached_token
        
        token = self._fetch_new_token(config)
        
        if config.get('cache_tokens') and token:
            self._cache_token(cache_key, token)
            
        return token

    def _get_cached_token(self, cache_key):
        """Obtener token del cache"""
        try:
            if hasattr(self, '_token_cache'):
                cache_entry = self._token_cache.get(cache_key)
                if cache_entry and cache_entry['expires'] > time.time():
                    return cache_entry['token']
        except Exception as e:
            _logger.debug('Error obteniendo token del cache: %s', str(e))
        return None

    def _cache_token(self, cache_key, token):
        """Guardar token en cache"""
        try:
            if not hasattr(self, '_token_cache'):
                self._token_cache = {}
            
            self._token_cache[cache_key] = {
                'token': token,
                'expires': time.time() + 240
            }
        except Exception as e:
            _logger.debug('Error guardando token en cache: %s', str(e))

    def _fetch_new_token(self, config):
        """Obtener nuevo token desde Superset API"""
        try:
            login_url = f"{config['url']}/api/v1/security/login"
            login_data = {
                'username': config['username'],
                'password': config['password'],
                'provider': 'db'
            }
            
            response = requests.post(
                login_url,
                json=login_data,
                headers={'Content-Type': 'application/json'},
                timeout=config.get('timeout', 30)
            )
            
            if response.status_code == 401:
                raise UserError(_('Credenciales incorrectas. Verifica usuario y contraseña.'))
            elif response.status_code == 403:
                raise UserError(_('Usuario sin permisos suficientes para acceder a Superset.'))
            elif response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', f'Error HTTP {response.status_code}')
                raise UserError(_('Error de autenticación: %s') % error_msg)
                
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                raise UserError(_('Respuesta de login inválida: sin token de acceso'))
                
            return access_token
            
        except requests.exceptions.ConnectionError:
            raise UserError(_('No se puede conectar al servidor Superset. Verifica la URL y conectividad.'))
        except requests.exceptions.Timeout:
            raise UserError(_('Timeout al conectar con Superset. El servidor no responde.'))
        except requests.exceptions.RequestException as e:
            raise UserError(_('Error de red: %s') % str(e))

    @api.model
    def test_superset_connection(self, config=None):
        """Probar conexión a Superset de manera robusta"""
        if not config:
            config = self.get_superset_config()
            
        try:
            self.validate_config(config)
            health_response = self._test_health_endpoint(config)
            access_token = self.get_access_token(config, force_refresh=True)
            dashboards_count = self._test_api_access(config, access_token)
            
            return {
                'success': True,
                'message': _('Conexión exitosa'),
                'details': {
                    'health': 'OK',
                    'auth': 'OK',
                    'api_access': 'OK',
                    'dashboards_found': dashboards_count
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'details': {
                    'error_type': type(e).__name__
                }
            }

    def _test_health_endpoint(self, config):
        """Probar endpoint de salud"""
        try:
            health_url = f"{config['url']}/health"
            response = requests.get(health_url, timeout=config.get('timeout', 30))
            
            if response.status_code != 200:
                raise UserError(_('Superset no está disponible (HTTP %s)') % response.status_code)
                
            return response
        except requests.exceptions.ConnectionError:
            raise UserError(_('No se puede conectar al servidor Superset. Verifica la URL y conectividad.'))
        except requests.exceptions.Timeout:
            raise UserError(_('Timeout al conectar con Superset. El servidor no responde.'))
        except requests.exceptions.RequestException as e:
            raise UserError(_('Error de red: %s') % str(e))

    def _test_api_access(self, config, access_token):
        """Probar acceso a la API de dashboards"""
        try:
            dashboards_url = f"{config['url']}/api/v1/dashboard/"
            
            response = requests.get(
                dashboards_url,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=config.get('timeout', 30)
            )
            
            if response.status_code == 401:
                raise UserError(_('Token de acceso inválido o expirado'))
            elif response.status_code == 403:
                raise UserError(_('Sin permisos para acceder a dashboards'))
            elif response.status_code != 200:
                raise UserError(_('Error accediendo a API de dashboards (HTTP %s)') % response.status_code)
                
            dashboard_data = response.json()
            return len(dashboard_data.get('result', []))
        except requests.exceptions.ConnectionError:
            raise UserError(_('No se puede conectar al servidor Superset. Verifica la URL y conectividad.'))
        except requests.exceptions.Timeout:
            raise UserError(_('Timeout al conectar con Superset. El servidor no responde.'))
        except requests.exceptions.RequestException as e:
            raise UserError(_('Error de red: %s') % str(e))

    @api.model
    def clear_token_cache(self):
        """Limpiar cache de tokens"""
        try:
            if hasattr(self, '_token_cache'):
                self._token_cache.clear()
            return {'success': True, 'message': _('Cache limpiado')}
        except Exception as e:
            _logger.error('Error limpiando cache: %s', str(e))
            return {'success': False, 'message': str(e)}

    @api.model
    def log_debug(self, message, data=None):
        """Log debug solo si está habilitado"""
        config = self.get_superset_config()
        if config.get('debug_mode'):
            if data:
                _logger.info('SUPERSET DEBUG: %s - Data: %s', message, data)
            else:
                _logger.info('SUPERSET DEBUG: %s', message)

    @api.model 
    def create_user_notification(self, title, message, notification_type='info', sticky=False):
        """Crear notificación para el usuario"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': sticky,
            }
        }

    @api.model
    def validate_dashboard_data(self, dashboard_data):
        """Validar datos de dashboard"""
        errors = []
        
        if not dashboard_data:
            errors.append('Datos de dashboard vacíos')
            
        if not dashboard_data.get('id'):
            errors.append('Dashboard sin ID')
            
        if not dashboard_data.get('uuid'):
            errors.append('Dashboard sin UUID')
            
        if not dashboard_data.get('title'):
            errors.append('Dashboard sin título')
            
        if errors:
            raise ValidationError(_('Datos de dashboard inválidos: %s') % ', '.join(errors))
            
        return True

    @api.model
    def validate_embedding_requirements(self, dashboard_data):
        """Validar requisitos para embedding"""
        self.validate_dashboard_data(dashboard_data)
        
        if not dashboard_data.get('embedding_enabled'):
            raise ValidationError(_('Dashboard "%s" no tiene embedding habilitado') % dashboard_data.get('title'))
            
        if not dashboard_data.get('embedding_uuid'):
            raise ValidationError(_('Dashboard "%s" no tiene UUID de embedding') % dashboard_data.get('title'))
            
        return True
    
    @api.model
    def is_configured(self):
        """Verificar si Superset está configurado (sin hacer peticiones HTTP)"""
        try:
            config = self.get_superset_config()
            return bool(config.get('url') and config.get('username') and config.get('password'))
        except:
            return False
    
    @api.model
    def get_system_status(self, force_refresh=False):
        """Obtener estado del sistema de forma unificada y optimizada"""
        # Verificación básica primero (sin HTTP)
        if not self.is_configured():
            return {
                'has_configuration': False,
                'connection_status': 'Configuración incompleta',
                'total_dashboards': 0,
                'with_embedding': 0,
                'last_check': None
            }
        
        cache_key = 'system_status'
        cache_duration = 300  # 5 minutos
        
        # Usar cache si no se fuerza refresh
        if not force_refresh and hasattr(self, '_status_cache'):
            cache_entry = self._status_cache.get(cache_key)
            if cache_entry and cache_entry['expires'] > time.time():
                return cache_entry['data']
        
        # Calcular estado completo con HTTP (solo si es necesario)
        try:
            config = self.get_superset_config()
            self.validate_config(config)
            
            # Verificar conectividad básica
            access_token = self.get_access_token(config)
            
            # Obtener estadísticas de dashboards
            dashboards_url = f"{config['url']}/api/v1/dashboard/"
            params = {'q': '(page:0,page_size:100)'}
            
            response = requests.get(
                dashboards_url,
                params=params,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=config.get('timeout', 30)
            )
            
            if response.status_code == 200:
                data = response.json()
                dashboards = [d for d in data.get('result', []) if d.get('published')]
                
                # Contar dashboards con embedding
                embedding_count = 0
                for dashboard in dashboards:
                    try:
                        embedding_url = f"{config['url']}/api/v1/dashboard/{dashboard.get('id')}/embedded"
                        embedding_response = requests.get(
                            embedding_url,
                            headers={'Authorization': f'Bearer {access_token}'},
                            timeout=config.get('timeout', 30)
                        )
                        if (embedding_response.status_code == 200 and 
                            embedding_response.json().get('result', {}).get('uuid')):
                            embedding_count += 1
                    except:
                        pass
                
                status = {
                    'has_configuration': True,
                    'connection_status': 'Conectado correctamente',
                    'total_dashboards': len(dashboards),
                    'with_embedding': embedding_count,
                    'last_check': time.time()
                }
            else:
                status = {
                    'has_configuration': True,
                    'connection_status': f'Error HTTP {response.status_code}',
                    'total_dashboards': 0,
                    'with_embedding': 0,
                    'last_check': time.time()
                }
                
        except Exception as e:
            _logger.debug('Error verificando conexión con Superset: %s', str(e))
            status = {
                'has_configuration': True,
                'connection_status': f'Error de conexión: {str(e)[:50]}...',
                'total_dashboards': 0,
                'with_embedding': 0,
                'last_check': time.time()
            }
        
        # Guardar en cache
        if not hasattr(self, '_status_cache'):
            self._status_cache = {}
        self._status_cache[cache_key] = {
            'data': status,
            'expires': time.time() + cache_duration
        }
        
        return status
    
    @api.model  
    def get_dashboard_stats_cached(self):
        """Compatibilidad: obtener solo stats de dashboards"""
        status = self.get_system_status()
        return {
            'has_configuration': status['has_configuration'],
            'total_dashboards': status['total_dashboards'],
            'with_embedding': status['with_embedding']
        }