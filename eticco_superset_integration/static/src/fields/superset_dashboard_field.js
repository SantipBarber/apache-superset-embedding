/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { SupersetDashboard } from "../components/superset_dashboard/superset_dashboard";

/**
 * Field Widget para embeber dashboards de Superset
 * Uso: <field name="selected_dashboard" widget="superset_dashboard_field"/>
 */
export class SupersetDashboardField extends Component {
    static template = "eticco_superset_integration.SupersetDashboardFieldTemplate";
    static components = { SupersetDashboard };

    setup() {
        this.notification = useService("notification");
        this.rpc = useService("rpc");
        
        this.state = useState({
            isLoading: false,
            lastLoadedId: null
        });
    }

    get currentDashboardId() {
        return this.props.record.data[this.props.name] || "";
    }

    get isDashboardLoaded() {
        // Verificar si hay un dashboard cargado y coincide con la selección actual
        return this.state.lastLoadedId === this.currentDashboardId && 
               this.currentDashboardId && 
               !['no_config', 'no_dashboards', 'error'].includes(this.currentDashboardId);
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
        console.log('Dashboard seleccionado (sin auto-carga):', newValue);
        
        // SOLO GUARDAR - NO AUTO-CARGAR
        await this.props.record.update({
            [this.props.name]: newValue
        });

        // Limpiar estado de carga si cambió la selección
        if (newValue !== this.state.lastLoadedId) {
            this.state.lastLoadedId = null;
            
            // Usar event bus para limpiar dashboard anterior
            this.env.bus.trigger('clear-dashboard', {});
        }

        // Guardar cambios en el record
        await this.props.record.save();
    }

    async loadSelectedDashboard() {
        if (!this.currentDashboardId || ['no_config', 'no_dashboards', 'error'].includes(this.currentDashboardId)) {
            this.notification.add(
                _t('Selecciona un dashboard válido primero'),
                { type: 'warning' }
            );
            return;
        }

        if (this.state.isLoading) {
            return; // Evitar múltiples cargas simultáneas
        }

        this.state.isLoading = true;

        try {
            console.log('Cargando dashboard manualmente:', this.currentDashboardId);

            // Método alternativo: Usar event bus para comunicarse con el componente
            this.env.bus.trigger('load-dashboard', { 
                dashboardId: this.currentDashboardId,
                recordId: this.props.record.resId,
                modelName: this.props.record.resModel
            });
            
            // Marcar como cargado exitosamente (será confirmado por el evento de respuesta)
            this.state.lastLoadedId = this.currentDashboardId;

            this.notification.add(
                _t('Cargando dashboard...'),
                { type: 'info' }
            );

        } catch (error) {
            console.error('Error cargando dashboard:', error);
            
            this.notification.add(
                _t('Error cargando dashboard: ') + error.message,
                { type: 'danger' }
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    async reloadCurrentDashboard() {
        if (!this.isDashboardLoaded) {
            this.notification.add(
                _t('No hay dashboard cargado para actualizar'),
                { type: 'warning' }
            );
            return;
        }

        try {
            // Usar event bus para recargar
            this.env.bus.trigger('reload-dashboard', {
                dashboardId: this.currentDashboardId
            });
            
            this.notification.add(
                _t('Recargando dashboard...'),
                { type: 'info' }
            );
        } catch (error) {
            console.error('Error recargando dashboard:', error);
            
            this.notification.add(
                _t('Error actualizando dashboard: ') + error.message,
                { type: 'danger' }
            );
        }
    }

    onDashboardLoaded(dashboardData) {
        console.log('Dashboard cargado en field widget:', dashboardData);
        
        // Actualizar estado cuando el dashboard se carga exitosamente
        this.state.lastLoadedId = this.currentDashboardId;
        
        this.notification.add(
            _t('Dashboard activo: ') + (dashboardData.dashboard_title || 'Sin título'),
            { type: 'success' }
        );
    }

    onDashboardError(error) {
        console.error('Error en dashboard field widget:', error);
        
        // Limpiar estado de carga en caso de error
        this.state.lastLoadedId = null;
        
        this.notification.add(
            _t('Error cargando dashboard: ') + error,
            { type: 'danger' }
        );
    }
}

SupersetDashboardField.props = {
    record: Object,
    name: String,
    
    class: { type: String, optional: true },
    height: { type: String, optional: true },
    autoLoad: { type: Boolean, optional: true },
    showInfo: { type: Boolean, optional: true }
};

SupersetDashboardField.defaultProps = {
    height: '600px',
    autoLoad: false,  // ← CRÍTICO: Sin auto-carga
    showInfo: true
};

registry.category("fields").add("superset_dashboard_field", {
    component: SupersetDashboardField,
    supportedTypes: ["selection", "char"],
    extractProps: ({ attrs }) => {
        return {
            class: attrs.class,
            height: attrs.height,
            autoLoad: false,  // ← FORZAR: Sin auto-carga nunca
            showInfo: attrs.showInfo !== undefined ? JSON.parse(attrs.showInfo) : true
        };
    },
});