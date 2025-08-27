/** @odoo-module **/

import { Component, useState, useRef, onWillStart, onMounted, onPatched, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Componente integrado para selección y visualización automática de dashboards de Superset
 * Fusiona la funcionalidad de selección + embedding en una sola experiencia fluida
 */
export class SupersetDashboardIntegrated extends Component {
    static template = "eticco_superset_integration.SupersetDashboardIntegratedTemplate";

    setup() {
        this.notification = useService("notification");
        this.rpc = useService("rpc");
        this.dashboardRef = useRef("dashboardContainer");
        
        this.state = useState({
            isLoading: false,
            error: null,
            errorType: null,
            actionRequired: null,
            dashboardData: null,
            isEmbedded: false,
            lastLoadedId: null,
            lastError: null
        });

        onWillStart(this.onWillStart.bind(this));
        onMounted(this.onMounted.bind(this));
        onPatched(this.onPatched.bind(this));
        onWillUnmount(this.onWillUnmount.bind(this));
    }

    async onWillStart() {
        await this.loadSupersetSDK();
    }

    async onMounted() {
        // Verificar configuración y auto-seleccionar después del montaje
        await this.initializeConfiguration();
        
        // Auto-cargar si hay un dashboard válido seleccionado
        if (this.currentDashboardId && this.isDashboardValid(this.currentDashboardId)) {
            this.loadDashboard();
        }
    }

    onPatched() {
        // NO AUTO-CARGAR desde onPatched para evitar bucles infinitos
        // La carga se hará directamente desde onDashboardSelectionChange
    }

    onWillUnmount() {
        this.clearDashboard();
    }

    get currentDashboardId() {
        return this.props.record.data[this.props.name] || "";
    }

    isDashboardValid(dashboardId) {
        return dashboardId && !['no_config', 'no_dashboards', 'error', ''].includes(dashboardId);
    }

    get isCurrentDashboardLoaded() {
        return this.state.lastLoadedId === this.currentDashboardId && 
               this.isDashboardValid(this.currentDashboardId) &&
               this.state.isEmbedded;
    }

    getDashboardOptions() {
        const field = this.props.record.fields[this.props.name];
        if (field && field.selection) {
            return field.selection;
        }
        
        return [
            ['no_config', '⚠️ Configurar Superset en Ajustes'],
            ['no_dashboards', '❌ No hay dashboards disponibles']
        ];
    }

    async onDashboardSelectionChange(event) {
        const newValue = event.target.value;
        
        // Actualizar el record
        await this.props.record.update({
            [this.props.name]: newValue
        });

        // Limpiar dashboard anterior inmediatamente
        if (newValue !== this.state.lastLoadedId) {
            this.clearDashboard();
        }

        // Guardar cambios
        await this.props.record.save();

        // 🚀 CARGA DIRECTA INMEDIATA (sin esperar onPatched)
        if (this.isDashboardValid(newValue) && !this.state.isLoading) {
            await this.loadDashboard();
        }
    }

    async loadSupersetSDK() {
        if (window.supersetEmbeddedSdk) {
            return;
        }

        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/@superset-ui/embedded-sdk@0.2.0';
            script.onload = () => {
                resolve();
            };
            script.onerror = () => {
                reject(new Error('Error cargando Superset SDK'));
            };
            document.head.appendChild(script);
        });
    }

    async loadDashboard() {
        if (this.state.isLoading) {
            return;
        }

        if (!this.isDashboardValid(this.currentDashboardId)) {
            return;
        }

        this.state.isLoading = true;
        this.state.error = null;

        try {            
            const dashboardData = await this.rpc('/web/dataset/call_kw', {
                model: this.props.record.resModel,
                method: 'get_dashboard_data_for_js',
                args: [this.props.record.resId],
                kwargs: {}
            });

            if (dashboardData.error) {
                // Crear error estructurado con información detallada
                const errorObj = new Error(dashboardData.user_message || dashboardData.error);
                errorObj.errorType = dashboardData.error_type;
                errorObj.actionRequired = dashboardData.action_required;
                errorObj.technicalDetails = dashboardData.technical_details;
                errorObj.originalError = dashboardData.error;
                throw errorObj;
            }

            this.state.dashboardData = dashboardData;
            await this.embedDashboard(dashboardData);
            
            this.state.lastLoadedId = this.currentDashboardId;

            this.notification.add(
                '✅ Dashboard cargado: ' + (dashboardData.dashboard_title || 'Sin título'),
                { type: 'success' }
            );

        } catch (error) {
            console.error('❌ Error cargando dashboard:', error);
            
            // Manejar errores según su tipo específico
            let errorMessage = error.message || _t('Error desconocido cargando dashboard');
            let notificationType = 'danger';
            let sticky = true;
            
            // Ajustar mensaje y comportamiento según tipo de error
            if (error.errorType) {
                switch (error.errorType) {
                    case 'connection_error':
                    case 'timeout_error':
                        notificationType = 'warning';
                        errorMessage = _t('🌐 ') + error.message;
                        break;
                        
                    case 'auth_error':
                    case 'permission_error':
                    case 'token_expired':
                        notificationType = 'danger';
                        errorMessage = _t('🔒 ') + error.message;
                        break;
                        
                    case 'server_error':
                        notificationType = 'warning';
                        errorMessage = _t('⚠️ ') + error.message;
                        break;
                        
                    case 'dashboard_not_found':
                    case 'embedding_disabled':
                        notificationType = 'info';
                        errorMessage = _t('📊 ') + error.message;
                        break;
                        
                    case 'config_error':
                        notificationType = 'warning';
                        errorMessage = _t('⚙️ ') + error.message;
                        break;
                        
                    default:
                        errorMessage = _t('❌ ') + error.message;
                }
            }
            
            this.state.error = error.message;
            this.state.errorType = error.errorType;
            this.state.actionRequired = error.actionRequired;
            this.state.lastError = error;
            
            // Mostrar notificación con tipo apropiado
            this.notification.add(errorMessage, { 
                type: notificationType,
                sticky: sticky
            });
            
            // Log técnico para administradores
            if (error.technicalDetails) {
                console.error('Detalles técnicos:', error.technicalDetails);
            }
            
        } finally {
            this.state.isLoading = false;
        }
    }

    async embedDashboard(data) {
        if (!window.supersetEmbeddedSdk) {
            throw new Error('SDK de Superset no disponible');
        }

        if (!data.embedding_uuid) {
            throw new Error('Dashboard no tiene embedding habilitado');
        }

        const container = this.dashboardRef.el;
        if (!container) {
            throw new Error('Contenedor del dashboard no disponible');
        }

        // Limpiar contenedor y asegurar ancho completo
        container.innerHTML = '';
        container.style.width = '100%';
        container.style.height = '100%';

        try {
            const config = {
                id: data.embedding_uuid,
                supersetDomain: data.superset_domain,
                mountPoint: container,
                fetchGuestToken: () => data.guest_token,
                debug: data.debug_mode || false
            };

            await window.supersetEmbeddedSdk.embedDashboard(config);
            
            this.state.isEmbedded = true;

        } catch (error) {
            throw new Error('Error embebiendo dashboard: ' + error.message);
        }
    }

    clearDashboard() {
        if (this.dashboardRef.el) {
            this.dashboardRef.el.innerHTML = '';
        }
        
        this.state.isEmbedded = false;
        this.state.dashboardData = null;
        this.state.error = null;
        this.state.errorType = null;
        this.state.actionRequired = null;
        this.state.lastError = null;
    }

    async reloadDashboard() {
        if (!this.isCurrentDashboardLoaded) {
            this.notification.add(
                _t('No hay dashboard cargado para actualizar'),
                { type: 'warning' }
            );
            return;
        }

        console.log('🔄 Recargando dashboard...');
        this.clearDashboard();
        await this.loadDashboard();
    }

    getLoadingMessage() {
        if (this.state.isLoading) {
            return _t('⏳ Cargando dashboard...');
        }
        if (this.state.error) {
            // Mensaje específico según tipo de error
            switch (this.state.errorType) {
                case 'connection_error':
                    return _t('🌐 Servidor no disponible');
                case 'timeout_error':
                    return _t('⏰ Conexión lenta');
                case 'auth_error':
                case 'permission_error':
                    return _t('🔒 Sin permisos');
                case 'server_error':
                    return _t('⚠️ Error del servidor');
                case 'dashboard_not_found':
                    return _t('📊 Dashboard no encontrado');
                case 'embedding_disabled':
                    return _t('📊 Embedding deshabilitado');
                case 'config_error':
                    return _t('⚙️ Configuración inválida');
                default:
                    return _t('❌ Error: ') + this.state.error;
            }
        }
        if (!this.currentDashboardId) {
            return _t('👆 Selecciona un dashboard para comenzar');
        }
        if (!this.isDashboardValid(this.currentDashboardId)) {
            if (this.currentDashboardId === 'no_config') {
                return _t('⚠️ Configurar Superset en Ajustes');
            }
            if (this.currentDashboardId === 'no_dashboards') {
                return _t('❌ No hay dashboards disponibles');
            }
            return _t('🚫 Dashboard no válido');
        }
        return _t('✅ Dashboard listo');
    }
    
    getActionButton() {
        if (!this.state.error || !this.state.actionRequired) {
            return null;
        }
        
        switch (this.state.actionRequired) {
            case 'retry':
            case 'retry_later':
                return {
                    text: _t('🔄 Reintentar'),
                    class: 'btn-outline-primary',
                    action: () => this.reloadDashboard()
                };
            case 'refresh_page':
            case 'reload_page':
                return {
                    text: _t('↻ Recargar página'),
                    class: 'btn-outline-warning', 
                    action: () => window.location.reload()
                };
            case 'check_credentials':
            case 'check_config':
                return {
                    text: _t('⚙️ Ir a Ajustes'),
                    class: 'btn-outline-info',
                    action: () => this.openSettings()
                };
            case 'contact_admin':
                return {
                    text: _t('📞 Contactar administrador'),
                    class: 'btn-outline-secondary',
                    action: () => this.notification.add(_t('Contacta al administrador del sistema para resolver este problema.'), { type: 'info' })
                };
            case 'select_different':
                return {
                    text: _t('📋 Seleccionar otro dashboard'),
                    class: 'btn-outline-info',
                    action: () => {
                        // Limpiar selección actual
                        this.props.record.update({ [this.props.name]: '' });
                        this.clearDashboard();
                    }
                };
            default:
                return {
                    text: _t('🔄 Intentar de nuevo'),
                    class: 'btn-outline-primary',
                    action: () => this.reloadDashboard()
                };
        }
    }
    
    openSettings() {
        // Abrir Settings de Superset
        window.open('/web#action=base.action_res_config_settings', '_blank');
    }

    async initializeConfiguration() {
        try {
            // Siempre verificar el estado actual de la configuración
            const result = await this.rpc('/web/dataset/call_kw', {
                model: this.props.record.resModel,
                method: 'refresh_dashboard_options',
                args: [this.props.record.resId],
                kwargs: {}
            });

            // Refrescar el record para obtener las opciones actualizadas
            if (result.options_refreshed) {
                await this.props.record.load();
                
                // Si se detectó configuración válida, mostrar notificación
                if (result.has_configuration && result.available_options > 0) {
                    this.notification.add(
                        `✅ ${result.available_options} dashboard(s) disponible(s)`,
                        { type: 'success' }
                    );
                }
            }

        } catch (error) {
            console.error('Error inicializando configuración:', error);
            // No mostrar error al usuario, solo en consola para debug
        }
    }
}

SupersetDashboardIntegrated.props = {
    record: Object,
    name: String,
    class: { type: String, optional: true },
    height: { type: String, optional: true },
    width: { type: String, optional: true }
};

SupersetDashboardIntegrated.defaultProps = {
    height: '700px',
    width: '100%'
};

registry.category("fields").add("superset_dashboard_integrated", {
    component: SupersetDashboardIntegrated,
    supportedTypes: ["selection", "char"],
    extractProps: ({ attrs }) => {
        return {
            class: attrs.class,
            height: attrs.height,
            width: attrs.width
        };
    },
});