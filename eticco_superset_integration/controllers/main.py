# -*- coding: utf-8 -*-
 
from odoo import http
from odoo.http import request
import requests
import json
import logging
from datetime import datetime, timedelta
import functools
 
_logger = logging.getLogger(__name__)
 
 
def require_superset_user(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not request.env.user.has_group('eticco_superset_integration.group_superset_user'):
            return {
                'success': False,
                'error': 'No tiene permisos para acceder a dashboards de Superset'
            }
        return func(*args, **kwargs)
    return wrapper
 
 
class SupersetController(http.Controller):
 
    def __init__(self):
        super().__init__()
        self._access_token_cache = {}
        self._cache_timeout = 240
 
    def _get_superset_config(self):
        try:
            ICPSudo = request.env['ir.config_parameter'].sudo()
            config = {
                'url': ICPSudo.get_param('superset.url', '').rstrip('/'),
                'username': ICPSudo.get_param('superset.username', ''),
                'password': ICPSudo.get_param('superset.password', ''),
            }
            
            if not all(config.values()):
                return None
                
            return config
        except Exception as e:
            _logger.error('Error obteniendo configuración Superset: %s', str(e))
            return None
 
    def _is_token_valid(self, timestamp):
        if not timestamp:
            return False
        return datetime.now() < timestamp + timedelta(seconds=self._cache_timeout)
 
    def _get_access_token(self, config, force_refresh=False):
        cache_key = f"{config['url']}_{config['username']}"
        
        if not force_refresh and cache_key in self._access_token_cache:
            token_data = self._access_token_cache[cache_key]
            if self._is_token_valid(token_data.get('timestamp')):
                _logger.info('Usando token cached para %s', config['url'])
                return token_data['token']
        
        try:
            login_url = f"{config['url']}/api/v1/security/login"
            login_data = {
                'username': config['username'],
                'password': config['password'],
                'provider': 'db'
            }
            
            _logger.info('Solicitando nuevo access token para %s', config['url'])
            response = requests.post(
                login_url,
                json=login_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token')
                
                if access_token:
                    self._access_token_cache[cache_key] = {
                        'token': access_token,
                        'timestamp': datetime.now()
                    }
                    _logger.info('Token obtenido y cacheado exitosamente')
                    return access_token
                else:
                    _logger.error('Respuesta sin access_token: %s', data)
                    raise Exception('Respuesta sin access_token')
                    
            elif response.status_code == 401:
                raise Exception('Credenciales incorrectas')
            elif response.status_code == 403:
                raise Exception('Usuario sin permisos suficientes')
            else:
                _logger.error('Error login HTTP %s: %s', response.status_code, response.text)
                raise Exception(f'Error de autenticación: HTTP {response.status_code}')
                
        except requests.exceptions.RequestException as e:
            _logger.error('Error de conexión con Superset: %s', str(e))
            raise Exception(f'Error de conexión: {str(e)}')
 
    def _get_dashboard_by_uuid(self, config, access_token, dashboard_uuid):
        try:
            search_url = f"{config['url']}/api/v1/dashboard/"
            params = {
                'q': f'(filters:!((col:uuid,opr:eq,value:{dashboard_uuid})))'
            }
            
            response = requests.get(
                search_url,
                params=params,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('result', [])
                if results:
                    return results[0]
                else:
                    _logger.warning('Dashboard con UUID %s no encontrado', dashboard_uuid)
                    return None
            else:
                _logger.error('Error buscando dashboard: HTTP %s', response.status_code)
                return None
                
        except Exception as e:
            _logger.error('Error buscando dashboard por UUID: %s', str(e))
            return None
 
    def _get_embedding_uuid(self, config, access_token, dashboard_id):
        try:
            embedding_url = f"{config['url']}/api/v1/dashboard/{dashboard_id}/embedded"
            
            response = requests.get(
                embedding_url,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=30
            )
            
            if response.status_code == 200:
                embedding_data = response.json()
                result = embedding_data.get('result')
                if result and result.get('uuid'):
                    embedding_uuid = result['uuid']
                    _logger.info('Embedding UUID obtenido: %s para dashboard %s', embedding_uuid, dashboard_id)
                    return embedding_uuid
                else:
                    _logger.warning('Dashboard %s no tiene embedding habilitado', dashboard_id)
                    return None
            elif response.status_code == 404:
                _logger.warning('Dashboard %s no tiene configuración de embedding', dashboard_id)
                return None
            else:
                _logger.error('Error obteniendo embedding config: HTTP %s', response.status_code)
                return None
                
        except Exception as e:
            _logger.error('Error obteniendo embedding UUID: %s', str(e))
            return None
 
    def _generate_guest_token(self, config, access_token, embedding_uuid):
        try:
            guest_token_url = f"{config['url']}/api/v1/security/guest_token/"
            
            guest_data = {
                'user': {
                    'username': f'odoo_user_{request.env.user.id}',
                    'first_name': request.env.user.name.split()[0] if request.env.user.name else 'Odoo',
                    'last_name': ' '.join(request.env.user.name.split()[1:]) if len(request.env.user.name.split()) > 1 else 'User'
                },
                'resources': [{
                    'type': 'dashboard',
                    'id': embedding_uuid
                }],
                'rls': []
            }
            
            _logger.info('Generando guest token para embedding UUID: %s', embedding_uuid)
            
            response = requests.post(
                guest_token_url,
                json=guest_data,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                guest_token = data.get('token')
                _logger.info('Guest token generado exitosamente')
                return guest_token
            else:
                error_detail = response.text
                _logger.error('Error generando guest token: HTTP %s - %s', response.status_code, error_detail)
                raise Exception(f'Error generando guest token: HTTP {response.status_code}')
                
        except requests.exceptions.RequestException as e:
            _logger.error('Error de conexión generando guest token: %s', str(e))
            raise Exception(f'Error de conexión: {str(e)}')
 
    @http.route('/superset/embed', type='json', auth='user', methods=['POST'])
    @require_superset_user
    def get_embed_data(self, dashboard_uuid=None):
        try:
            _logger.info('get_embed_data iniciado con dashboard_uuid: %s', dashboard_uuid)
            
            if not dashboard_uuid:
                return {
                    'success': False,
                    'error': 'No se especificó el UUID del dashboard'
                }
            
            config = self._get_superset_config()
            if not config:
                return {
                    'success': False,
                    'error': 'Configuración incompleta. Vaya a Configuración → Ajustes → Superset Integration'
                }
            
            _logger.info('Obteniendo access token para dashboard %s', dashboard_uuid)
            access_token = self._get_access_token(config)
            
            if not access_token:
                return {
                    'success': False,
                    'error': 'No se pudo obtener access token de Superset. Verifique las credenciales.'
                }
            
            _logger.info('Buscando dashboard por UUID: %s', dashboard_uuid)
            dashboard = self._get_dashboard_by_uuid(config, access_token, dashboard_uuid)
            if not dashboard:
                return {
                    'success': False,
                    'error': f'Dashboard con UUID {dashboard_uuid} no encontrado o no publicado'
                }
            
            _logger.info('Dashboard encontrado: ID=%s, Título=%s', dashboard['id'], dashboard.get('dashboard_title', 'Sin título'))
            
            embedding_uuid = self._get_embedding_uuid(config, access_token, dashboard['id'])
            if not embedding_uuid:
                return {
                    'success': False,
                    'error': 'Este dashboard no tiene embedding habilitado. Habilítelo en Superset UI.'
                }
            
            _logger.info('Embedding UUID obtenido: %s', embedding_uuid)
            
            _logger.info('Generando guest token para embedding UUID %s', embedding_uuid)
            guest_token = self._generate_guest_token(config, access_token, embedding_uuid)
            
            if not guest_token:
                return {
                    'success': False,
                    'error': 'No se pudo generar guest token. Verifique la configuración de embedding.'
                }
            
            result = {
                'success': True,
                'superset_url': config['url'],
                'dashboard_uuid': embedding_uuid,
                'guest_token': guest_token,
                'dashboard_title': dashboard.get('dashboard_title', 'Dashboard'),
                'dashboard_id': dashboard['id'],
                'original_dashboard_uuid': dashboard_uuid
            }
            
            _logger.info('Embed data generado exitosamente: %s', {
                'embedding_uuid': embedding_uuid,
                'dashboard_title': result['dashboard_title'],
                'has_guest_token': bool(guest_token)
            })
            
            return result
            
        except Exception as e:
            _logger.error('Error en /superset/embed: %s', str(e), exc_info=True)
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
 
    @http.route('/superset/dashboard/<string:dashboard_uuid>', type='http', auth='user', website=True)
    def dashboard_page(self, dashboard_uuid):
        try:
            _logger.info('Dashboard page solicitada - UUID: %s', dashboard_uuid)
            
            embed_data = self.get_embed_data(dashboard_uuid=dashboard_uuid)
            
            _logger.info('Embed data resultado: success=%s', embed_data.get('success'))
            if embed_data.get('success'):
                _logger.info('Embedding UUID a usar: %s', embed_data.get('dashboard_uuid'))
            
            if not embed_data.get('success'):
                return request.render('eticco_superset_integration.dashboard_error', {
                    'error': embed_data.get('error', 'Error desconocido')
                })
            
            return request.render('eticco_superset_integration.dashboard_page', {
                'superset_url': embed_data['superset_url'],
                'dashboard_uuid': embed_data['dashboard_uuid'],
                'guest_token': embed_data['guest_token'],
                'dashboard_title': embed_data['dashboard_title']
            })
            
        except Exception as e:
            _logger.error('Error en dashboard_page: %s', str(e))
            return request.render('eticco_superset_integration.dashboard_error', {
                'error': f'Error interno: {str(e)}'
            })

    @http.route('/superset/health', type='json', auth='user', methods=['GET'])
    @require_superset_user
    def check_health(self):
        try:
            config = self._get_superset_config()
            
            if not config:
                return {
                    'success': False,
                    'status': 'not_configured',
                    'error': 'Configuración de Superset no completada'
                }
            
            health_url = f"{config['url']}/health"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                try:
                    access_token = self._get_access_token(config)
                    return {
                        'success': True,
                        'status': 'healthy',
                        'url': config['url'],
                        'authenticated': bool(access_token)
                    }
                except Exception as auth_error:
                    return {
                        'success': False,
                        'status': 'auth_error',
                        'error': f'Error de autenticación: {str(auth_error)}'
                    }
            else:
                return {
                    'success': False,
                    'status': 'unreachable',
                    'error': f'Superset respondió HTTP {response.status_code}'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'status': 'connection_error',
                'error': f'Error de conexión: {str(e)}'
            }
        except Exception as e:
            _logger.error('Error en /superset/health: %s', str(e))
            return {
                'success': False,
                'status': 'error',
                'error': f'Error interno: {str(e)}'
            }

    @http.route('/superset/dashboards', type='json', auth='user', methods=['GET'])
    @require_superset_user
    def get_dashboards_list(self):
        try:
            config = self._get_superset_config()
            if not config:
                return {
                    'success': False,
                    'error': 'Configuración de Superset incompleta'
                }
            
            access_token = self._get_access_token(config)
            
            dashboards_url = f"{config['url']}/api/v1/dashboard/"
            params = {'q': '(page:0,page_size:100)'}
            
            response = requests.get(
                dashboards_url,
                params=params,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Error obteniendo dashboards: HTTP {response.status_code}'
                }
            
            data = response.json()
            dashboards = data.get('result', [])
            
            published_dashboards = []
            for dashboard in dashboards:
                if dashboard.get('published'):
                    embedding_uuid = self._get_embedding_uuid(config, access_token, dashboard['id'])
                    
                    published_dashboards.append({
                        'id': dashboard.get('id'),
                        'uuid': dashboard.get('uuid'),
                        'title': dashboard.get('dashboard_title', 'Sin título'),
                        'description': dashboard.get('description', ''),
                        'url': dashboard.get('url', ''),
                        'embedding_enabled': bool(embedding_uuid),
                        'embedding_uuid': embedding_uuid,
                        'changed_on': dashboard.get('changed_on'),
                        'owners': [owner.get('username', '') for owner in dashboard.get('owners', [])],
                    })
            
            return {
                'success': True,
                'dashboards': published_dashboards,
                'total': len(published_dashboards),
                'with_embedding': len([d for d in published_dashboards if d['embedding_enabled']])
            }
            
        except Exception as e:
            _logger.error('Error en /superset/dashboards: %s', str(e))
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }

    @http.route('/superset/config', type='json', auth='user', methods=['GET'])
    def get_config_status(self):
        try:
            is_manager = request.env.user.has_group('eticco_superset_integration.group_superset_manager')
            
            config = self._get_superset_config()
            
            result = {
                'configured': bool(config),
                'superset_available': False,
                'dashboards_count': 0,
                'embedding_count': 0
            }
            
            if is_manager and config:
                result.update({
                    'url': config.get('url', ''),
                    'username': config.get('username', ''),
                })
                
                try:
                    health_url = f"{config['url']}/health"
                    response = requests.get(health_url, timeout=10)
                    result['superset_available'] = response.status_code == 200
                    
                    if result['superset_available']:
                        dashboards_response = self.get_dashboards_list()
                        if dashboards_response.get('success'):
                            result['dashboards_count'] = dashboards_response.get('total', 0)
                            result['embedding_count'] = dashboards_response.get('with_embedding', 0)
                            
                except Exception:
                    pass
            
            return result
            
        except Exception as e:
            _logger.error('Error en /superset/config: %s', str(e))
            return {'error': str(e)}

    @http.route('/superset/cache/clear', type='json', auth='user', methods=['POST'])
    def clear_token_cache(self):
        try:
            if not request.env.user.has_group('eticco_superset_integration.group_superset_manager'):
                return {'success': False, 'error': 'Sin permisos'}
            
            self._access_token_cache.clear()
            _logger.info('Cache de tokens limpiado por usuario %s', request.env.user.name)
            
            return {
                'success': True,
                'message': 'Cache de tokens limpiado exitosamente'
            }
            
        except Exception as e:
            _logger.error('Error limpiando cache: %s', str(e))
            return {
                'success': False,
                'error': f'Error: {str(e)}'
            }