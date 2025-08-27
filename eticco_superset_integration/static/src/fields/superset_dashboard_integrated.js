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
            dashboardData: null,
            isEmbedded: false,
            lastLoadedId: null
        });

        onWillStart(this.onWillStart.bind(this));
        onMounted(this.onMounted.bind(this));
        onPatched(this.onPatched.bind(this));
        onWillUnmount(this.onWillUnmount.bind(this));
    }

    async onWillStart() {
        await this.loadSupersetSDK();
    }

    onMounted() {
        // Auto-cargar si hay un dashboard seleccionado
        if (this.currentDashboardId && this.isDashboardValid(this.currentDashboardId)) {
            this.loadDashboard();
        }
    }

    onPatched() {
        // TEMPORALMENTE DESHABILITADO PARA EVITAR BUCLES
        console.log('🔄 onPatched ejecutado (DESHABILITADO):', {
            currentDashboardId: this.currentDashboardId,
            lastLoadedId: this.state.lastLoadedId,
            isLoading: this.state.isLoading
        });
        
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
        console.log('📊 Dashboard seleccionado (con auto-carga):', {
            newValue,
            oldValue: this.currentDashboardId,
            lastLoadedId: this.state.lastLoadedId
        });
        
        // Actualizar el record
        console.log('📝 Actualizando record...');
        await this.props.record.update({
            [this.props.name]: newValue
        });

        // Limpiar dashboard anterior inmediatamente
        if (newValue !== this.state.lastLoadedId) {
            console.log('🧹 Limpiando dashboard anterior');
            this.clearDashboard();
        }

        // Guardar cambios
        console.log('💾 Guardando cambios...');
        await this.props.record.save();

        // 🚀 CARGA DIRECTA INMEDIATA (sin esperar onPatched)
        if (this.isDashboardValid(newValue) && !this.state.isLoading) {
            console.log('🚀 Iniciando carga DIRECTA después de selección');
            await this.loadDashboard();
        } else {
            console.log('⏸️ No se carga directamente:', {
                isValid: this.isDashboardValid(newValue),
                isLoading: this.state.isLoading
            });
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
        console.log('📍 loadDashboard iniciado:', {
            isLoading: this.state.isLoading,
            currentDashboardId: this.currentDashboardId,
            recordResId: this.props.record.resId,
            recordResModel: this.props.record.resModel
        });
        
        if (this.state.isLoading) {
            console.warn('⚠️ Ya hay una carga en progreso, ignorando...');
            return;
        }

        if (!this.isDashboardValid(this.currentDashboardId)) {
            console.warn('⚠️ Dashboard ID no válido:', this.currentDashboardId);
            return;
        }

        this.state.isLoading = true;
        this.state.error = null;

        try {
            console.log('🚀 Cargando dashboard automáticamente:', this.currentDashboardId);
            
            console.log('📞 Ejecutando RPC call:', {
                model: this.props.record.resModel,
                method: 'get_dashboard_data_for_js',
                args: [this.props.record.resId]
            });
            
            const dashboardData = await this.rpc('/web/dataset/call_kw', {
                model: this.props.record.resModel,
                method: 'get_dashboard_data_for_js',
                args: [this.props.record.resId],
                kwargs: {}
            });

            console.log('📞 RPC response recibido:', dashboardData);

            if (dashboardData.error) {
                console.error('❌ Error en RPC response:', dashboardData.error);
                throw new Error(dashboardData.error);
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
            this.state.error = error.message || _t('Error desconocido cargando dashboard');
            
            this.notification.add(
                _t('Error cargando dashboard: ') + this.state.error,
                { type: 'danger' }
            );
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

        // Limpiar contenedor
        container.innerHTML = '';

        try {
            const config = {
                id: data.embedding_uuid,
                supersetDomain: data.superset_domain,
                mountPoint: container,
                fetchGuestToken: () => data.guest_token,
                debug: data.debug_mode || false
            };

            console.log('📊 Embedding dashboard con config:', config);
            await window.supersetEmbeddedSdk.embedDashboard(config);
            
            this.state.isEmbedded = true;

        } catch (error) {
            console.error('❌ Error en embedding:', error);
            throw new Error('Error embebiendo dashboard: ' + error.message);
        }
    }

    clearDashboard() {
        console.log('🧹 clearDashboard ejecutado:', {
            hadElement: !!this.dashboardRef.el,
            wasEmbedded: this.state.isEmbedded,
            currentDashboardId: this.currentDashboardId,
            lastLoadedId: this.state.lastLoadedId
        });
        
        if (this.dashboardRef.el) {
            this.dashboardRef.el.innerHTML = '';
        }
        
        this.state.isEmbedded = false;
        this.state.dashboardData = null;
        this.state.error = null;
        
        console.log('✅ Dashboard limpiado completado');
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
            return _t('Cargando dashboard...');
        }
        if (this.state.error) {
            return _t('Error: ') + this.state.error;
        }
        if (!this.currentDashboardId) {
            return _t('Selecciona un dashboard para comenzar');
        }
        if (!this.isDashboardValid(this.currentDashboardId)) {
            if (this.currentDashboardId === 'no_config') {
                return _t('⚠️ Configurar Superset en Ajustes');
            }
            if (this.currentDashboardId === 'no_dashboards') {
                return _t('❌ No hay dashboards disponibles');
            }
            return _t('Dashboard no válido');
        }
        return _t('Dashboard listo');
    }
}

SupersetDashboardIntegrated.props = {
    record: Object,
    name: String,
    class: { type: String, optional: true },
    height: { type: String, optional: true }
};

SupersetDashboardIntegrated.defaultProps = {
    height: '700px'
};

registry.category("fields").add("superset_dashboard_integrated", {
    component: SupersetDashboardIntegrated,
    supportedTypes: ["selection", "char"],
    extractProps: ({ attrs }) => {
        return {
            class: attrs.class,
            height: attrs.height
        };
    },
});