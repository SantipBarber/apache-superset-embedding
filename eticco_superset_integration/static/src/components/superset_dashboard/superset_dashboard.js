/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUnmount, onPatched, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class SupersetDashboard extends Component {
    static template = "eticco_superset_integration.SupersetDashboardTemplate";
    
    setup() {
        this.notification = useService("notification");
        this.rpc = useService("rpc");
        this.dashboardRef = useRef("dashboardContainer");
        
        this.state = useState({
            loading: false,
            error: null,
            dashboardData: null,
            isEmbedded: false,
            lastDashboardId: null
        });

        onWillStart(this.onWillStart.bind(this));
        onMounted(this.onMounted.bind(this));
        onPatched(this.onPatched.bind(this));
        onWillUnmount(this.onWillUnmount.bind(this));
        this.env.bus.addEventListener('dashboard-selection-changed', this.onDashboardSelectionEvent.bind(this));   
     }

     async onDashboardSelectionEvent(event) {
        const { dashboardId } = event.detail;
        await this.loadDashboard(dashboardId);
    }

    async onWillStart() {
        await this.loadSupersetSDK();
    }

    onMounted() {
        this.state.lastDashboardId = this.props.dashboardId;
        if (this.props.dashboardId && this.props.autoLoad) {
            this.loadDashboard();
        }
    }

    onPatched() {
        const currentId = this.props.dashboardId;
        
        if (currentId !== this.state.lastDashboardId) {
            this.state.lastDashboardId = currentId;
            this.clearDashboard();
        }
    }

    onWillUnmount() {
        this.clearDashboard();
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

    async loadDashboard(dashboardId = null) {
        if (this.state.loading) return;

        this.state.loading = true;
        this.state.error = null;

        try {
            const targetId = dashboardId || this.props.dashboardId;
            
            let dashboardData;
            
            if (this.props.modelName && this.props.recordId) {
                dashboardData = await this.rpc('/web/dataset/call_kw', {
                    model: this.props.modelName,
                    method: 'get_dashboard_data_for_js',
                    args: [this.props.recordId],
                    kwargs: {}
                });
            } else if (targetId) {
                dashboardData = await this.rpc('/web/dataset/call_kw', {
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

    async embedDashboard(data) {
        if (!window.supersetEmbeddedSdk) {
            throw new Error('SDK de Superset no disponible');
        }
    
        if (!data.embedding_uuid) {
            throw new Error('Dashboard no tiene embedding habilitado');
        }
    
        let container = this.dashboardRef.el;
        
        if (!container) {
            container = document.querySelector('#superset-container, .superset_dashboard_embed, [t-ref="dashboardContainer"]');
        }
        
        if (!container) {
            console.error('dashboardRef:', this.dashboardRef);
            console.error('Buscando contenedores disponibles...');
            const allContainers = document.querySelectorAll('div[class*="dashboard"], div[id*="superset"]');
            console.error('Contenedores encontrados:', allContainers);
            throw new Error('Contenedor del dashboard no disponible');
        }
    
        container.innerHTML = '';
    
        try {
            const config = {
                id: data.embedding_uuid,
                supersetDomain: data.superset_domain,
                mountPoint: container,
                fetchGuestToken: () => data.guest_token,
                debug: data.debug_mode || false
            };
    
            console.log('Embedding config:', config);
            await window.supersetEmbeddedSdk.embedDashboard(config);
            
            this.state.isEmbedded = true;
    
            this.notification.add(
                'Dashboard cargado: ' + data.dashboard_title,
                { type: 'success' }
            );
    
        } catch (error) {
            console.error('Error en embedding:', error);
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
        this.clearDashboard();
        await this.loadDashboard();
    }

    async onDashboardChange(newDashboardId) {
        if (newDashboardId && newDashboardId !== this.props.dashboardId) {
            await this.loadDashboard(newDashboardId);
        } else if (!newDashboardId) {
            this.clearDashboard();
        }
    }

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
    dashboardId: { type: Number, optional: true },
    modelName: { type: String, optional: true },
    recordId: { type: Number, optional: true },
    autoLoad: { type: Boolean, optional: true },
    className: { type: String, optional: true },
    height: { type: String, optional: true }
};

SupersetDashboard.defaultProps = {
    autoLoad: true,
    className: '',
    height: '600px'
};