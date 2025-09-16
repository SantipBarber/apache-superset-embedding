#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar escenarios de error de producción
Simula diferentes fallos que pueden ocurrir en producción
"""

import requests
import json
import time
import sys
import os

# URL base de tu Odoo (ajusta según tu configuración)
ODOO_BASE_URL = "http://localhost:8069"
DB_NAME = "test_db"  # Ajusta según tu base de datos de prueba

class ProductionErrorTester:
    def __init__(self, odoo_url, db_name):
        self.odoo_url = odoo_url
        self.db_name = db_name
        self.session_id = None
        
    def authenticate(self, username="admin", password="admin"):
        """Autenticar con Odoo"""
        print(f"🔑 Autenticando con Odoo en {self.odoo_url}...")
        
        login_data = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'service': 'common',
                'method': 'authenticate',
                'args': [self.db_name, username, password, {}]
            },
            'id': 1
        }
        
        try:
            response = requests.post(f"{self.odoo_url}/jsonrpc", json=login_data)
            result = response.json()
            
            if result.get('result'):
                print("✅ Autenticación exitosa")
                return True
            else:
                print("❌ Error de autenticación:", result)
                return False
                
        except Exception as e:
            print(f"❌ Error conectando con Odoo: {e}")
            return False
    
    def test_scenario_1_broken_connection(self):
        """Escenario 1: Conexión rota - Superset offline"""
        print("\n" + "="*60)
        print("🧪 ESCENARIO 1: Conexión rota (Superset offline)")
        print("="*60)
        
        # Configurar URL inválida para simular servidor offline
        invalid_config = {
            'superset.url': 'http://invalid-superset-server.com:8088',
            'superset.username': 'admin',
            'superset.password': 'admin',
            'superset.timeout': '10'
        }
        
        print("📝 Configurando URL inválida para simular servidor offline...")
        self._update_config_parameters(invalid_config)
        
        print("🔄 Probando carga de dashboard con servidor offline...")
        result = self._test_dashboard_load()
        
        print("📊 Resultado esperado:")
        print("  - Error tipo: connection_error")
        print("  - Mensaje: servidor no disponible")
        print("  - Acción: verificar servidor")
        print(f"📊 Resultado obtenido: {result}")
        
        return result
    
    def test_scenario_2_invalid_credentials(self):
        """Escenario 2: Credenciales inválidas"""
        print("\n" + "="*60)
        print("🧪 ESCENARIO 2: Credenciales inválidas")
        print("="*60)
        
        # Configurar credenciales incorrectas
        invalid_config = {
            'superset.url': 'http://localhost:8088',  # Asume servidor local funcional
            'superset.username': 'invalid_user',
            'superset.password': 'wrong_password',
            'superset.timeout': '10'
        }
        
        print("📝 Configurando credenciales inválidas...")
        self._update_config_parameters(invalid_config)
        
        print("🔄 Probando autenticación con credenciales incorrectas...")
        result = self._test_dashboard_load()
        
        print("📊 Resultado esperado:")
        print("  - Error tipo: auth_error")
        print("  - Mensaje: credenciales incorrectas")
        print("  - Acción: verificar credenciales")
        print(f"📊 Resultado obtenido: {result}")
        
        return result
    
    def test_scenario_3_timeout_error(self):
        """Escenario 3: Timeout de conexión"""
        print("\n" + "="*60)
        print("🧪 ESCENARIO 3: Timeout de conexión")
        print("="*60)
        
        # Configurar timeout muy bajo para forzar timeout
        timeout_config = {
            'superset.url': 'http://httpstat.us/200?sleep=5000',  # Simula respuesta lenta
            'superset.username': 'admin',
            'superset.password': 'admin',
            'superset.timeout': '1'  # 1 segundo timeout
        }
        
        print("📝 Configurando timeout muy bajo...")
        self._update_config_parameters(timeout_config)
        
        print("🔄 Probando conexión con timeout...")
        result = self._test_dashboard_load()
        
        print("📊 Resultado esperado:")
        print("  - Error tipo: timeout_error")
        print("  - Mensaje: timeout de conexión")
        print("  - Acción: reintentar más tarde")
        print(f"📊 Resultado obtenido: {result}")
        
        return result
    
    def test_scenario_4_server_error(self):
        """Escenario 4: Error del servidor (HTTP 500)"""
        print("\n" + "="*60)
        print("🧪 ESCENARIO 4: Error del servidor (HTTP 500)")
        print("="*60)
        
        # Usar URL que devuelve HTTP 500
        server_error_config = {
            'superset.url': 'http://httpstat.us/500',
            'superset.username': 'admin',
            'superset.password': 'admin',
            'superset.timeout': '10'
        }
        
        print("📝 Configurando URL que devuelve HTTP 500...")
        self._update_config_parameters(server_error_config)
        
        print("🔄 Probando conexión que devuelve error 500...")
        result = self._test_dashboard_load()
        
        print("📊 Resultado esperado:")
        print("  - Error tipo: server_error")
        print("  - Mensaje: error interno del servidor")
        print("  - Acción: contactar administrador")
        print(f"📊 Resultado obtenido: {result}")
        
        return result
    
    def test_scenario_5_no_configuration(self):
        """Escenario 5: Sin configuración"""
        print("\n" + "="*60)
        print("🧪 ESCENARIO 5: Sin configuración")
        print("="*60)
        
        # Limpiar configuración
        empty_config = {
            'superset.url': '',
            'superset.username': '',
            'superset.password': '',
            'superset.timeout': '30'
        }
        
        print("📝 Limpiando configuración...")
        self._update_config_parameters(empty_config)
        
        print("🔄 Probando carga sin configuración...")
        result = self._test_dashboard_load()
        
        print("📊 Resultado esperado:")
        print("  - Error tipo: config_error")
        print("  - Mensaje: configuración incompleta")
        print("  - Acción: ir a ajustes")
        print(f"📊 Resultado obtenido: {result}")
        
        return result
    
    def _update_config_parameters(self, config_dict):
        """Actualizar parámetros de configuración"""
        for key, value in config_dict.items():
            data = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'service': 'object',
                    'method': 'execute',
                    'args': [
                        self.db_name, 1, 'admin',  # uid, password
                        'ir.config_parameter',
                        'set_param',
                        key, str(value)
                    ]
                },
                'id': 1
            }
            
            try:
                requests.post(f"{self.odoo_url}/jsonrpc", json=data)
            except Exception as e:
                print(f"⚠️ Error actualizando {key}: {e}")
    
    def _test_dashboard_load(self):
        """Probar carga de dashboard"""
        # Simular llamada al método get_dashboard_data_for_js
        data = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'service': 'object',
                'method': 'execute',
                'args': [
                    self.db_name, 1, 'admin',  # uid, password
                    'superset.analytics.hub',
                    'get_dashboard_data_for_js',
                    [1]  # record id
                ]
            },
            'id': 1
        }
        
        try:
            response = requests.post(f"{self.odoo_url}/jsonrpc", json=data, timeout=30)
            result = response.json()
            
            if 'result' in result:
                return result['result']
            else:
                return {'error': 'Error en respuesta JSON', 'details': result}
                
        except Exception as e:
            return {'error': f'Exception durante test: {str(e)}'}
    
    def run_all_tests(self):
        """Ejecutar todos los escenarios de prueba"""
        print("🚀 INICIANDO PRUEBAS DE ESCENARIOS DE ERROR EN PRODUCCIÓN")
        print("=" * 80)
        
        if not self.authenticate():
            print("❌ No se pudo autenticar. Verifica la configuración de Odoo.")
            return
        
        scenarios = [
            self.test_scenario_1_broken_connection,
            self.test_scenario_2_invalid_credentials,
            self.test_scenario_3_timeout_error,
            self.test_scenario_4_server_error,
            self.test_scenario_5_no_configuration
        ]
        
        results = []
        for i, scenario in enumerate(scenarios, 1):
            try:
                result = scenario()
                results.append(result)
                print(f"✅ Escenario {i} completado")
            except Exception as e:
                print(f"❌ Error en escenario {i}: {e}")
                results.append({'error': str(e)})
            
            time.sleep(2)  # Pausa entre tests
        
        # Resumen final
        print("\n" + "="*80)
        print("📋 RESUMEN DE RESULTADOS")
        print("="*80)
        
        for i, result in enumerate(results, 1):
            print(f"\n🧪 Escenario {i}:")
            if isinstance(result, dict) and 'error' in result:
                error_type = result.get('error_type', 'unknown')
                user_message = result.get('user_message', result.get('error', 'Error desconocido'))
                action_required = result.get('action_required', 'N/A')
                
                print(f"   ❌ Error detectado: {error_type}")
                print(f"   💬 Mensaje: {user_message}")
                print(f"   🔧 Acción: {action_required}")
            else:
                print(f"   ✅ Resultado: {result}")


def main():
    """Función principal"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Uso: python test_production_error_scenarios.py [odoo_url] [db_name]

Parámetros:
  odoo_url    URL de Odoo (default: http://localhost:8069)
  db_name     Nombre de base de datos (default: test_db)

Ejemplos:
  python test_production_error_scenarios.py
  python test_production_error_scenarios.py http://localhost:8069 my_db
        """)
        return
    
    odoo_url = sys.argv[1] if len(sys.argv) > 1 else ODOO_BASE_URL
    db_name = sys.argv[2] if len(sys.argv) > 2 else DB_NAME
    
    print(f"🎯 Configuración:")
    print(f"   Odoo URL: {odoo_url}")
    print(f"   DB Name: {db_name}")
    print()
    
    tester = ProductionErrorTester(odoo_url, db_name)
    tester.run_all_tests()


if __name__ == "__main__":
    main()