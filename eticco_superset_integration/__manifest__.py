# -*- coding: utf-8 -*-
{
    'name': 'Superset Integration MVP',
    'version': '17.0.1.1.0',
    'category': 'Tools',
    'summary': 'Integración robusta de Apache Superset en Odoo',
    'description': """
        Integración moderna de Apache Superset con componentes OWL en Odoo 17.
        
        Características principales:
        - Hub de Analytics integrado con UX de un solo paso
        - Componentes OWL modernos y reactivos
        - Embedding directo con SDK @superset-ui/embedded-sdk
        - Selección de dashboard → Carga automática
        - Arquitectura Python limpia y modular
        - Configuración integrada en Settings de Odoo
        - Soporte completo para múltiples dashboards
        
        Configuración:
        1. Ir a Configuración → Ajustes → Superset Integration
        2. Configurar URL y credenciales de Superset
        3. Probar conexión y crear menú Analytics
        4. Acceder a menú Analytics → Seleccionar dashboard
        
        Requisitos Superset:
        - EMBEDDED_SUPERSET = True en configuración
        - CORS habilitado correctamente
        - Dashboards con embedding habilitado
        - Guest tokens configurados
        
        Arquitectura técnica:
        - Modelos Python separados por responsabilidad
        - Componentes OWL para UI reactiva
        - Widget superset_dashboard reutilizable
        - Validación robusta y manejo de errores
    """,
    'author': 'Eticco Freelosophy SL',
    'website': 'https://www.eticco.es',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
    ],
    
    'data': [
        'data/superset_data.xml',
        'security/superset_security.xml',
        'security/ir.model.access.csv',
        'views/superset_config_views.xml',
        'views/superset_analytics_hub_views.xml',
    ],
    
    'assets': {
        'web.assets_backend': [
            # Componente integrado con UX mejorada
            'eticco_superset_integration/static/src/fields/superset_dashboard_integrated.js',
            'eticco_superset_integration/static/src/fields/superset_dashboard_integrated.xml',
        ],
    },
    
    'installable': True,
    'auto_install': False,
    'application': False,
    
    'images': ['static/description/icon.png'],
    'external_dependencies': {
        'python': ['requests'],
    },
    
    'development_status': 'Beta',
    'maintainers': ['tu_usuario'],
}