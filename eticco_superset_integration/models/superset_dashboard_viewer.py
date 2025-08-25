# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class SupersetDashboardViewer(models.TransientModel):
    """Modelo mejorado para vista completa del dashboard"""
    _name = 'superset.dashboard.viewer'
    _description = 'Visor de Dashboard de Superset'

    dashboard_uuid = fields.Char(
        string='UUID del Dashboard',
        required=True,
        help='UUID del dashboard de Superset'
    )
    
    dashboard_id = fields.Integer(
        string='ID del Dashboard',
        help='ID numérico del dashboard en Superset'
    )
    
    embedding_uuid = fields.Char(
        string='UUID de Embedding',
        help='UUID específico para embedding del dashboard'
    )
   
    dashboard_title = fields.Char(
        string='Título del Dashboard',
        readonly=True,
        compute='_compute_dashboard_info'
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
    
    dashboard_url = fields.Char(
        string='URL',
        readonly=True,
        compute='_compute_dashboard_info'
    )
    
    embedding_enabled = fields.Boolean(
        string='Embedding Habilitado',
        readonly=True,
        compute='_compute_dashboard_info'
    )

    @api.depends('dashboard_uuid')
    def _compute_dashboard_info(self):
        """Obtener información completa del dashboard"""
        for record in self:
            if record.dashboard_uuid:
                try:
                    dashboard_info = self._get_dashboard_info(record.dashboard_uuid)
                    record.dashboard_title = dashboard_info.get('title', 'Dashboard Analytics')
                    record.dashboard_description = dashboard_info.get('description', '')
                    record.dashboard_owners = ', '.join(dashboard_info.get('owners', []))
                    record.dashboard_url = dashboard_info.get('url', '')
                    record.embedding_enabled = dashboard_info.get('embedding_enabled', False)
                    
                    # Si no se pasó explícitamente, actualizar desde la info obtenida
                    if not record.dashboard_id:
                        record.dashboard_id = dashboard_info.get('id')
                    if not record.embedding_uuid:
                        record.embedding_uuid = dashboard_info.get('embedding_uuid')
                        
                except Exception as e:
                    _logger.error('Error obteniendo info de dashboard %s: %s', record.dashboard_uuid, str(e))
                    record.dashboard_title = 'Dashboard Analytics'
                    record.dashboard_description = 'Error obteniendo información'
                    record.dashboard_owners = ''
                    record.dashboard_url = ''
                    record.embedding_enabled = False
            else:
                record.dashboard_title = 'Dashboard Analytics'
                record.dashboard_description = ''
                record.dashboard_owners = ''
                record.dashboard_url = ''
                record.embedding_enabled = False

    def _get_dashboard_info(self, dashboard_uuid):
        """Obtener información de un dashboard específico"""
        try:
            selector = self.env['superset.dashboard.selector'].create({})
            dashboards = selector._fetch_dashboards_from_superset()
            dashboard = next((d for d in dashboards if d.get('uuid') == dashboard_uuid), None)
            return dashboard or {}
        except Exception as e:
            _logger.error('Error obteniendo info de dashboard %s: %s', dashboard_uuid, str(e))
            return {}
    
    def _get_superset_config(self):
        """Obtener configuración de Superset"""
        ICPSudo = self.env['ir.config_parameter'].sudo()
        return {
            'url': ICPSudo.get_param('superset.url', '').rstrip('/'),
            'username': ICPSudo.get_param('superset.username', ''),
            'password': ICPSudo.get_param('superset.password', ''),
            'timeout': int(ICPSudo.get_param('superset.timeout', '30')),
        }
    
    def _get_access_token(self):
        """Obtener token de acceso a la API de Superset"""
        config = self._get_superset_config()
        
        if not all([config.get('url'), config.get('username'), config.get('password')]):
            raise UserError(_('Configuración de Superset incompleta'))
        
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
                timeout=config.get('timeout', 30)
            )
           
            if response.status_code != 200:
                raise UserError(_('Error de autenticación con Superset'))
           
            access_token = response.json().get('access_token')
            if not access_token:
                raise UserError(_('No se pudo obtener token de acceso'))
            
            return access_token
            
        except Exception as e:
            _logger.error('Error obteniendo access token: %s', str(e))
            raise UserError(_(f'Error de autenticación: {str(e)}'))
    
    def _generate_guest_token(self):
        """Generar guest token para embedding"""
        if not self.embedding_uuid:
            raise UserError(_('UUID de embedding no disponible'))
        
        try:
            config = self._get_superset_config()
            access_token = self._get_access_token()
            
            guest_token_url = f"{config['url']}/api/v1/security/guest_token/"
            guest_data = {
                'user': {
                    'username': 'guest_user',
                    'first_name': 'Guest',
                    'last_name': 'User'
                },
                'resources': [{
                    'type': 'dashboard',
                    'id': self.embedding_uuid  # Usar embedding_uuid para guest token
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
                raise UserError(_(f'Error generando guest token: {error_data}'))
            
            return response.json().get('token')
            
        except Exception as e:
            _logger.error('Error generando guest token: %s', str(e))
            raise UserError(_(f'Error: {str(e)}'))

    def action_open_in_superset(self):
        """Abrir dashboard directamente en Superset"""
        self.ensure_one()
       
        try:
            config = self._get_superset_config()
           
            if config.get('url') and self.dashboard_url:
                superset_url = f"{config['url']}{self.dashboard_url}"
               
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
        """Abrir en la misma ventana usando controlador interno"""
        self.ensure_one()
       
        if not self.dashboard_id:
            raise UserError(_('No hay ID de dashboard configurado'))
        
        embed_url = f"/superset/dashboard/{self.dashboard_id}"
       
        return {
            'type': 'ir.actions.act_url',
            'url': embed_url,
            'target': 'self',
        }
    
    def get_embedding_data(self):
        """Obtener datos necesarios para embedding del dashboard"""
        self.ensure_one()
        
        if not self.embedding_enabled:
            raise UserError(_('Este dashboard no tiene embedding habilitado'))
        
        try:
            guest_token = self._generate_guest_token()
            config = self._get_superset_config()
            
            return {
                'embedding_uuid': self.embedding_uuid,
                'guest_token': guest_token,
                'superset_domain': config['url'],
                'dashboard_title': self.dashboard_title,
                'dashboard_id': self.dashboard_id
            }
            
        except Exception as e:
            _logger.error('Error obteniendo datos de embedding: %s', str(e))
            raise UserError(_(f'Error: {str(e)}'))
    
    @api.model
    def create_from_dashboard_data(self, dashboard_uuid, dashboard_id=None, embedding_uuid=None):
        """Método de conveniencia para crear viewer desde datos de dashboard"""
        values = {'dashboard_uuid': dashboard_uuid}
        
        if dashboard_id:
            values['dashboard_id'] = dashboard_id
        if embedding_uuid:
            values['embedding_uuid'] = embedding_uuid
            
        return self.create(values)