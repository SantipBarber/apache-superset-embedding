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
            loadingMessage: null,
            loadingStep: null,
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
        console.log('🔍 [TIMING] onMounted - has_configuration inicial:', this.props.record.data.has_configuration);
        
        // ⭐ FORZAR cálculo de campos antes de mostrar la interfaz
        await this.ensureConfigurationIsComputed();
        
        // Verificar configuración y auto-seleccionar después del montaje
        await this.initializeConfiguration();
        
        // 🚀 Auto-selección inteligente y carga automática
        await this.performIntelligentAutoSelection();
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
        const hasConfiguration = this.props.record.data.has_configuration;
        
        console.log('🔍 [TIMING] getDashboardOptions - has_configuration:', hasConfiguration, 'field.selection:', field?.selection?.length || 0);
        
        if (field && field.selection) {
            return field.selection;
        }
        
        // Opciones por defecto mientras se calcula la configuración
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

        // 💾 Guardar preferencia del usuario
        if (this.isDashboardValid(newValue)) {
            await this.saveLastUsedDashboard(newValue);
        }

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

        // 🚀 Iniciar carga con feedback progresivo
        this.setLoadingState(true, '🔍 Verificando configuración...', 1);

        try {
            // Paso 1: Verificar configuración
            await this.simulateProgress(300); // Pequeña pausa para UX
            this.setLoadingState(true, '🔑 Autenticando con Superset...', 2);
            
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

            // Paso 2: Obtener datos del dashboard
            this.setLoadingState(true, '📊 Preparando dashboard...', 3);
            this.state.dashboardData = dashboardData;
            
            // Paso 3: Embed dashboard
            this.setLoadingState(true, '🎨 Renderizando visualización...', 4);
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
            this.setLoadingState(false);
        }
    }

    setLoadingState(isLoading, message = null, step = null) {
        this.state.isLoading = isLoading;
        this.state.loadingMessage = message;
        this.state.loadingStep = step;
        
        if (!isLoading) {
            this.state.loadingMessage = null;
            this.state.loadingStep = null;
        }
    }

    async simulateProgress(delay = 200) {
        // Pequeña pausa para mostrar progreso de manera natural
        return new Promise(resolve => setTimeout(resolve, delay));
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
        
        // Limpiar también los estados de carga
        this.setLoadingState(false);
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
    
    async ensureConfigurationIsComputed() {
        console.log('🔍 [TIMING] ensureConfigurationIsComputed - Forzando cálculo...');
        
        try {
            // Forzar cálculo de campos computados ANTES de mostrar la interfaz
            await this.rpc('/web/dataset/call_kw', {
                model: this.props.record.resModel,
                method: 'force_refresh_configuration',
                args: [this.props.record.resId],
                kwargs: {}
            });
            
            // Recargar el record para obtener los campos actualizados
            await this.props.record.load();
            
            console.log('✅ [TIMING] ensureConfigurationIsComputed - Configuración forzada. has_configuration:', 
                       this.props.record.data.has_configuration);
            
        } catch (error) {
            console.error('❌ [TIMING] Error forzando configuración:', error);
        }
    }

    openSettings() {
        // Abrir Settings de Superset
        window.open('/web#action=base.action_res_config_settings', '_blank');
    }

    async initializeConfiguration() {
        console.log('🔍 [TIMING] initializeConfiguration - has_configuration antes:', this.props.record.data.has_configuration);
        
        try {
            const result = await this.rpc('/web/dataset/call_kw', {
                model: this.props.record.resModel,
                method: 'refresh_dashboard_options',
                args: [this.props.record.resId],
                kwargs: {}
            });

            if (result.options_refreshed) {
                await this.props.record.load();
                console.log('✅ [TIMING] initializeConfiguration - has_configuration después:', this.props.record.data.has_configuration);
                
                // Si se detectó configuración válida, mostrar notificación
                if (result.has_configuration && result.available_options > 0) {
                    this.notification.add(
                        `✅ ${result.available_options} dashboard(s) disponible(s)`,
                        { type: 'success' }
                    );
                }
            }

        } catch (error) {
            console.error('❌ [TIMING] Error inicializando configuración:', error);
        }
    }

    async performIntelligentAutoSelection() {
        try {
            const options = this.getDashboardOptions();
            const validOptions = options.filter(([key]) => this.isDashboardValid(key));
            const currentSelection = this.currentDashboardId;

            console.log('🔍 [TIMING] Auto-selección - opciones válidas:', validOptions.length, 'selección actual:', currentSelection);

            // Caso 1: Ya hay selección válida - cargar directamente
            if (currentSelection && this.isDashboardValid(currentSelection)) {
                console.log('🎯 [TIMING] Dashboard válido ya seleccionado, cargando...');
                await this.loadDashboard();
                return;
            }

            // Caso 2: Solo hay 1 dashboard disponible - auto-seleccionar y cargar
            if (validOptions.length === 1) {
                const [dashboardId, dashboardTitle] = validOptions[0];
                console.log('🚀 [TIMING] Auto-seleccionando único dashboard:', dashboardTitle);
                
                await this.props.record.update({
                    [this.props.name]: dashboardId
                });
                await this.props.record.save();
                
                this.notification.add(
                    `🎯 Dashboard seleccionado automáticamente: ${dashboardTitle.replace(/^📊\s*/, '')}`,
                    { type: 'info' }
                );
                
                await this.loadDashboard();
                return;
            }

            // Caso 3: Múltiples dashboards - verificar preferencia del usuario
            if (validOptions.length > 1) {
                const lastUsedDashboard = await this.getLastUsedDashboard();
                
                if (lastUsedDashboard && this.isDashboardValid(lastUsedDashboard)) {
                    const stillAvailable = validOptions.some(([key]) => key === lastUsedDashboard);
                    
                    if (stillAvailable) {
                        console.log('🔄 [TIMING] Restaurando último dashboard usado');
                        
                        await this.props.record.update({
                            [this.props.name]: lastUsedDashboard
                        });
                        await this.props.record.save();
                        
                        await this.loadDashboard();
                        return;
                    }
                }
                
                this.notification.add(
                    `📋 ${validOptions.length} dashboards disponibles. Selecciona uno para comenzar.`,
                    { type: 'info', sticky: false }
                );
            }

        } catch (error) {
            console.error('❌ [TIMING] Error en auto-selección:', error);
        }
    }

    async getLastUsedDashboard() {
        try {
            // Intentar obtener preferencia del usuario desde localStorage
            const userId = this.env?.services?.user?.userId || 'default';
            const storageKey = `superset_last_dashboard_${userId}`;
            const lastUsed = localStorage.getItem(storageKey);
            
            return lastUsed || null;
        } catch (error) {
            console.error('Error obteniendo último dashboard usado:', error);
            return null;
        }
    }

    async saveLastUsedDashboard(dashboardId) {
        try {
            if (this.isDashboardValid(dashboardId)) {
                const userId = this.env?.services?.user?.userId || 'default';
                const storageKey = `superset_last_dashboard_${userId}`;
                localStorage.setItem(storageKey, dashboardId);
            }
        } catch (error) {
            console.error('Error guardando último dashboard usado:', error);
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