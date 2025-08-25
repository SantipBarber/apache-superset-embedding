/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUnmount, useState, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export class SupersetDashboard extends Component {
    static template = "eticco_superset_integration.SupersetDashboardTemplate";
    
    setup() {
        this.notification = useService("notification");
        this.dashboardRef = useRef("dashboardContainer");
        
        this.state = useState({
            loading: false,
            error: null,
            dashboardData: null,
            isEmbedded: false
        });

        onWillStart(this.onWillStart.bind(this));
        onMounted(this.onMounted.bind(this));
        onWillUnmount(this.onWillUnmount.bind(this));
    }

    async onWillStart() {
        // Cargar SDK de Superset
        await this.loadSupersetSDK();
    }

    onMounted() {
        // Cargar dashboard si hay datos disponibles
        if (this.props.dashboardId || this.props.autoLoad) {
            this.loadDashboard();
        }
    }

    onWillUnmount() {
        // Limpiar dashboard al desmontar componente
        this.clearDashboard();
    }

    /**
     * Cargar SDK de Superset dinámicamente
     */
    async loadSupersetSDK() {
        if (window.supersetEmbeddedSdk) {
            return; // Ya está cargado
        }

        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/@superset-ui/embedded-sdk@0.2.0';
            script.onload = () => {
                console.log('Superset SDK cargado exitosamente');
                resolve();
            };
            script.onerror = () => {
                console.error('Error cargando Superset SDK');
                reject(new Error('Error cargando Superset SDK'));
            };
            document.head.appendChild(script);
        });
    }

    /**
     * Cargar dashboard desde el modelo Python
     */
    async loadDashboard(dashboardId = null) {
        if (this.state.loading) return;

        this.state.loading = true;
        this.state.error = null;

        try {
            // Usar ID proporcionado o el de props
            const targetId = dashboardId || this.props.dashboardId;
            
            let dashboardData;
            
            if (this.props.modelName && this.props.recordId) {
                // Obtener datos desde el modelo
                dashboardData = await rpc('/web/dataset/call_kw', {
                    model: this.props.modelName,
                    method: 'get_dashboard_data_for_js',
                    args: [this.props.recordId],
                    kwargs: {}
                });
            } else if (targetId) {
                // Obtener datos directamente por ID
                dashboardData = await rpc('/web/dataset/call_kw', {
                    model: 'superset.analytics.hub',
                    method: 'get_dashboard_data_for_js',
                    args: [targetId],
                    kwargs: {}
                });
            } else {
                throw new Error(_t('No se especificó dashboard para cargar'));
            }

            if (dashboardData.error) {
                throw new Error(dashboardData.error);
            }

            this.state.dashboardData = dashboardData;
            await this.embedDashboard(dashboardData);

        } catch (error) {
            console.error('Error cargando dashboard:', error);
            this.state.error = error.message || _t('Error desconocido cargando dashboard');
            
            this.notification.add(
                _t('Error cargando dashboard: ') + this.state.error,
                { type: 'danger' }
            );
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Embeber dashboard usando el SDK oficial
     */
    async embedDashboard(data) {
        if (!window.supersetEmbeddedSdk) {
            throw new Error(_t('SDK de Superset no disponible'));
        }

        if (!data.embedding_uuid) {
            throw new Error(_t('Dashboard no tiene embedding habilitado'));
        }

        const container = this.dashboardRef.el;
        if (!container) {
            throw new Error(_t('Contenedor del dashboard no disponible'));
        }

        // Limpiar contenedor
        container.innerHTML = '';

        try {
            // Configuración para el embedding
            const config = {
                id: data.embedding_uuid, // Usar embedding_uuid como ID
                supersetDomain: data.superset_domain,
                mountPoint: container,
                fetchGuestToken: () => data.guest_token,
                debug: data.debug_mode || false
            };

            console.log('Configuración embedding:', config);

            // Embeber dashboard
            await window.supersetEmbeddedSdk.embedDashboard(config);
            
            this.state.isEmbedded = true;
            console.log('Dashboard embebido exitosamente');

            this.notification.add(
                _t('Dashboard cargado: ') + data.dashboard_title,
                { type: 'success' }
            );

        } catch (error) {
            console.error('Error en embedding:', error);
            throw new Error(_t('Error embebiendo dashboard: ') + error.message);
        }
    }

    /**
     * Limpiar dashboard actual
     */
    clearDashboard() {
        if (this.dashboardRef.el) {
            this.dashboardRef.el.innerHTML = '';
        }
        
        this.state.isEmbedded = false;
        this.state.dashboardData = null;
        this.state.error = null;
    }

    /**
     * Recargar dashboard actual
     */
    async reloadDashboard() {
        this.clearDashboard();
        await this.loadDashboard();
    }

    /**
     * Manejar cambio de dashboard (llamado desde componente padre)
     */
    async onDashboardChange(newDashboardId) {
        if (newDashboardId && newDashboardId !== this.props.dashboardId) {
            await this.loadDashboard(newDashboardId);
        } else if (!newDashboardId) {
            this.clearDashboard();
        }
    }

    /**
     * Obtener estado del componente (para debugging)
     */
    getState() {
        return {
            loading: this.state.loading,
            error: this.state.error,
            isEmbedded: this.state.isEmbedded,
            hasDashboardData: !!this.state.dashboardData
        };
    }
}

SupersetDashboard.props = {
    // ID del dashboard a cargar
    dashboardId: { type: Number, optional: true },
    
    // Modelo y registro para obtener datos
    modelName: { type: String, optional: true },
    recordId: { type: Number, optional: true },
    
    // Cargar automáticamente al montar
    autoLoad: { type: Boolean, optional: true },
    
    // Clases CSS adicionales
    className: { type: String, optional: true },
    
    // Altura del contenedor
    height: { type: String, optional: true }
};

SupersetDashboard.defaultProps = {
    autoLoad: true,
    className: '',
    height: '600px'
};