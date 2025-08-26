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

    @api.depends()
    def _compute_system_status(self):
        """Computar estado del sistema"""
        for record in self:
            try:
                utils = self.env['superset.utils']
                config = utils.get_superset_config()
                record.has_configuration = bool(config.get('url') and config.get('username') and config.get('password'))
                
                if record.has_configuration:
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
                        
                        if response.status_code == 200:
                            data = response.json()
                            dashboards = [d for d in data.get('result', []) if d.get('published')]
                            
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
                            
                            record.available_dashboards_count = embedding_count
                        else:
                            record.available_dashboards_count = 0
                    except:
                        record.available_dashboards_count = 0
                else:
                    record.available_dashboards_count = 0
            except:
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
                        
                        if embedding_enabled:
                            selection.append((dashboard_uuid, f"✅ {dashboard_title}"))
                        else:
                            selection.append((dashboard_uuid, f"❌ {dashboard_title} (sin embedding)"))
                            
                    except Exception as e:
                        _logger.error('Error verificando embedding para dashboard %s: %s', 
                                    dashboard.get('id'), str(e))
                        selection.append((
                            dashboard.get('uuid'),
                            f"❓ {dashboard.get('dashboard_title', 'Sin título')} (error)"
                        ))
                
                if not selection:
                    return [('no_dashboards', '❌ No hay dashboards disponibles')]
                    
                selection.sort(key=lambda x: (not x[1].startswith('✅'), x[1]))
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
            'target': 'current',
            'context': {'module': 'eticco_superset_integration'}
        }

    def get_embedding_url(self):
        """Obtener URL para embedding del dashboard actual"""
        self.ensure_one()
        
        if not self.dashboard_loaded or not self.current_dashboard_id:
            return None
            
        return f"/superset/dashboard/{self.current_dashboard_id}"

    def get_dashboard_data_for_js(self):
        """Obtener datos del dashboard para JavaScript/OWL"""
        self.ensure_one()
        
        if not self.selected_dashboard or self.selected_dashboard in ['no_config', 'no_dashboards', 'error']:
            return {'error': 'No hay dashboard seleccionado'}
            
        try:
            self._compute_dashboard_info()
            
            utils = self.env['superset.utils']
            config = utils.get_superset_config()
            utils.validate_config(config)
            
            if not all([self.current_dashboard_id, self.selected_dashboard, self.current_embedding_uuid]):
                return {'error': 'Datos de dashboard incompletos'}
            
            access_token = utils.get_access_token(config)
            
            guest_token_url = f"{config['url']}/api/v1/security/guest_token/"
            guest_data = {
                'user': {
                    'username': 'guest_user',
                    'first_name': 'Guest',
                    'last_name': 'User'
                },
                'resources': [{
                    'type': 'dashboard',
                    'id': self.current_embedding_uuid
                }],
                'rls': []
            }
            
            response = requests.post(
                guest_token_url,
                json=guest_data,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                timeout=config.get('timeout', 30)
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                return {'error': f'Error generando guest token: {error_data}'}
            
            guest_token = response.json().get('token')
            
            if not guest_token:
                return {'error': 'No se pudo obtener guest token'}
            
            self.dashboard_loaded = True
            
            return {
                'embedding_uuid': self.current_embedding_uuid,
                'guest_token': guest_token,
                'superset_domain': config['url'],
                'dashboard_title': self.current_dashboard_title,
                'dashboard_id': self.current_dashboard_id,
                'debug_mode': config.get('debug_mode', False)
            }
            
        except Exception as e:
            _logger.error('Error inesperado obteniendo datos para JS: %s', str(e))
            return {'error': f'Error inesperado: {str(e)}'}

    @api.model
    def get_default_hub(self):
        """Obtener o crear hub por defecto"""
        hub = self.search([], limit=1)
        if not hub:
            hub = self.create({})
        return hub