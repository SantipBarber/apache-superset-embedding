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
        
        // Event listeners para comunicación con field widget
        this.env.bus.addEventListener('load-dashboard', this.onLoadDashboardEvent.bind(this));
        this.env.bus.addEventListener('reload-dashboard', this.onReloadDashboardEvent.bind(this));
        this.env.bus.addEventListener('clear-dashboard', this.onClearDashboardEvent.bind(this));
     }

    async onWillStart() {
        await this.loadSupersetSDK();
    }

    onMounted() {        
        // SOLO cargar si autoLoad está explícitamente habilitado Y hay dashboardId
        if (this.props.autoLoad && this.props.dashboardId) {
            this.state.lastDashboardId = this.props.dashboardId;
            this.loadDashboard();
        }
    }

    onPatched() {
        // ⚠️ ELIMINADO: Auto-carga que causaba timing issues
        // Solo actualizar tracking del ID, NO cargar automáticamente
        this.state.lastDashboardId = this.props.dashboardId;
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
        if (this.state.loading) {
            console.warn('Ya hay una carga en progreso, ignorando...');
            return;
        }

        this.state.loading = true;
        this.state.error = null;

        try {
            const targetId = dashboardId || this.props.dashboardId;
            console.log('Iniciando carga de dashboard:', targetId);
            
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

            // Emitir evento de éxito
            this.env.bus.trigger('dashboard-loaded', { dashboardData });

        } catch (error) {
            console.error('Error cargando dashboard:', error);
            this.state.error = error.message || _t('Error desconocido cargando dashboard');
            
            // Emitir evento de error
            this.env.bus.trigger('dashboard-error', { error: this.state.error });
            
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
    
            console.log('Embedding dashboard con config:', config);
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
        
        console.log('Dashboard limpiado');
    }

    async reloadDashboard() {
        console.log('Recargando dashboard...');
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

    // Event handlers para comunicación con field widget
    async onLoadDashboardEvent(event) {
        const { dashboardId, recordId, modelName } = event.detail;
        console.log('Evento load-dashboard recibido:', event.detail);
        
        try {
            await this.loadDashboard(dashboardId);
        } catch (error) {
            console.error('Error en evento load-dashboard:', error);
        }
    }

    async onReloadDashboardEvent(event) {
        console.log('Evento reload-dashboard recibido:', event.detail);
        await this.reloadDashboard();
    }

    onClearDashboardEvent(event) {
        console.log('Evento clear-dashboard recibido:', event.detail);
        this.clearDashboard();
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
    autoLoad: false,  // ← CRÍTICO: Sin auto-carga por defecto
    className: '',
    height: '600px'
};