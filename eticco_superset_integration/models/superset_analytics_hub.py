# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class SupersetAnalyticsHub(models.Model):
    """Hub principal de Analytics - Combina selección y visualización"""
    _name = 'superset.analytics.hub'
    _description = 'Hub de Analytics Superset'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Nombre',
        default='Analytics Dashboard',
        readonly=True
    )
   
    selected_dashboard = fields.Selection(
        selection='_get_dashboard_selection',
        string='Dashboard Activo',
        help='Dashboard que se está visualizando actualmente'
    )
   
    dashboard_loaded = fields.Boolean(
        string='Dashboard Cargado',
        default=False,
        help='Indica si hay un dashboard cargado'
    )
    current_dashboard_id = fields.Integer(
        string='ID Dashboard',
        readonly=True
    )
    
    current_embedding_uuid = fields.Char(
        string='Embedding UUID',
        readonly=True  
    )
    
    current_dashboard_title = fields.Char(
        string='Título Dashboard',
        readonly=True,
        compute='_compute_dashboard_info'
    )
    
    current_dashboard_info = fields.Text(
        string='Información Dashboard',
        readonly=True,
        compute='_compute_dashboard_info'
    )
    
    has_configuration = fields.Boolean(
        string='Configurado',
        compute='_compute_system_status'
    )
    
    available_dashboards_count = fields.Integer(
        string='Dashboards Disponibles',
        compute='_compute_system_status'
    )

    @api.depends('selected_dashboard')
    def _compute_dashboard_info(self):
        """Computar información del dashboard seleccionado"""
        for record in self:
            if record.selected_dashboard and record.selected_dashboard not in ['no_config', 'no_dashboards', 'error']:
                try:
                    utils = self.env['superset.utils']
                    config = utils.get_superset_config()
                    utils.validate_config(config)
                    access_token = utils.get_access_token(config)
                    
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
                        dashboards = data.get('result', [])
                        
                        dashboard = next((d for d in dashboards if d.get('uuid') == record.selected_dashboard), None)
                        
                        if dashboard:
                            record.current_dashboard_title = dashboard.get('dashboard_title', 'Sin título')
                            record.current_dashboard_id = dashboard.get('id')
                            
                            try:
                                embedding_url = f"{config['url']}/api/v1/dashboard/{dashboard.get('id')}/embedded"
                                embedding_response = requests.get(
                                    embedding_url,
                                    headers={'Authorization': f'Bearer {access_token}'},
                                    timeout=config.get('timeout', 30)
                                )
                                if embedding_response.status_code == 200:
                                    embedding_data = embedding_response.json()
                                    record.current_embedding_uuid = embedding_data.get('result', {}).get('uuid')
                                else:
                                    record.current_embedding_uuid = False
                            except:
                                record.current_embedding_uuid = False
                                
                            record.current_dashboard_info = f"""Título: {dashboard.get('dashboard_title', 'N/A')}
                                                    Descripción: {dashboard.get('description', 'Sin descripción')}
                                                    Embedding: {'✅ Habilitado' if record.current_embedding_uuid else '❌ Deshabilitado'}
                                                    Propietarios: {', '.join([owner.get('username', '') for owner in dashboard.get('owners', [])])}"""
                        else:
                            record._reset_dashboard_info()
                    else:
                        record._reset_dashboard_info()
                except Exception as e:
                    _logger.error('Error obteniendo info dashboard: %s', str(e))
                    record._reset_dashboard_info()
            else:
                record._reset_dashboard_info()

    def _reset_dashboard_info(self):
        """Reset información del dashboard"""
        self.current_dashboard_title = ''
        self.current_dashboard_id = False
        self.current_embedding_uuid = False
        self.current_dashboard_info = ''

    def _compute_system_status(self):
        """Computar estado del sistema usando lógica centralizada optimizada"""
        for record in self:
            try:
                utils = self.env['superset.utils']
                # Usar método unificado sin forzar refresh (usa cache)
                status = utils.get_system_status(force_refresh=False)
                
                record.has_configuration = status.get('has_configuration', False)
                record.available_dashboards_count = status.get('with_embedding', 0)
                
            except Exception as e:
                _logger.debug('Error calculando estado del sistema: %s', str(e))
                record.has_configuration = False
                record.available_dashboards_count = 0

    def _get_dashboard_selection(self):
        """Obtener opciones de dashboard disponibles"""
        try:
            utils = self.env['superset.utils']
            config = utils.get_superset_config()
            
            if not all([config.get('url'), config.get('username'), config.get('password')]):
                return [('no_config', '⚠️ Configurar Superset en Ajustes')]
            
            try:
                utils.validate_config(config)
                access_token = utils.get_access_token(config)
                
                dashboards_url = f"{config['url']}/api/v1/dashboard/"
                params = {'q': '(page:0,page_size:100)'}
                
                response = requests.get(
                    dashboards_url,
                    params=params,
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=config.get('timeout', 30)
                )
                
                if response.status_code != 200:
                    return [('error', f'❌ Error HTTP: {response.status_code}')]
                    
                data = response.json()
                dashboards = [d for d in data.get('result', []) if d.get('published')]
                
                if not dashboards:
                    return [('no_dashboards', '❌ No hay dashboards publicados')]
                
                selection = []
                
                for dashboard in dashboards:
                    try:
                        embedding_url = f"{config['url']}/api/v1/dashboard/{dashboard.get('id')}/embedded"
                        embedding_response = requests.get(
                            embedding_url,
                            headers={'Authorization': f'Bearer {access_token}'},
                            timeout=config.get('timeout', 30)
                        )
                        
                        embedding_enabled = False
                        if embedding_response.status_code == 200:
                            embedding_data = embedding_response.json()
                            embedding_uuid = embedding_data.get('result', {}).get('uuid')
                            embedding_enabled = bool(embedding_uuid)
                        
                        dashboard_title = dashboard.get('dashboard_title', 'Sin título')
                        dashboard_uuid = dashboard.get('uuid')
                        
                        # SOLO añadir dashboards que tienen embedding habilitado
                        if embedding_enabled:
                            selection.append((dashboard_uuid, f"📊 {dashboard_title}"))
                            
                    except Exception as e:
                        _logger.error('Error verificando embedding para dashboard %s: %s', 
                                    dashboard.get('id'), str(e))
                        # No añadir dashboards con errores al selector
                
                if not selection:
                    return [('no_dashboards', '❌ No hay dashboards con embedding disponibles')]
                    
                # Ordenar por título (todos tienen embedding ya)
                selection.sort(key=lambda x: x[1])
                return selection
                
            except Exception as e:
                _logger.error('Error obteniendo dashboards para hub: %s', str(e))
                return [('error', f'❌ Error: {str(e)[:50]}...')]
        
        except Exception as e:
            _logger.error('Error en _get_dashboard_selection: %s', str(e))
            return [('error', f'❌ Error: {str(e)[:50]}...')]

    def _get_superset_config(self):
        """Obtener configuración de Superset"""
        return self.env['superset.utils'].get_superset_config()

    @api.onchange('selected_dashboard')
    def _onchange_selected_dashboard(self):
        """Al cambiar dashboard, actualizar estado"""
        if self.selected_dashboard and self.selected_dashboard not in ['no_config', 'no_dashboards', 'error']:
            self.dashboard_loaded = True
        else:
            self.dashboard_loaded = False
            self._reset_dashboard_info()

    def action_load_dashboard(self):
        """Cargar/actualizar dashboard seleccionado"""
        self.ensure_one()
        
        if not self.selected_dashboard or self.selected_dashboard in ['no_config', 'no_dashboards', 'error']:
            raise UserError(_('Selecciona un dashboard válido'))
            
        try:
            utils = self.env['superset.utils']
            
            # Refrescar información
            self._compute_dashboard_info()
            
            # Validar datos del dashboard
            dashboard_data = {
                'id': self.current_dashboard_id,
                'uuid': self.selected_dashboard,
                'title': self.current_dashboard_title,
                'embedding_enabled': bool(self.current_embedding_uuid),
                'embedding_uuid': self.current_embedding_uuid
            }
            
            utils.validate_embedding_requirements(dashboard_data)
            
            self.dashboard_loaded = True
            
            utils.log_debug(f'Dashboard cargado exitosamente: {self.current_dashboard_title}')
            
            return utils.create_user_notification(
                _('Dashboard cargado'),
                _(f'Dashboard "{self.current_dashboard_title}" listo para visualización'),
                'success'
            )
            
        except (ValidationError, UserError):
            # Re-raise user errors
            raise
        except Exception as e:
            _logger.error('Error inesperado cargando dashboard: %s', str(e))
            raise UserError(_(f'Error inesperado: {str(e)}'))

    def action_refresh_dashboards(self):
        """Refrescar lista de dashboards"""
        self.ensure_one()
        
        try:
            # Limpiar selección actual
            self.selected_dashboard = False
            self.dashboard_loaded = False
            self._reset_dashboard_info()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            
        except Exception as e:
            _logger.error('Error refrescando: %s', str(e))
            raise UserError(_(f'Error: {str(e)}'))

    def action_open_settings(self):
        """Abrir configuración de Superset"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configuración Superset',
            'res_model': 'res.config.settings',
            'view_mode': 'form',
            'target': 'new',  # Cambiar a 'new' para abrir en modal
            'context': {
                'module': 'eticco_superset_integration',
                'default_module': 'eticco_superset_integration',
                'hub_id': self.id  # Pasar ID del hub para refrescar después
            }
        }

    def get_embedding_url(self):
        """Obtener URL para embedding del dashboard actual"""
        self.ensure_one()
        
        if not self.dashboard_loaded or not self.current_dashboard_id:
            return None
            
        return f"/superset/dashboard/{self.current_dashboard_id}"

    def get_dashboard_data_for_js(self):
        """Obtener datos del dashboard para JavaScript/OWL con manejo profesional de errores"""
        self.ensure_one()
        
        if not self.selected_dashboard or self.selected_dashboard in ['no_config', 'no_dashboards', 'error']:
            return {
                'error': 'No hay dashboard seleccionado',
                'error_type': 'selection_error',
                'user_message': 'Selecciona un dashboard válido del menú desplegable'
            }
            
        try:
            # Obtener configuración
            utils = self.env['superset.utils']
            config = utils.get_superset_config()
            utils.validate_config(config)
            
            # Obtener token con manejo de errores específicos
            try:
                access_token = utils.get_access_token(config)
            except Exception as auth_error:
                error_msg = str(auth_error)
                if '401' in error_msg or 'Unauthorized' in error_msg:
                    return {
                        'error': 'Credenciales incorrectas o expiradas',
                        'error_type': 'auth_error',
                        'user_message': 'Las credenciales de Superset han caducado o son incorrectas. Verifica la configuración en Ajustes.',
                        'action_required': 'check_credentials'
                    }
                elif '403' in error_msg or 'Forbidden' in error_msg:
                    return {
                        'error': 'Sin permisos suficientes',
                        'error_type': 'permission_error',
                        'user_message': 'El usuario no tiene permisos para acceder a Superset. Contacta al administrador.',
                        'action_required': 'contact_admin'
                    }
                else:
                    return {
                        'error': 'Error de autenticación',
                        'error_type': 'auth_error', 
                        'user_message': 'No se pudo autenticar con Superset. Verifica que el servidor esté funcionando.',
                        'action_required': 'check_connection'
                    }
            
            # Buscar el dashboard con manejo de errores de conectividad
            dashboards_url = f"{config['url']}/api/v1/dashboard/"
            params = {'q': '(page:0,page_size:100)'}
            
            try:
                response = requests.get(
                    dashboards_url,
                    params=params,
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=config.get('timeout', 30)
                )
            except requests.exceptions.ConnectionError:
                return {
                    'error': 'Servidor no disponible',
                    'error_type': 'connection_error',
                    'user_message': 'No se puede conectar al servidor de Superset. Verifica que esté en línea y accesible.',
                    'action_required': 'check_server'
                }
            except requests.exceptions.Timeout:
                return {
                    'error': 'Timeout de conexión',
                    'error_type': 'timeout_error',
                    'user_message': 'El servidor de Superset no responde. El servidor puede estar sobrecargado.',
                    'action_required': 'retry_later'
                }
            except requests.exceptions.RequestException as req_error:
                return {
                    'error': 'Error de red',
                    'error_type': 'network_error',
                    'user_message': f'Error de conectividad: {str(req_error)[:100]}...',
                    'action_required': 'check_network'
                }
            
            if response.status_code == 401:
                return {
                    'error': 'Token expirado',
                    'error_type': 'token_expired',
                    'user_message': 'La sesión ha caducado. Intenta recargar la página.',
                    'action_required': 'refresh_page'
                }
            elif response.status_code == 403:
                return {
                    'error': 'Sin permisos',
                    'error_type': 'permission_denied',
                    'user_message': 'Sin permisos para acceder a los dashboards. Contacta al administrador.',
                    'action_required': 'contact_admin'
                }
            elif response.status_code == 500:
                return {
                    'error': 'Error del servidor',
                    'error_type': 'server_error',
                    'user_message': 'Error interno del servidor de Superset. Intenta más tarde.',
                    'action_required': 'retry_later'
                }
            elif response.status_code != 200:
                return {
                    'error': f'Error HTTP {response.status_code}',
                    'error_type': 'http_error',
                    'user_message': f'El servidor respondió con error {response.status_code}. Intenta más tarde.',
                    'action_required': 'retry_later'
                }
            
            data = response.json()
            dashboards = data.get('result', [])
            
            # Buscar el dashboard por UUID
            dashboard = None
            for d in dashboards:
                if d.get('uuid') == self.selected_dashboard:
                    dashboard = d
                    break
                    
            if not dashboard:
                return {
                    'error': 'Dashboard no encontrado',
                    'error_type': 'dashboard_not_found',
                    'user_message': 'El dashboard seleccionado ya no existe o no es accesible.',
                    'action_required': 'select_different'
                }
            
            # Obtener embedding UUID con manejo de errores
            embedding_url = f"{config['url']}/api/v1/dashboard/{dashboard.get('id')}/embedded"
            
            try:
                embedding_response = requests.get(
                    embedding_url,
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=config.get('timeout', 30)
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as conn_error:
                return {
                    'error': 'Error verificando embedding',
                    'error_type': 'embedding_check_error',
                    'user_message': 'No se pudo verificar si el dashboard tiene embedding habilitado.',
                    'action_required': 'retry'
                }
            
            if embedding_response.status_code != 200:
                return {
                    'error': 'Dashboard sin embedding',
                    'error_type': 'embedding_disabled',
                    'user_message': 'Este dashboard no tiene embedding habilitado. Contacta al administrador.',
                    'action_required': 'contact_admin'
                }
            
            embedding_data = embedding_response.json()
            embedding_uuid = embedding_data.get('result', {}).get('uuid')
            
            if not embedding_uuid:
                return {
                    'error': 'UUID de embedding no disponible',
                    'error_type': 'embedding_uuid_missing',
                    'user_message': 'El dashboard no está correctamente configurado para embedding.',
                    'action_required': 'contact_admin'
                }
            
            # Actualizar campos del record
            self.current_dashboard_id = dashboard.get('id')
            self.current_dashboard_title = dashboard.get('dashboard_title', 'Sin título')
            self.current_embedding_uuid = embedding_uuid
            
            # Generar guest token con manejo de errores
            guest_token_url = f"{config['url']}/api/v1/security/guest_token/"
            guest_data = {
                'user': {
                    'username': 'guest_user',
                    'first_name': 'Guest',
                    'last_name': 'User'
                },
                'resources': [{
                    'type': 'dashboard',
                    'id': embedding_uuid
                }],
                'rls': []
            }
            
            try:
                token_response = requests.post(
                    guest_token_url,
                    json=guest_data,
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    },
                    timeout=config.get('timeout', 30)
                )
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                return {
                    'error': 'Error generando token de acceso',
                    'error_type': 'guest_token_error',
                    'user_message': 'No se pudo generar el token de acceso. El servidor puede estar sobrecargado.',
                    'action_required': 'retry_later'
                }
            
            if token_response.status_code != 200:
                error_detail = ''
                try:
                    error_data = token_response.json()
                    error_detail = error_data.get('message', '')
                except:
                    error_detail = f'HTTP {token_response.status_code}'
                
                return {
                    'error': 'Error de autorización',
                    'error_type': 'guest_token_failed',
                    'user_message': f'No se pudo autorizar el acceso al dashboard: {error_detail}',
                    'action_required': 'contact_admin'
                }
            
            guest_token = token_response.json().get('token')
            
            if not guest_token:
                return {
                    'error': 'Token de acceso inválido',
                    'error_type': 'invalid_guest_token',
                    'user_message': 'No se pudo obtener un token válido para acceder al dashboard.',
                    'action_required': 'retry'
                }
            
            self.dashboard_loaded = True
            
            return {
                'embedding_uuid': embedding_uuid,
                'guest_token': guest_token,
                'superset_domain': config['url'],
                'dashboard_title': dashboard.get('dashboard_title', 'Sin título'),
                'dashboard_id': dashboard.get('id'),
                'debug_mode': config.get('debug_mode', False),
                'success': True
            }
            
        except ValidationError as val_error:
            return {
                'error': 'Error de configuración',
                'error_type': 'config_error',
                'user_message': f'Configuración inválida: {str(val_error)}',
                'action_required': 'check_config'
            }
        except Exception as e:
            _logger.error('Error inesperado obteniendo datos para JS: %s', str(e))
            return {
                'error': 'Error interno',
                'error_type': 'unexpected_error',
                'user_message': 'Ha ocurrido un error inesperado. Intenta recargar la página.',
                'action_required': 'reload_page',
                'technical_details': str(e) if self.env.user.has_group('base.group_system') else None
            }

    def refresh_dashboard_options(self):
        """Refrescar opciones de dashboard (método público para llamadas desde JS)"""
        self.ensure_one()
        
        _logger.info('🔍 [TIMING] refresh_dashboard_options() - has_configuration inicial: %s', self.has_configuration)
        
        # Forzar recálculo de campos computados
        self._compute_system_status()
        
        _logger.info('✅ [TIMING] refresh_dashboard_options() - has_configuration después: %s', self.has_configuration)
        
        # Forzar la re-evaluación de las opciones de dashboard
        options = self._get_dashboard_selection()
        valid_count = len([opt for opt in options if opt[0] not in ['no_config', 'no_dashboards', 'error']])
        
        result = {
            'options_refreshed': True,
            'available_options': valid_count,
            'has_configuration': self.has_configuration,
            'configuration_status': 'configured' if self.has_configuration else 'missing'
        }
        
        return result

    def force_refresh_configuration(self):
        """Método público para forzar recálculo completo desde configuración"""
        self.ensure_one()
        
        try:
            # Forzar recálculo completo con HTTP
            utils = self.env['superset.utils']
            status = utils.get_system_status(force_refresh=True)
            
            # Actualizar campos inmediatamente
            self.has_configuration = status.get('has_configuration', False)
            self.available_dashboards_count = status.get('with_embedding', 0)
            
            # Limpiar selección si no hay configuración válida
            if not self.has_configuration:
                self.selected_dashboard = False
                self.dashboard_loaded = False
                self._reset_dashboard_info()
            
            _logger.info(f"Configuración actualizada: has_configuration={self.has_configuration}, "
                        f"dashboards_count={self.available_dashboards_count}")
            
        except Exception as e:
            _logger.error('Error forzando refresh de configuración: %s', str(e))
            self.has_configuration = False
            self.available_dashboards_count = 0
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    @api.model
    def get_default_hub(self):
        """Obtener o crear hub por defecto"""
        hub = self.search([], limit=1)
        
        if not hub:
            hub = self.create({})
            _logger.info('🔍 [TIMING] get_default_hub() - Hub creado con ID: %s', hub.id)
        else:
            _logger.info('🔍 [TIMING] get_default_hub() - Hub existente ID: %s, has_configuration: %s', 
                        hub.id, hub.has_configuration)
        
        # Forzar el cálculo de campos computados para el hub
        hub._compute_system_status()
        
        _logger.info('✅ [TIMING] get_default_hub() - Después del cálculo has_configuration: %s', hub.has_configuration)
        
        return hub