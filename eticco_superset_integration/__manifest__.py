# -*- coding: utf-8 -*-
{
    'name': 'Superset Integration MVP',
    'version': '17.0.1.1.0',
    'category': 'Tools',
    'summary': 'Integración robusta de Apache Superset en Odoo',
    'description': """
        Módulo MVP para embeber dashboards de Apache Superset en formularios de Odoo.
        
        Características principales:
        - Configuración integrada en Settings de Odoo
        - Widget superset_dashboard para cualquier formulario
        - Embedding con SDK oficial @superset-ui/embedded-sdk
        - Guest tokens automáticos con cache inteligente
        - Manejo robusto de errores y logging detallado
        - Menús dinámicos configurables
        - Selector de dashboards con vista previa
        - Soporte para múltiples dashboards
        
        Configuración:
        1. Ir a Configuración → Ajustes → Superset Integration
        2. Configurar URL, credenciales de Superset
        3. Probar conexión
        4. Crear menú de dashboards
        5. Usar widget: <field name="campo" widget="superset_dashboard"/>
        
        Requisitos Superset:
        - EMBEDDED_SUPERSET = True
        - CORS habilitado con URLs terminadas en "/"
        - Dashboards con embedding habilitado manualmente
        - Guest tokens configurados
        
        Seguridad:
        - Grupos de usuarios específicos
        - Permisos granulares
        - Validación de credenciales
        - Logs de auditoría
    """,
    'author': 'Eticco Freelosophy SL',
    'website': 'https://www.eticco.es',
    'license': 'LGPL-3',
    
    # Dependencias
    'depends': [
        'base',
        'web',
    ],
    
    # Archivos de datos
    'data': [
        'data/superset_data.xml',              # Configuración inicial
        'security/superset_security.xml',
        'security/ir.model.access.csv',
        'views/superset_config_views.xml',
        'views/superset_analytics_hub_views.xml',  # Nueva vista del hub
        'templates/dashboard_page.xml',        # Template HTML para embedding
        'templates/dashboard_error.xml',       # Template HTML para errores
    ],
    
    # Assets frontend OWL
    'assets': {
        'web.assets_backend': [
            # Componentes OWL
            'eticco_superset_integration/static/src/components/**/*.js',
            'eticco_superset_integration/static/src/fields/**/*.js',
            'eticco_superset_integration/static/src/components/**/*.xml',
            'eticco_superset_integration/static/src/fields/**/*.xml',
            'eticco_superset_integration/static/src/components/**/*.scss',
        ],
    },
    
    # Configuración del módulo
    'installable': True,
    'auto_install': False,
    'application': False,
    
    # Sin hooks en Odoo 17 - usar data files para configuración inicial
    
    # Metadatos adicionales
    'images': ['static/description/icon.png'],
    'external_dependencies': {
        'python': ['requests'],  # Asegurar que requests esté disponible
    },
    
    # Configuración de desarrollo
    'development_status': 'Beta',
    'maintainers': ['tu_usuario'],
}