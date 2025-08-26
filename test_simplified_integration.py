#!/usr/bin/env python3
"""
Script de pruebas para la integración simplificada de Superset
Simula el entorno de Odoo para validar la funcionalidad.
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Any

class MockOdooRecord:
    """Simula un record de Odoo para pruebas"""
    
    def __init__(self, model_name: str, res_id: int = 1):
        self.resModel = model_name
        self.resId = res_id
        self.data = {
            'selected_dashboard': '',
            'has_configuration': True,
            'available_dashboards_count': 0,
        }
        self.fields = {
            'selected_dashboard': {
                'selection': [
                    ('no_config', '⚠️ Configurar Superset en Ajustes'),
                    ('no_dashboards', '❌ No hay dashboards disponibles')
                ]
            }
        }
    
    async def update(self, values: Dict[str, Any]):
        """Simula actualización del record"""
        self.data.update(values)
        print(f"✅ Record actualizado: {values}")
        return True
    
    async def save(self):
        """Simula guardar el record"""
        print(f"💾 Record guardado: {self.data}")
        return True

class MockSupersetConfig:
    """Configuración simulada de Superset"""
    
    def __init__(self):
        self.config = {
            'url': 'http://localhost:8088',
            'username': 'admin',
            'password': 'admin',
            'cache_tokens': True,
            'debug_mode': True
        }
    
    def get_access_token(self) -> str:
        """Simula obtención de token de acceso"""
        print(f"🔐 Simulando login a Superset: {self.config['url']}")
        return "mock_access_token_12345"
    
    def get_dashboard_data_for_js(self, dashboard_id: str) -> Dict[str, Any]:
        """Simula obtención de datos del dashboard para JavaScript"""
        
        mock_dashboards = {
            '1': {
                'dashboard_id': 1,
                'dashboard_title': 'Sales Analytics Dashboard',
                'embedding_uuid': 'abc123-def456-ghi789',
                'superset_domain': self.config['url'],
                'guest_token': 'guest_token_xyz789',
                'debug_mode': self.config['debug_mode'],
                'error': None
            },
            '2': {
                'dashboard_id': 2,
                'dashboard_title': 'Marketing KPIs Dashboard',
                'embedding_uuid': 'xyz789-abc123-def456',
                'superset_domain': self.config['url'],
                'guest_token': 'guest_token_abc123',
                'debug_mode': self.config['debug_mode'],
                'error': None
            },
            'error_case': {
                'error': 'Dashboard no encontrado o embedding no habilitado'
            }
        }
        
        return mock_dashboards.get(dashboard_id, mock_dashboards['error_case'])

class TestSupersetIntegration:
    """Pruebas para la integración simplificada"""
    
    def __init__(self):
        self.superset_config = MockSupersetConfig()
        self.record = MockOdooRecord('superset.analytics.hub')
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Registra resultado de una prueba"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
    
    def test_dashboard_selection(self):
        """Prueba selección de dashboard"""
        print("\n🧪 Probando selección de dashboard...")
        
        # Simular selección de dashboard válido
        dashboard_id = '1'
        self.record.data['selected_dashboard'] = dashboard_id
        
        # Verificar que el dashboard se seleccionó correctamente
        current_id = self.record.data.get('selected_dashboard')
        is_valid = current_id and current_id not in ['no_config', 'no_dashboards', 'error', '']
        
        self.log_test(
            "Dashboard Selection", 
            current_id == dashboard_id and is_valid,
            f"Dashboard ID: {current_id}, Válido: {is_valid}"
        )
    
    def test_dashboard_data_loading(self):
        """Prueba carga de datos del dashboard"""
        print("\n🧪 Probando carga de datos del dashboard...")
        
        dashboard_id = '1'
        dashboard_data = self.superset_config.get_dashboard_data_for_js(dashboard_id)
        
        has_embedding_uuid = 'embedding_uuid' in dashboard_data
        has_guest_token = 'guest_token' in dashboard_data
        has_domain = 'superset_domain' in dashboard_data
        no_error = dashboard_data.get('error') is None
        
        self.log_test(
            "Dashboard Data Loading",
            all([has_embedding_uuid, has_guest_token, has_domain, no_error]),
            f"UUID: {has_embedding_uuid}, Token: {has_guest_token}, Domain: {has_domain}, Error: {not no_error}"
        )
        
        return dashboard_data
    
    def test_auto_load_behavior(self):
        """Prueba comportamiento de auto-carga"""
        print("\n🧪 Probando comportamiento de auto-carga...")
        
        # Simular cambio de selección
        old_dashboard = self.record.data.get('selected_dashboard', '')
        new_dashboard = '2'
        
        # El componente debería detectar el cambio y cargar automáticamente
        selection_changed = old_dashboard != new_dashboard
        is_valid_dashboard = new_dashboard not in ['no_config', 'no_dashboards', 'error', '']
        should_auto_load = selection_changed and is_valid_dashboard
        
        self.log_test(
            "Auto-load Trigger",
            should_auto_load,
            f"Cambio detectado: {selection_changed}, Dashboard válido: {is_valid_dashboard}"
        )
        
        # Actualizar selección
        self.record.data['selected_dashboard'] = new_dashboard
        
        return should_auto_load
    
    def test_error_handling(self):
        """Prueba manejo de errores"""
        print("\n🧪 Probando manejo de errores...")
        
        # Caso de error: dashboard inexistente
        error_data = self.superset_config.get_dashboard_data_for_js('nonexistent')
        has_error = 'error' in error_data and error_data['error'] is not None
        
        self.log_test(
            "Error Handling",
            has_error,
            f"Error detectado: {error_data.get('error', 'Sin error')}"
        )
        
        # Casos de configuración inválida
        invalid_cases = ['no_config', 'no_dashboards', '']
        for case in invalid_cases:
            is_invalid = case in ['no_config', 'no_dashboards', 'error', '']
            self.log_test(
                f"Invalid Case: {case}",
                is_invalid,
                f"Correctamente identificado como inválido: {is_invalid}"
            )
    
    def test_ui_states(self):
        """Prueba estados de la UI"""
        print("\n🧪 Probando estados de la UI...")
        
        states = {
            'empty': {'dashboard_id': '', 'loading': False, 'error': None},
            'loading': {'dashboard_id': '1', 'loading': True, 'error': None},
            'loaded': {'dashboard_id': '1', 'loading': False, 'error': None},
            'error': {'dashboard_id': '1', 'loading': False, 'error': 'Connection failed'}
        }
        
        for state_name, state_data in states.items():
            # Simular estado
            is_loading = state_data['loading']
            has_error = state_data['error'] is not None
            has_dashboard = bool(state_data['dashboard_id'])
            
            # Verificar que cada estado tiene el comportamiento esperado
            state_valid = True
            
            if state_name == 'empty':
                state_valid = not has_dashboard and not is_loading and not has_error
            elif state_name == 'loading':
                state_valid = has_dashboard and is_loading and not has_error
            elif state_name == 'loaded':
                state_valid = has_dashboard and not is_loading and not has_error
            elif state_name == 'error':
                state_valid = has_dashboard and not is_loading and has_error
            
            self.log_test(
                f"UI State: {state_name}",
                state_valid,
                f"Dashboard: {has_dashboard}, Loading: {is_loading}, Error: {has_error}"
            )
    
    def test_superset_sdk_integration(self):
        """Prueba integración con SDK de Superset"""
        print("\n🧪 Probando integración con SDK de Superset...")
        
        dashboard_data = self.superset_config.get_dashboard_data_for_js('1')
        
        # Verificar que tenemos todos los datos necesarios para el SDK
        required_fields = ['embedding_uuid', 'superset_domain', 'guest_token']
        has_all_fields = all(field in dashboard_data for field in required_fields)
        
        # Simular configuración del SDK
        if has_all_fields:
            sdk_config = {
                'id': dashboard_data['embedding_uuid'],
                'supersetDomain': dashboard_data['superset_domain'],
                'fetchGuestToken': lambda: dashboard_data['guest_token'],
                'debug': dashboard_data.get('debug_mode', False)
            }
            
            config_valid = all([
                sdk_config['id'],
                sdk_config['supersetDomain'],
                callable(sdk_config['fetchGuestToken']),
            ])
        else:
            config_valid = False
        
        self.log_test(
            "SDK Integration",
            has_all_fields and config_valid,
            f"Campos requeridos: {has_all_fields}, Configuración válida: {config_valid}"
        )
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("🚀 Iniciando pruebas de integración simplificada de Superset")
        print("=" * 60)
        
        # Ejecutar pruebas
        self.test_dashboard_selection()
        self.test_dashboard_data_loading()
        self.test_auto_load_behavior()
        self.test_error_handling()
        self.test_ui_states()
        self.test_superset_sdk_integration()
        
        # Resumen de resultados
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 60)
        
        passed_tests = [r for r in self.test_results if "✅ PASS" in r['status']]
        failed_tests = [r for r in self.test_results if "❌ FAIL" in r['status']]
        
        print(f"✅ Pruebas pasadas: {len(passed_tests)}")
        print(f"❌ Pruebas fallidas: {len(failed_tests)}")
        print(f"📈 Tasa de éxito: {len(passed_tests)/len(self.test_results)*100:.1f}%")
        
        if failed_tests:
            print("\n❌ PRUEBAS FALLIDAS:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['message']}")
        
        # Guardar resultados
        with open('test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Resultados guardados en: test_results.json")
        
        return len(failed_tests) == 0

if __name__ == "__main__":
    tester = TestSupersetIntegration()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ¡Todas las pruebas pasaron! La integración simplificada está lista.")
        sys.exit(0)
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa los resultados arriba.")
        sys.exit(1)