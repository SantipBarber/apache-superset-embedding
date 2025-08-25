# -*- coding: utf-8 -*-
 
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import logging
import re
 
_logger = logging.getLogger(__name__)
 
 
class ResConfigSettings(models.TransientModel):
    """Configuración extendida de Superset en Settings"""
    _inherit = 'res.config.settings'
 
    # Campos de configuración de Superset
    superset_url = fields.Char(
        string='URL de Superset',
        config_parameter='superset.url',
        default='http://localhost:8088',
        help='URL base del servidor Superset (ej: http://localhost:8088)'
    )
    
    superset_username = fields.Char(
        string='Usuario',
        config_parameter='superset.username',
        default='admin',
        help='Usuario administrador de Superset'
    )
    
    superset_password = fields.Char(
        string='Contraseña',
        config_parameter='superset.password',
        default='admin',
        help='Contraseña del usuario administrador'
    )
    
    superset_timeout = fields.Integer(
        string='Timeout (segundos)',
        config_parameter='superset.timeout',
        default=30,
        help='Timeout para conexiones con Superset'
    )
    
    # Configuración del menú
    superset_menu_parent = fields.Many2one(
        'ir.ui.menu',
        string='Menú Padre para Dashboards',
        config_parameter='superset.menu_parent',
        help='Menú donde se creará el submenú de dashboards de Superset'
    )
    
    superset_menu_name = fields.Char(
        string='Nombre del Menú',
        config_parameter='superset.menu_name',
        default='Analytics',
        help='Nombre del menú que contendrá los dashboards'
    )
    
    # Configuración avanzada
    superset_debug_mode = fields.Boolean(
        string='Modo Debug',
        config_parameter='superset.debug_mode',
        default=False,
        help='Activar logging detallado para debugging'
    )
    
    superset_cache_tokens = fields.Boolean(
        string='Cache de Tokens',
        config_parameter='superset.cache_tokens',
        default=True,
        help='Cachear access tokens para mejorar performance'
    )
    
    # Campos informativos (solo lectura)
    superset_connection_status = fields.Char(
        string='Estado de Conexión',
        readonly=True,
        compute='_compute_connection_status'
    )
    
    superset_dashboards_count = fields.Integer(
        string='Dashboards Disponibles',
        readonly=True,
        compute='_compute_dashboards_info'
    )
    
    superset_embedding_count = fields.Integer(
        string='Con Embedding Habilitado',
        readonly=True,
        compute='_compute_dashboards_info'
    )
 
    @api.depends('superset_url', 'superset_username', 'superset_password')
    def _compute_connection_status(self):
        """Calcular estado de conexión dinámicamente"""
        for record in self:
            if not record.superset_url or not record.superset_username or not record.superset_password:
                record.superset_connection_status = 'Configuración incompleta'
            else:
                record.superset_connection_status = 'Configurado (usar Probar Conexión para verificar)'
 
    @api.depends('superset_url', 'superset_username', 'superset_password')
    def _compute_dashboards_info(self):
        """Obtener información de dashboards si es posible"""
        for record in self:
            record.superset_dashboards_count = 0
            record.superset_embedding_count = 0
            
            if record.superset_url and record.superset_username and record.superset_password:
                try:
                    # Llamar al endpoint interno para obtener stats
                    dashboards_info = self._get_dashboards_stats()
                    record.superset_dashboards_count = dashboards_info.get('total', 0)
                    record.superset_embedding_count = dashboards_info.get('with_embedding', 0)
                except:
                    pass  # Ignorar errores al calcular
 
    def _get_dashboards_stats(self):
        """Obtener estadísticas básicas de dashboards"""
        try:
            # Usar el controlador interno
            result = self.env['ir.http']._dispatch('/superset/dashboards')
 
            
            if result.get('success'):
                return {
                    'total': result.get('total', 0),
                    'with_embedding': result.get('with_embedding', 0)
                }
        except Exception as e:
            _logger.debug('Error obteniendo stats de dashboards: %s', str(e))
        
        return {'total': 0, 'with_embedding': 0}
 
    def test_superset_connection(self):
        """Probar conexión con Superset - MEJORADO"""
        self.ensure_one()
        
        if not self.superset_url or not self.superset_username or not self.superset_password:
            raise ValidationError(_('Complete todos los campos de conexión primero.'))
        
        try:
            # Validar URL
            if not re.match(r'^https?://', self.superset_url):
                raise ValidationError(_('La URL debe comenzar con http:// o https://'))
            
            superset_url = self.superset_url.rstrip('/')
            timeout = self.superset_timeout or 30
            
            # 1. Probar endpoint de salud
            health_url = f"{superset_url}/health"
            response = requests.get(health_url, timeout=timeout)
            
            if response.status_code != 200:
                raise ValidationError(_(f'Superset no disponible. Código HTTP: {response.status_code}'))
            
            # 2. Probar autenticación
            login_url = f"{superset_url}/api/v1/security/login"
            login_data = {
                'username': self.superset_username,
                'password': self.superset_password,
                'provider': 'db'
            }
            
            auth_response = requests.post(
                login_url,
                json=login_data,
                headers={'Content-Type': 'application/json'},
                timeout=timeout
            )
            
            if auth_response.status_code == 200:
                token_data = auth_response.json()
                access_token = token_data.get('access_token')
                
                if access_token:
                    # 3. Probar acceso a API de dashboards
                    dashboards_url = f"{superset_url}/api/v1/dashboard/"
                    dashboard_response = requests.get(
                        dashboards_url,
                        headers={'Authorization': f'Bearer {access_token}'},
                        timeout=timeout
                    )
                    
                    if dashboard_response.status_code == 200:
                        dashboard_data = dashboard_response.json()
                        dashboard_count = len(dashboard_data.get('result', []))
                        
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('✅ Conexión exitosa'),
                                'message': _(f'Conectado correctamente. Se encontraron {dashboard_count} dashboards.'),
                                'type': 'success',
                                'sticky': False,
                            }
                        }
                    else:
                        raise ValidationError(_('Token válido pero sin acceso a dashboards. Verifique permisos.'))
                else:
                    raise ValidationError(_('Respuesta de login sin access_token'))
                    
            elif auth_response.status_code == 401:
                raise ValidationError(_('Usuario o contraseña incorrectos'))
            elif auth_response.status_code == 403:
                raise ValidationError(_('Usuario sin permisos suficientes'))
            else:
                error_detail = auth_response.text[:200] if auth_response.text else 'Sin detalles'
                raise ValidationError(_(f'Error de autenticación: HTTP {auth_response.status_code} - {error_detail}'))
                
        except requests.exceptions.ConnectionError:
            raise ValidationError(_('No se puede conectar al servidor Superset. Verifica la URL y conectividad.'))
        except requests.exceptions.Timeout:
            raise ValidationError(_(f'Timeout al conectar con Superset después de {timeout}s. El servidor no responde.'))
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            _logger.error('Error inesperado probando conexión Superset: %s', str(e))
            raise ValidationError(_(f'Error inesperado: {str(e)}'))
 
    def open_superset_dashboards(self):
        """Abrir lista de dashboards de Superset"""
        self.ensure_one()
        
        try:
            # Llamar endpoint para obtener dashboards
            dashboards_response = self.env['ir.http']._dispatch('/superset/dashboards')
            
            if not dashboards_response.get('success'):
                raise UserError(_(f"Error obteniendo dashboards: {dashboards_response.get('error', 'Error desconocido')}"))
            
            dashboards = dashboards_response.get('dashboards', [])
            
            if not dashboards:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sin dashboards'),
                        'message': _('No se encontraron dashboards publicados en Superset.'),
                        'type': 'warning',
                    }
                }
            
            # Mostrar lista en una ventana
            message_lines = ['Dashboards encontrados:', '']
            
            for dashboard in dashboards[:10]:  # Mostrar solo los primeros 10
                embedding_status = "✅" if dashboard.get('embedding_enabled') else "❌"
                message_lines.append(f"{embedding_status} {dashboard.get('title', 'Sin título')}")
            
            if len(dashboards) > 10:
                message_lines.append(f'... y {len(dashboards) - 10} más')
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _(f'📊 {len(dashboards)} Dashboards Encontrados'),
                    'message': '\n'.join(message_lines),
                    'type': 'info',
                    'sticky': True,
                }
            }
            
        except Exception as e:
            _logger.error('Error abriendo dashboards: %s', str(e))
            raise UserError(_(f'Error: {str(e)}'))
 
    def clear_superset_cache(self):
        """Limpiar cache de tokens"""
        self.ensure_one()
        
        try:
            # Llamar endpoint para limpiar cache
            cache_response = self.env['ir.http']._dispatch('/superset/cache/clear')
            
            if cache_response.get('success'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Cache limpiado'),
                        'message': _('El cache de tokens de Superset ha sido limpiado.'),
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_(cache_response.get('error', 'Error limpiando cache')))
                
        except Exception as e:
            _logger.error('Error limpiando cache: %s', str(e))
            raise UserError(_(f'Error: {str(e)}'))
 
    def create_dashboard_menu(self):
        """Crear el menú de dashboards en la ubicación especificada"""
        self.ensure_one()
        
        if not self.superset_menu_parent:
            raise ValidationError(_('Selecciona un menú padre primero.'))
        
        menu_name = self.superset_menu_name or 'Analytics'
        
        # Buscar si ya existe el menú
        existing_menu = self.env['ir.ui.menu'].search([
            ('name', '=', menu_name),
            ('parent_id', '=', self.superset_menu_parent.id)
        ])
        
        if existing_menu:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Menú ya existe'),
                    'message': _(f'El menú "{menu_name}" ya existe en la ubicación seleccionada.'),
                    'type': 'warning',
                }
            }
        
        # Crear acción para el dashboard selector
        action = self.env['ir.actions.act_window'].create({
            'name': f'{menu_name} - Dashboard Selector',
            'res_model': 'superset.dashboard.selector',
            'view_mode': 'form',
            'target': 'current',
            'context': "{}",
        })
        
        # Crear el menú
        menu = self.env['ir.ui.menu'].create({
            'name': menu_name,
            'parent_id': self.superset_menu_parent.id,
            'action': f'ir.actions.act_window,{action.id}',
            'sequence': 99,
        })
        
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Menú creado'),
                'message': _(f'El menú "{menu_name}" se creó exitosamente bajo "{self.superset_menu_parent.name}".'),
                'type': 'success',
            }
        }
 
    @api.constrains('superset_url')
    def _check_superset_url(self):
        """Validar formato de URL"""
        for record in self:
            if record.superset_url:
                if not record.superset_url.startswith(('http://', 'https://')):
                    raise ValidationError(_('La URL debe empezar con http:// o https://'))
                
                # Validar que no tenga espacios
                if ' ' in record.superset_url:
                    raise ValidationError(_('La URL no puede contener espacios'))
 
    @api.constrains('superset_timeout')
    def _check_timeout(self):
        """Validar timeout"""
        for record in self:
            if record.superset_timeout and (record.superset_timeout < 5 or record.superset_timeout > 300):
                raise ValidationError(_('El timeout debe estar entre 5 y 300 segundos'))
 
 
