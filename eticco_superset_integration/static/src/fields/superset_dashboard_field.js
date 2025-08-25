/** @odoo-module **/

import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
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
        this.dashboardComponentRef = useRef("dashboardComponent");
        
        this.state = useState({
            currentDashboardId: null,
            autoLoad: false
        });

        onWillStart(this.onWillStart.bind(this));
        onMounted(this.onMounted.bind(this));
    }

    async onWillStart() {
        // Inicializar estado desde el valor del campo
        const currentValue = this.props.record.data[this.props.name];
        this.state.currentDashboardId = currentValue || null;
        this.state.autoLoad = !!currentValue;
    }

    onMounted() {
        // Escuchar cambios en el campo para actualizar el dashboard
        this.env.bus.addEventListener('field-changed', this.onFieldChanged.bind(this));
    }

    /**
     * Manejar cambios en el campo del formulario
     */
    onFieldChanged(event) {
        if (event.detail.fieldName === this.props.name) {
            const newValue = event.detail.newValue;
            
            // Solo actualizar si el valor realmente cambió
            if (newValue !== this.state.currentDashboardId) {
                this.state.currentDashboardId = newValue;
                
                // Notificar al componente dashboard sobre el cambio
                if (this.dashboardComponentRef.el) {
                    const dashboardComponent = this.dashboardComponentRef.el.__owl_component__;
                    if (dashboardComponent && dashboardComponent.onDashboardChange) {
                        dashboardComponent.onDashboardChange(newValue);
                    }
                }
            }
        }
    }

    /**
     * Obtener configuración para el componente dashboard
     */
    getDashboardConfig() {
        return {
            dashboardId: this.state.currentDashboardId,
            modelName: this.props.record.resModel,
            recordId: this.props.record.resId,
            autoLoad: this.state.autoLoad,
            className: this.props.class || '',
            height: this.props.height || '600px'
        };
    }

    /**
     * Callback cuando el dashboard se carga exitosamente
     */
    onDashboardLoaded(dashboardData) {
        console.log('Dashboard cargado en field widget:', dashboardData);
        
        // Actualizar el campo si es necesario
        if (dashboardData.dashboard_id && 
            dashboardData.dashboard_id !== this.state.currentDashboardId) {
            this.state.currentDashboardId = dashboardData.dashboard_id;
        }
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

    /**
     * Recargar dashboard manualmente
     */
    reloadDashboard() {
        if (this.dashboardComponentRef.el) {
            const dashboardComponent = this.dashboardComponentRef.el.__owl_component__;
            if (dashboardComponent && dashboardComponent.reloadDashboard) {
                dashboardComponent.reloadDashboard();
            }
        }
    }

    /**
     * Obtener estado actual del dashboard
     */
    getDashboardState() {
        if (this.dashboardComponentRef.el) {
            const dashboardComponent = this.dashboardComponentRef.el.__owl_component__;
            if (dashboardComponent && dashboardComponent.getState) {
                return dashboardComponent.getState();
            }
        }
        return null;
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

SupersetDashboardField.extractProps = ({ attrs, field }) => {
    return {
        class: attrs.class,
        height: attrs.height,
        autoLoad: attrs.autoLoad !== undefined ? JSON.parse(attrs.autoLoad) : true,
        showInfo: attrs.showInfo !== undefined ? JSON.parse(attrs.showInfo) : true
    };
};

// Registrar el field widget
registry.category("fields").add("superset_dashboard_field", SupersetDashboardField);

/**
 * Variant para modo readonly
 */
export class SupersetDashboardFieldReadonly extends SupersetDashboardField {
    static template = "eticco_superset_integration.SupersetDashboardFieldReadonlyTemplate";

    setup() {
        super.setup();
        // En modo readonly, siempre auto-cargar si hay valor
        this.state.autoLoad = !!this.state.currentDashboardId;
    }
}

// Registrar variant readonly
registry.category("fields").add("superset_dashboard_field", {
    component: SupersetDashboardField,
    additionalClasses: ["o_field_superset_dashboard"],
    supportedTypes: ["selection", "char"],
    isEmpty: (value) => !value || ["no_config", "no_dashboards", "error"].includes(value),
    extractProps: SupersetDashboardField.extractProps,
});