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
        """Calcular estado de conexión usando lógica centralizada"""
        for record in self:
            # Usar lógica unificada de superset_utils
            utils = self.env['superset.utils']
            status = utils.get_system_status(force_refresh=False)
            record.superset_connection_status = status['connection_status']

    @api.depends('superset_url', 'superset_username', 'superset_password')
    def _compute_dashboards_info(self):
        """Obtener información de dashboards usando lógica centralizada"""
        for record in self:
            # Usar lógica unificada de superset_utils
            utils = self.env['superset.utils']
            status = utils.get_system_status(force_refresh=False)
            
            record.superset_dashboards_count = status.get('total_dashboards', 0)
            record.superset_embedding_count = status.get('with_embedding', 0)


    def test_superset_connection(self):
        """Probar conexión con Superset usando utilidades centralizadas"""
        self.ensure_one()
       
        # Crear configuración temporal con valores actuales
        config = {
            'url': self.superset_url.rstrip('/') if self.superset_url else '',
            'username': self.superset_username or '',
            'password': self.superset_password or '',
            'timeout': self.superset_timeout or 30,
        }
        
        try:
            utils = self.env['superset.utils']
            result = utils.test_superset_connection(config)
            
            if result['success']:
                dashboards_count = result['details'].get('dashboards_found', 0)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('✅ Conexión exitosa'),
                        'message': _(f'Conectado correctamente. Se encontraron {dashboards_count} dashboards.'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise ValidationError(result['message'])
                
        except Exception as e:
            _logger.error('Error probando conexión: %s', str(e))
            # Si ya es ValidationError o UserError, propagar
            if isinstance(e, (ValidationError, UserError)):
                raise
            raise ValidationError(_(f'Error inesperado: {str(e)}'))

    def open_superset_dashboards(self):
        """Abrir lista de dashboards de Superset"""
        self.ensure_one()
    
        try:
            # Usar directamente el método de superset_utils en lugar de endpoint
            utils = self.env['superset.utils']
            config = utils.get_superset_config()
            
            # Validar configuración
            utils.validate_config(config)
            
            # Obtener token de acceso
            access_token = utils.get_access_token(config)
            
            # Obtener dashboards usando directamente requests
            import requests
            dashboards_url = f"{config['url']}/api/v1/dashboard/"
            params = {'q': '(page:0,page_size:100)'}
            
            response = requests.get(
                dashboards_url,
                params=params,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=config.get('timeout', 30)
            )
            
            if response.status_code != 200:
                raise UserError(_('Error obteniendo dashboards: HTTP %s') % response.status_code)
                
            data = response.json()
            dashboards = data.get('result', [])
            
            # Filtrar solo dashboards publicados
            published_dashboards = [d for d in dashboards if d.get('published')]
            
            _logger.info('Dashboards encontrados: %s', len(published_dashboards))
            
            if not published_dashboards:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sin dashboards'),
                        'message': _('No se encontraron dashboards publicados en Superset.'),
                        'type': 'warning',
                    }
                }
            
            # Verificar cuáles tienen embedding habilitado
            embedding_count = 0
            message_lines = ['Dashboards encontrados:', '']
            
            for dashboard in published_dashboards[:10]:  # Mostrar solo los primeros 10
                # Verificar si tiene embedding habilitado
                try:
                    embedding_url = f"{config['url']}/api/v1/dashboard/{dashboard.get('id')}/embedded"
                    embedding_response = requests.get(
                        embedding_url,
                        headers={'Authorization': f'Bearer {access_token}'},
                        timeout=config.get('timeout', 30)
                    )
                    
                    has_embedding = (embedding_response.status_code == 200 and 
                                embedding_response.json().get('result', {}).get('uuid'))
                    
                    if has_embedding:
                        embedding_count += 1
                        embedding_status = "✅"
                    else:
                        embedding_status = "❌"
                        
                except Exception:
                    embedding_status = "❓"  # Error verificando embedding
                
                title = dashboard.get('dashboard_title', 'Sin título')
                message_lines.append(f"{embedding_status} {title}")
            
            if len(published_dashboards) > 10:
                message_lines.append(f'... y {len(published_dashboards) - 10} más')
                
            message_lines.extend(['', f'Con embedding habilitado: {embedding_count}'])
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('📊 %s Dashboards Encontrados') % len(published_dashboards),
                    'message': '\n'.join(message_lines),
                    'type': 'info',
                    'sticky': True,
                }
            }
        
        except Exception as e:
            _logger.error('Error abriendo dashboards: %s', str(e))
            # Quitar la f-string que causa problemas con _()
            raise UserError(_('Error: %s') % str(e))

    def clear_superset_cache(self):
        """Limpiar cache de tokens usando utilidades centralizadas"""
        self.ensure_one()
       
        try:
            utils = self.env['superset.utils']
            result = utils.clear_all_cache()
            
            if result['success']:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Cache limpio'),
                        'message': result['message'],
                        'type': 'success',
                    }
                }
            else:
                raise UserError(result['message'])
               
        except Exception as e:
            _logger.error('Error limpiando cache: %s', str(e))
            if isinstance(e, UserError):
                raise
            raise UserError(_(f'Error inesperado: {str(e)}'))

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
       
        # Crear acción para el hub de analytics mejorado
        action = self.env['ir.actions.act_window'].create({
            'name': f'{menu_name} - Analytics Hub',
            'res_model': 'superset.analytics.hub',
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

    def write(self, vals):
        """Interceptar guardado de configuración para refrescar hub"""
        result = super().write(vals)
        
        # Si se modificó algún campo de configuración de Superset, refrescar hub
        superset_fields = ['superset_url', 'superset_username', 'superset_password', 'superset_timeout']
        if any(field in vals for field in superset_fields):
            # Buscar hub y forzar recálculo
            hub = self.env['superset.analytics.hub'].search([], limit=1)
            if hub:
                try:
                    hub.force_refresh_configuration()
                    _logger.info('Hub refrescado después de cambiar configuración')
                except Exception as e:
                    _logger.error('Error refrescando hub: %s', str(e))
        
        return result