class SupersetDashboardSelector(models.Model):
    """Modelo mejorado para el selector de dashboards"""
    _name = 'superset.dashboard.selector'
    _description = 'Selector de Dashboards de Superset'
    _rec_name = 'display_name'
 
    display_name = fields.Char(
        string='Nombre',
        default='Analytics Dashboard',
        readonly=True
    )
    
    selected_dashboard = fields.Selection(
        selection='_get_dashboard_selection',
        string='Dashboard Seleccionado',
        help='Selecciona el dashboard que quieres visualizar'
    )
    
    dashboard_info = fields.Text(
        string='Información del Dashboard',
        readonly=True,
        compute='_compute_dashboard_info'
    )
 
    @api.depends('selected_dashboard')
    def _compute_dashboard_info(self):
        """Calcular información del dashboard seleccionado"""
        for record in self:
            _logger.info(f"Compute_dashboard_info: {record}")
            if record.selected_dashboard and record.selected_dashboard not in ['no_config', 'no_dashboards', 'error']:
                try:
                    # Obtener información del dashboard
                    dashboards = self._fetch_dashboards_from_superset()
                    selected = next((d for d in dashboards if d.get('uuid') == record.selected_dashboard), None)
                    
                    if selected:
                        info_lines = [
                            f"Título: {selected.get('title', 'N/A')}",
                            f"Descripción: {selected.get('description', 'Sin descripción')}",
                            f"Embedding: {'✅ Habilitado' if selected.get('embedding_enabled') else '❌ Deshabilitado'}",
                            f"Propietarios: {', '.join(selected.get('owners', []))}"
                        ]
                        record.dashboard_info = '\n'.join(info_lines)
                    else:
                        record.dashboard_info = 'Dashboard no encontrado'
                except:
                    record.dashboard_info = 'Error obteniendo información'
            else:
                record.dashboard_info = ''
 
    def _get_dashboard_selection(self):
        try:
            config = self._get_superset_config()
            if not config.get('url'):
                return [('no_config', 'Sin configurar - Ir a Ajustes')]
            
            dashboards = self._fetch_dashboards_from_superset(config)
            
            selection = []
            for dashboard in dashboards:
                _logger.info('Dashboard procesado: %s - UUID: %s - Embedding: %s', 
                            dashboard.get('title'), dashboard.get('uuid'), dashboard.get('embedding_enabled'))
                
                dashboard_uuid = dashboard.get('uuid', '')
                title = dashboard.get('title', 'Sin título')
                
                if dashboard.get('embedding_enabled'):  
                    selection.append((
                        dashboard_uuid,
                        f"✅ {title}"
                    ))
                else:
                    selection.append((
                        dashboard_uuid,
                        f"❌ {title} (sin embedding)"
                    ))
            
            if not selection:
                selection = [('no_dashboards', 'No hay dashboards con embedding habilitado')]
                
            _logger.info('Selection final: %s dashboards', len(selection))
            return selection
            
        except Exception as e:
            _logger.error('Error obteniendo dashboards: %s', str(e))
            return [('error', f'Error: {str(e)[:50]}...')]
 
    def _get_superset_config(self):
        """Obtener configuración actual de Superset"""
        ICPSudo = self.env['ir.config_parameter'].sudo()
        return {
            'url': ICPSudo.get_param('superset.url', '').rstrip('/'),
            'username': ICPSudo.get_param('superset.username', ''),
            'password': ICPSudo.get_param('superset.password', ''),
            'timeout': int(ICPSudo.get_param('superset.timeout', '30')),
        }
 
    def _fetch_dashboards_from_superset(self, config=None):
        """Obtener dashboards desde Superset API"""
        if not config:
            config = self._get_superset_config()
            
        try:
            # Login
            login_url = f"{config['url']}/api/v1/security/login"
            login_data = {
                'username': config['username'],
                'password': config['password'],
                'provider': 'db'
            }
            
            response = requests.post(
                login_url,
                json=login_data,
                timeout=config.get('timeout', 30)
            )
            
            if response.status_code != 200:
                _logger.error('Error login: HTTP %s', response.status_code)
                return []
            
            access_token = response.json().get('access_token')
            if not access_token:
                _logger.error('Login sin access_token')
                return []
            
            # Obtener dashboards
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
                
                # Verificar embedding para cada dashboard
                result = []
                for dashboard in dashboards:
                    if dashboard.get('published'):
                        # Verificar embedding
                        embedding_enabled = self._check_dashboard_embedding(
                            config, access_token, dashboard['id']
                        )
                        
                        result.append({
                            'id': dashboard.get('id'),
                            'uuid': dashboard.get('uuid'),
                            'title': dashboard.get('dashboard_title', 'Sin título'),
                            'description': dashboard.get('description', ''),
                            'url': dashboard.get('url', ''),
                            'embedding_enabled': embedding_enabled,
                            'owners': [owner.get('username', '') for owner in dashboard.get('owners', [])],
                            'changed_on': dashboard.get('changed_on'),
                        })
                _logger.info(f"Resultado {result}")
                return result
            else:
                _logger.error('Error obteniendo dashboards: HTTP %s', response.status_code)
                return []
            
        except Exception as e:
            _logger.error('Error fetching dashboards: %s', str(e))
            return []
 
    def _check_dashboard_embedding(self, config, access_token, dashboard_id):
        """Verificar si un dashboard tiene embedding habilitado"""
        try:
            embedding_url = f"{config['url']}/api/v1/dashboard/{dashboard_id}/embedded"
            response = requests.get(
                embedding_url,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=config.get('timeout', 30)
            )
            
            if response.status_code == 200:
                data = response.json()
                return bool(data.get('result', {}).get('uuid'))
            
            return False
            
        except Exception as e:
            _logger.debug('Error verificando embedding para dashboard %s: %s', dashboard_id, str(e))
            return False
 
    def action_view_dashboard(self):
        """Abrir dashboard seleccionado en vista completa"""
        self.ensure_one()
        
        if not self.selected_dashboard or self.selected_dashboard in ['no_config', 'no_dashboards', 'error']:
            raise ValidationError(_('Selecciona un dashboard válido primero.'))
        
        _logger.info(f"Action_view_dashboard: {self.selected_dashboard}")
        # Retornar acción para vista de dashboard
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dashboard Analytics',
            'res_model': 'superset.dashboard.viewer',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_dashboard_uuid': self.selected_dashboard,
            },
        }
 
    def action_refresh_dashboards(self):
        """Actualizar lista de dashboards"""
        self.ensure_one()
        
        try:
            # Limpiar cache si está habilitado
            self.env['ir.http']._dispatch('/superset/cache/clear')
            
            # Refrescar vista
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            
        except Exception as e:
            _logger.error('Error refrescando dashboards: %s', str(e))
            raise UserError(_(f'Error actualizando: {str(e)}'))
 
 
