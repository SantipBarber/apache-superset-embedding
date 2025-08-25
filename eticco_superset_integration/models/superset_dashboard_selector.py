# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import logging

_logger = logging.getLogger(__name__)


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
                            f"Propietarios: {', '.join(selected.get('owners', []))}",
                            f"Dashboard_id: {selected.get('id', False)}",
                            f"Dashboard_Uuid: {selected.get('uuid', False)}"
                        ]
                        record.dashboard_info = '\n'.join(info_lines)
                    else:
                        record.dashboard_info = 'Dashboard no encontrado'
                except:
                    record.dashboard_info = 'Error obteniendo información'
            else:
                record.dashboard_info = ''

    def _get_dashboard_selection(self):
        """Obtener lista de dashboards disponibles para selección"""
        try:
            config = self._get_superset_config()
            if not config.get('url'):
                return [('no_config', 'Sin configurar - Ir a Ajustes')]
           
            dashboards = self._fetch_dashboards_from_superset(config)
           
            selection = []
            for dashboard in dashboards:
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
            return selection
           
        except Exception as e:
            _logger.error('Error obteniendo dashboards: %s', str(e))
            return [('error', f'Error: {str(e)[:50]}...')]

    def _get_superset_config(self):
        """Obtener configuración actual de Superset"""
        return self.env['superset.utils'].get_superset_config()

    def _fetch_dashboards_from_superset(self, config=None):
        """Obtener dashboards desde Superset API con información de embedding"""
        if not config:
            config = self._get_superset_config()
           
        try:
            # Validar configuración
            utils = self.env['superset.utils']
            utils.validate_config(config)
            
            # Obtener token de acceso
            access_token = utils.get_access_token(config)
            if not access_token:
                _logger.error('No se pudo obtener access token')
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
                        # Verificar embedding y obtener embedding_uuid
                        embedding_info = self._get_dashboard_embedding_info(
                            config, access_token, dashboard['id']
                        )
                       
                        result.append({
                            'id': dashboard.get('id'),
                            'uuid': dashboard.get('uuid'),
                            'title': dashboard.get('dashboard_title', 'Sin título'),
                            'description': dashboard.get('description', ''),
                            'url': dashboard.get('url', ''),
                            'embedding_enabled': embedding_info['enabled'],
                            'embedding_uuid': embedding_info['uuid'],
                            'owners': [owner.get('username', '') for owner in dashboard.get('owners', [])],
                            'changed_on': dashboard.get('changed_on'),
                        })
                return result
            else:
                _logger.error('Error obteniendo dashboards: HTTP %s', response.status_code)
                return []
           
        except Exception as e:
            _logger.error('Error fetching dashboards: %s', str(e))
            # Si es un UserError, propagar para mostrar al usuario
            if isinstance(e, (ValidationError, UserError)):
                raise
            return []

    def _get_dashboard_embedding_info(self, config, access_token, dashboard_id):
        """Obtener información completa de embedding de un dashboard"""
        try:
            embedding_url = f"{config['url']}/api/v1/dashboard/{dashboard_id}/embedded"
            response = requests.get(
                embedding_url,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=config.get('timeout', 30)
            )
           
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                return {
                    'enabled': bool(result.get('uuid')),
                    'uuid': result.get('uuid', None)
                }
           
            return {'enabled': False, 'uuid': None}
           
        except Exception as e:
            _logger.debug('Error obteniendo embedding para dashboard %s: %s', dashboard_id, str(e))
            return {'enabled': False, 'uuid': None}

    def _check_dashboard_embedding(self, config, access_token, dashboard_id):
        """DEPRECATED: Usar _get_dashboard_embedding_info en su lugar"""
        embedding_info = self._get_dashboard_embedding_info(config, access_token, dashboard_id)
        return embedding_info['enabled']

    def action_view_dashboard(self):
        """Abrir dashboard seleccionado en vista completa"""
        self.ensure_one()
       
        if not self.selected_dashboard or self.selected_dashboard in ['no_config', 'no_dashboards', 'error']:
            raise ValidationError(_('Selecciona un dashboard válido primero.'))
        
        # Obtener información completa del dashboard incluyendo embedding_uuid
        dashboards = self._fetch_dashboards_from_superset()
        selected_dashboard = next((d for d in dashboards if d.get('uuid') == self.selected_dashboard), None)
        
        if not selected_dashboard:
            raise UserError(_('Dashboard no encontrado'))
        
        if not selected_dashboard.get('embedding_enabled') or not selected_dashboard.get('embedding_uuid'):
            raise UserError(_('Este dashboard no tiene embedding habilitado'))
        
        # Retornar acción para vista de dashboard
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dashboard Analytics',
            'res_model': 'superset.dashboard.viewer',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_dashboard_uuid': self.selected_dashboard,
                'default_dashboard_id': selected_dashboard.get('id'),
                'default_embedding_uuid': selected_dashboard.get('embedding_uuid'),
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

    @api.model
    def get_dashboard_data_for_embedding(self, dashboard_uuid):
        """Método auxiliar para obtener datos necesarios para embedding"""
        dashboards = self._fetch_dashboards_from_superset()
        dashboard = next((d for d in dashboards if d.get('uuid') == dashboard_uuid), None)
        
        if not dashboard:
            return None
            
        return {
            'id': dashboard.get('id'),
            'uuid': dashboard.get('uuid'),
            'embedding_uuid': dashboard.get('embedding_uuid'),
            'title': dashboard.get('title'),
            'enabled': dashboard.get('embedding_enabled', False)
        }