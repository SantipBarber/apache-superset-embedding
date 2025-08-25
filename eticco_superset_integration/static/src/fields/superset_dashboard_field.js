/** @odoo-module **/

import { Component } from "@odoo/owl";
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
    }

    /**
     * Obtener valor actual del campo
     */
    get currentDashboardId() {
        return this.props.record.data[this.props.name];
    }

    /**
     * Callback cuando el dashboard se carga exitosamente
     */
    onDashboardLoaded(dashboardData) {
        console.log('Dashboard cargado en field widget:', dashboardData);
    }

    /**
     * Callback cuando hay error cargando dashboard
     */
    onDashboardError(error) {
        console.error('Error en dashboard field widget:', error);
        
        this.notification.add(
            _t('Error en widget de dashboard: ') + error,
            { type: 'danger' }
        );
    }
}

SupersetDashboardField.props = {
    // Props estándar de field widget
    record: Object,
    name: String,
    
    // Props opcionales para personalización
    class: { type: String, optional: true },
    height: { type: String, optional: true },
    autoLoad: { type: Boolean, optional: true },
    showInfo: { type: Boolean, optional: true }
};

SupersetDashboardField.defaultProps = {
    height: '600px',
    autoLoad: true,
    showInfo: true
};


// Registrar el field widget
registry.category("fields").add("superset_dashboard_field", {
    component: SupersetDashboardField,
    supportedTypes: ["selection", "char"],
    extractProps: ({ attrs }) => {
        return {
            class: attrs.class,
            height: attrs.height,
            autoLoad: attrs.autoLoad !== undefined ? JSON.parse(attrs.autoLoad) : true,
            showInfo: attrs.showInfo !== undefined ? JSON.parse(attrs.showInfo) : true
        };
    },
});