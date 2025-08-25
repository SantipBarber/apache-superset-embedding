# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
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
    
    # Información del dashboard actual
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
    
    # Estado del sistema
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
                    selector = self.env['superset.dashboard.selector'].create({})
                    dashboards = selector._fetch_dashboards_from_superset()
                    
                    dashboard = next((d for d in dashboards if d.get('uuid') == record.selected_dashboard), None)
                    
                    if dashboard:
                        record.current_dashboard_title = dashboard.get('title', 'Sin título')
                        record.current_dashboard_id = dashboard.get('id')
                        record.current_embedding_uuid = dashboard.get('embedding_uuid')
                        record.current_dashboard_info = f"""Título: {dashboard.get('title', 'N/A')}
Descripción: {dashboard.get('description', 'Sin descripción')}
Embedding: {'✅ Habilitado' if dashboard.get('embedding_enabled') else '❌ Deshabilitado'}
Propietarios: {', '.join(dashboard.get('owners', []))}"""
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
                config = record._get_superset_config()
                record.has_configuration = bool(config.get('url') and config.get('username') and config.get('password'))
                
                if record.has_configuration:
                    selector = self.env['superset.dashboard.selector'].create({})
                    dashboards = selector._fetch_dashboards_from_superset(config)
                    record.available_dashboards_count = len([d for d in dashboards if d.get('embedding_enabled')])
                else:
                    record.available_dashboards_count = 0
            except:
                record.has_configuration = False
                record.available_dashboards_count = 0

    def _get_dashboard_selection(self):
        """Obtener opciones de dashboard disponibles"""
        try:
            config = self._get_superset_config()
            if not all([config.get('url'), config.get('username'), config.get('password')]):
                return [('no_config', '⚠️ Configurar Superset en Ajustes')]
           
            selector = self.env['superset.dashboard.selector'].create({})
            dashboards = selector._fetch_dashboards_from_superset(config)
           
            selection = []
            for dashboard in dashboards:
                if dashboard.get('embedding_enabled') and dashboard.get('embedding_uuid'):
                    selection.append((
                        dashboard.get('uuid'),
                        f"📊 {dashboard.get('title', 'Sin título')}"
                    ))
           
            if not selection:
                selection = [('no_dashboards', '❌ No hay dashboards con embedding habilitado')]
                
            return selection
           
        except Exception as e:
            _logger.error('Error obteniendo dashboards para hub: %s', str(e))
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
        
        if not self.dashboard_loaded:
            return {'error': 'No hay dashboard cargado'}
            
        try:
            utils = self.env['superset.utils']
            config = self._get_superset_config()
            
            # Validar configuración
            utils.validate_config(config)
            
            # Validar datos del dashboard
            dashboard_data = {
                'id': self.current_dashboard_id,
                'uuid': self.selected_dashboard,
                'title': self.current_dashboard_title,
                'embedding_enabled': bool(self.current_embedding_uuid),
                'embedding_uuid': self.current_embedding_uuid
            }
            
            utils.validate_embedding_requirements(dashboard_data)
            
            # Generar datos para embedding
            viewer = self.env['superset.dashboard.viewer'].create({
                'dashboard_uuid': self.selected_dashboard,
                'dashboard_id': self.current_dashboard_id,
                'embedding_uuid': self.current_embedding_uuid
            })
            
            embedding_data = viewer.get_embedding_data()
            utils.log_debug('Datos de embedding generados', embedding_data)
            
            return embedding_data
            
        except (ValidationError, UserError) as e:
            _logger.error('Error validación obteniendo datos JS: %s', str(e))
            return {'error': str(e)}
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