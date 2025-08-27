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

    async initializeConfiguration() {
        try {
            const hasValidSelection = this.currentDashboardId && this.isDashboardValid(this.currentDashboardId);
            
            // Si no hay selección válida, intentar obtener opciones actualizadas
            if (!hasValidSelection) {
                const result = await this.rpc('/web/dataset/call_kw', {
                    model: this.props.record.resModel,
                    method: 'refresh_dashboard_options',
                    args: [this.props.record.resId],
                    kwargs: {}
                });

                // Refrescar el record para obtener las opciones actualizadas
                if (result.options_refreshed) {
                    await this.props.record.load();
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