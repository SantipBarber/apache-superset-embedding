/** @odoo-module **/
 
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
 
class SupersetDashboardWidget extends Component {
    static template = "eticco_superset_integration.SupersetDashboardWidget";
    static props = {
        ...standardFieldProps,
        "*": true,
    };
    
    setup() {
        console.log('🚀 WIDGET SETUP EJECUTADO - Props:', this.props);
    }
}
 
// Intentar registrar en múltiples categorías para ver cuál funciona
registry.category("fields").add("superset_dashboard", SupersetDashboardWidget);
registry.category("components").add("SupersetDashboardWidget", SupersetDashboardWidget);
 
console.log('🔥 Widget registrado en fields registry');
console.log('🔍 Registry fields disponibles:', registry.category("fields").getEntries().map(e => e[0]));
 
// Ver si nuestro widget está realmente registrado
setTimeout(() => {
    const widget = registry.category("fields").get("superset_dashboard");
    console.log('🧐 Widget recuperado del registry:', widget);
}, 1000);
// /** @odoo-module **/
 
// import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
// import { registry } from "@web/core/registry";
// import { useService } from "@web/core/utils/hooks";
 
// export class SupersetDashboardWidget extends Component {
//     static template = "eticco_superset_integration.SupersetDashboardWidget";
//     static props = {
//         record: { type: Object, optional: true },
//         name: { type: String, optional: true },
//         value: { type: String, optional: true },
//         readonly: { type: Boolean, optional: true },
//         "*": true
//     };
    
//     setup() {
//         this.rpc = useService("rpc");
//         this.notification = useService("notification");
        
//         // Debug: Log props para ver qué llega
//         console.log('🔍 SupersetDashboardWidget props:', this.props);
//         console.log('🔍 Props.name:', this.props.name);
//         console.log('🔍 Props.record:', this.props.record);
        
//         this.containerRef = useRef("superset-container");
//         this.state = useState({
//             loading: false,
//             error: null,
//             currentMessage: ""
//         });
        
//         this.embedInstance = null;
        
//         onMounted(() => this.loadDashboard());
//         onWillUnmount(() => this.cleanup());
//     }
    
//     async loadDashboard() {
//         try {
//             // Obtener UUID del dashboard desde el record
//             let dashboardUuid = null;
            
//             console.log('🔍 Props completas:', this.props);
            
//             if (this.props?.record?.data) {
//                 // Buscar en los datos del record
//                 dashboardUuid = this.props.record.data.dashboard_uuid ||
//                                this.props.record.data.selected_dashboard;
//                 console.log('🎯 UUID encontrado:', dashboardUuid);
//                 console.log('🎯 Record data:', this.props.record.data);
//             }
            
//             // Fallback: usar el valor directo si se pasa como prop
//             if (!dashboardUuid && this.props?.value) {
//                 dashboardUuid = this.props.value;
//                 console.log('🎯 UUID desde props.value:', dashboardUuid);
//             }
            
            
//             if (!dashboardUuid || dashboardUuid === '' || dashboardUuid.includes('no_')) {
//                 this.setError('No dashboard configurado en este campo');
//                 return;
//             }
            
//             this.setLoading(true, "Cargando dashboard...");
            
//             // Cargar SDK
//             await this.loadSDK();
            
//             // Llamar API pasando el dashboard_uuid
//             const embedData = await this.rpc('/superset/embed', {
//                 dashboard_uuid: dashboardUuid
//             });
            
//             console.log('📡 Respuesta API:', embedData);
            
//             if (embedData.success) {
//                 await this.embedDashboard(embedData);
//             } else {
//                 this.setError(embedData.error);
//             }
            
//         } catch (error) {
//             console.error('❌ Error completo:', error);
//             this.setError(error.message);
//         } finally {
//             this.setLoading(false);
//         }
//     }
    
//     async loadSDK() {
//         if (window.supersetEmbeddedSdk) return;
        
//         return new Promise((resolve, reject) => {
//             const script = document.createElement('script');
//             script.src = 'https://unpkg.com/@superset-ui/embedded-sdk@0.2.0';
//             script.onload = () => resolve();
//             script.onerror = () => reject(new Error('Error cargando SDK'));
//             document.head.appendChild(script);
//         });
//     }
    
//     async embedDashboard(embedData) {
//         this.containerRef.el.innerHTML = '';
        
//         this.embedInstance = await window.supersetEmbeddedSdk.embedDashboard({
//             id: embedData.dashboard_uuid,  // Este es el embedding_uuid
//             supersetDomain: embedData.superset_url,
//             mountPoint: this.containerRef.el,
//             fetchGuestToken: () => embedData.guest_token,
//             dashboardUiConfig: {
//                 hideTitle: false,
//                 hideTab: false,
//                 hideChartControls: false,
//             }
//         });
        
//         // Ajustar iframe
//         setTimeout(() => {
//             const iframe = this.containerRef.el.querySelector('iframe');
//             if (iframe) {
//                 iframe.style.width = '100%';
//                 iframe.style.height = '600px';
//                 iframe.style.border = 'none';
//             }
//         }, 1000);
//     }
    
//     setLoading(loading, message = '') {
//         this.state.loading = loading;
//         this.state.currentMessage = message;
//     }
    
//     setError(error) {
//         this.state.error = error;
//         this.state.loading = false;
//     }
    
//     cleanup() {
//         if (this.embedInstance?.unmount) {
//             this.embedInstance.unmount();
//         }
//         if (this.containerRef.el) {
//             this.containerRef.el.innerHTML = '';
//         }
//     }
// }
 
// registry.category("fields").add("superset_dashboard", SupersetDashboardWidget);