class SupersetDashboardViewer(models.TransientModel):
    """Modelo mejorado para vista completa del dashboard"""
    _name = 'superset.dashboard.viewer'
    _description = 'Visor de Dashboard de Superset'
 
    dashboard_uuid = fields.Char(
        string='UUID del Dashboard',
        required=True
    )
    #!Cambio
    dashboard_id = fields.Char(
        string='ID del Dashboard',
        required=True
    )
    
    dashboard_title = fields.Char(
        string='Título del Dashboard',
        readonly=True,
        compute='_compute_dashboard_title'
    )
    
    dashboard_description = fields.Text(
        string='Descripción',
        readonly=True,
        compute='_compute_dashboard_info'
    )
    
    dashboard_owners = fields.Char(
        string='Propietarios',
        readonly=True,
        compute='_compute_dashboard_info'
    )
 
    @api.depends('dashboard_uuid')
    def _compute_dashboard_title(self):
        """Obtener título del dashboard"""
        for record in self:
            if record.dashboard_uuid:
                try:
                    # Obtener información del dashboard
                    dashboard_info = self._get_dashboard_info(record.dashboard_uuid)
                    record.dashboard_title = dashboard_info.get('title', 'Dashboard Analytics')
                except:
                    record.dashboard_title = 'Dashboard Analytics'
            else:
                record.dashboard_title = 'Dashboard Analytics'
 
    @api.depends('dashboard_uuid')
    def _compute_dashboard_info(self):
        """Obtener información completa del dashboard"""
        for record in self:
            if record.dashboard_uuid:
                try:
                    dashboard_info = self._get_dashboard_info(record.dashboard_uuid)
                    record.dashboard_description = dashboard_info.get('description', '')
                    record.dashboard_owners = ', '.join(dashboard_info.get('owners', []))
                except:
                    record.dashboard_description = ''
                    record.dashboard_owners = ''
            else:
                record.dashboard_description = ''
                record.dashboard_owners = ''
 
    def _get_dashboard_info(self, dashboard_uuid):
        """Obtener información de un dashboard específico"""
        try:
            selector = self.env['superset.dashboard.selector'].create({})
            dashboards = selector._fetch_dashboards_from_superset()
            
            dashboard = next((d for d in dashboards if d.get('uuid') == dashboard_uuid), None)

            #!Cambio
            _logger.error(f'AQUI VEO EL DASHBOARDDD ========================== {dashboard}')

            if dashboard:
                self.dashboard_id = dashboard['id']
                _logger.info(f'Dashboard ID asignado: {self.dashboard_id}')
            else:
                _logger.warning(f'Dashboard con UUID {dashboard_uuid} no encontrado')

                return dashboard or {}
                
        except Exception as e:
            _logger.error('Error obteniendo info de dashboard %s: %s', dashboard_uuid, str(e))
            return {}
 
    def action_open_in_superset(self):
        """Abrir dashboard directamente en Superset"""
        self.ensure_one()
        
        try:
            config = self.env['superset.dashboard.selector'].create({})._get_superset_config()
            dashboard_info = self._get_dashboard_info(self.dashboard_uuid)
            
            if config.get('url') and dashboard_info.get('url'):
                superset_url = f"{config['url']}{dashboard_info['url']}"
                
                return {
                    'type': 'ir.actions.act_url',
                    'url': superset_url,
                    'target': 'new',
                }
            else:
                raise UserError(_('No se pudo construir la URL del dashboard'))
                
        except Exception as e:
            _logger.error('Error abriendo dashboard en Superset: %s', str(e))
            raise UserError(_(f'Error: {str(e)}'))
 
    def open_dashboard_window(self):
        """Abrir en la misma ventana"""
        self.ensure_one()
        
        _logger.error(f'AQUI VEO EL ID: {self.dashboard_uuid}')
        if not self.dashboard_uuid:
            raise UserError(_('No hay UUID de dashboard configurado'))
        
        # URL de nuestro controlador que renderiza el HTML con SDK
        # embed_url = f"/superset/dashboard/{self.dashboard_uuid}"
        #!Cambio
        embed_url = f"/superset/dashboard/{self.dashboard_id}"
        
        return {
            'type': 'ir.actions.act_url',
            'url': embed_url,
            'target': 'self',
        }