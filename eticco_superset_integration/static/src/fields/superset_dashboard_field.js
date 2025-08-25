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
        this.rpc = useService("rpc");
    }

    get currentDashboardId() {
        return this.props.record.data[this.props.name];
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
        console.log('Dashboard seleccionado:', newValue);
        
        await this.props.record.update({
            [this.props.name]: newValue
        });
        
        if (newValue && !['no_config', 'no_dashboards', 'error'].includes(newValue)) {
            this.notification.add(
                _t('Cargando dashboard...'),
                { type: 'info' }
            );
        }
    }

    onDashboardLoaded(dashboardData) {
        console.log('Dashboard cargado en field widget:', dashboardData);
        
        this.notification.add(
            _t('Dashboard cargado: ') + (dashboardData.dashboard_title || 'Sin título'),
            { type: 'success' }
        );
    }

    onDashboardError(error) {
        console.error('Error en dashboard field widget:', error);
        
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
    autoLoad: true,
    showInfo: true
};


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