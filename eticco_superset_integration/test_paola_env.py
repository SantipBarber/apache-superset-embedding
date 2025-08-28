#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar el módulo Superset en el entorno de Paola
Adaptado para Docker Compose con puerto 9179
"""

import requests
import json
import time
import sys
import os

# Configuración específica del entorno de Paola
ODOO_BASE_URL = "http://localhost:9179"
DB_NAME = "test_superset"
PROJECT_PATH = "/desarrollo/0000-TEST-ODOO/odoo-test"

class PaolaEnvironmentTester:
    def __init__(self):
        self.odoo_url = ODOO_BASE_URL
        self.db_name = DB_NAME
        
    def check_odoo_accessibility(self):
        """Verificar que Odoo esté accesible"""
        print(f"🔗 Verificando Odoo en {self.odoo_url}...")
        
        try:
            response = requests.get(f"{self.odoo_url}/web/database/selector", timeout=10)
            if response.status_code == 200:
                print("✅ Odoo está accesible")
                return True
            else:
                print(f"⚠️ Odoo responde con código {response.status_code}")
                return False
        except requests.ConnectionError:
            print("❌ Error: No se puede conectar con Odoo")
            print("💡 Soluciones:")
            print(f"   1. cd {PROJECT_PATH}")
            print("   2. docker-compose up -d")
            print("   3. docker-compose logs -f")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False
    
    def list_databases(self):
        """Listar bases de datos disponibles"""
        print("🗃️ Listando bases de datos disponibles...")
        
        try:
            data = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'service': 'db',
                    'method': 'list',
                    'args': []
                },
                'id': 1
            }
            
            response = requests.post(f"{self.odoo_url}/jsonrpc", json=data, timeout=15)
            result = response.json()
            
            if 'result' in result and isinstance(result['result'], list):
                databases = result['result']
                print(f"✅ Bases de datos encontradas: {databases}")
                
                if self.db_name in databases:
                    print(f"✅ Base de datos '{self.db_name}' está disponible")
                    return True
                else:
                    print(f"⚠️ Base de datos '{self.db_name}' no encontrada")
                    print(f"💡 Usa una de estas: {databases}")
                    
                    # Usar la primera disponible
                    if databases:
                        self.db_name = databases[0]
                        print(f"🔄 Usando '{self.db_name}' para las pruebas")
                        return True
                    return False
            else:
                print("⚠️ No se pudieron listar las bases de datos")
                return True  # Continuar de todas formas
                
        except Exception as e:
            print(f"⚠️ Error listando bases de datos: {e}")
            return True  # Continuar de todas formas
    
    def test_authentication(self, username="admin", password="admin"):
        """Probar autenticación"""
        print(f"🔑 Probando autenticación (usuario: {username})...")
        
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
            response = requests.post(f"{self.odoo_url}/jsonrpc", json=login_data, timeout=15)
            result = response.json()
            
            if result.get('result'):
                uid = result['result']
                print(f"✅ Autenticación exitosa (UID: {uid})")
                return uid
            else:
                print("❌ Error de autenticación")
                print(f"   Respuesta: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error en autenticación: {e}")
            return None
    
    def check_module_installed(self, uid):
        """Verificar si el módulo está instalado"""
        print("📦 Verificando instalación del módulo...")
        
        try:
            data = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'service': 'object',
                    'method': 'execute',
                    'args': [
                        self.db_name, uid, 'admin',
                        'ir.module.module',
                        'search_read',
                        [['name', '=', 'eticco_superset_integration']],
                        ['name', 'state', 'summary']
                    ]
                },
                'id': 1
            }
            
            response = requests.post(f"{self.odoo_url}/jsonrpc", json=data, timeout=15)
            result = response.json()
            
            if 'result' in result and result['result']:
                module_info = result['result'][0]
                state = module_info.get('state', 'unknown')
                print(f"✅ Módulo encontrado - Estado: {state}")
                
                if state == 'installed':
                    print("✅ Módulo está instalado y listo")
                    return True
                elif state == 'to install':
                    print("⚠️ Módulo marcado para instalación")
                    return False
                elif state == 'uninstalled':
                    print("⚠️ Módulo no está instalado")
                    print("💡 Instálalo desde: Apps → Buscar 'eticco_superset_integration'")
                    return False
                else:
                    print(f"⚠️ Estado desconocido: {state}")
                    return False
            else:
                print("❌ Módulo no encontrado")
                print("💡 Asegúrate de que el módulo esté en extra_addons/")
                return False
                
        except Exception as e:
            print(f"❌ Error verificando módulo: {e}")
            return False
    
    def test_module_functionality(self, uid):
        """Probar funcionalidad básica del módulo"""
        print("🧪 Probando funcionalidad básica del módulo...")
        
        try:
            # Intentar crear un registro de Analytics Hub
            data = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'service': 'object',
                    'method': 'execute',
                    'args': [
                        self.db_name, uid, 'admin',
                        'superset.analytics.hub',
                        'create',
                        {
                            'name': 'Test Dashboard',
                            'superset_dashboard_id': '1',
                            'description': 'Dashboard de prueba'
                        }
                    ]
                },
                'id': 1
            }
            
            response = requests.post(f"{self.odoo_url}/jsonrpc", json=data, timeout=15)
            result = response.json()
            
            if 'result' in result and result['result']:
                record_id = result['result']
                print(f"✅ Registro creado exitosamente (ID: {record_id})")
                
                # Probar método de obtención de datos
                test_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'service': 'object',
                        'method': 'execute',
                        'args': [
                            self.db_name, uid, 'admin',
                            'superset.analytics.hub',
                            'get_dashboard_data_for_js',
                            [record_id]
                        ]
                    },
                    'id': 1
                }
                
                test_response = requests.post(f"{self.odoo_url}/jsonrpc", json=test_data, timeout=15)
                test_result = test_response.json()
                
                if 'result' in test_result:
                    print("✅ Método get_dashboard_data_for_js funciona")
                    
                    # Limpiar - eliminar registro de prueba
                    delete_data = {
                        'jsonrpc': '2.0',
                        'method': 'call',
                        'params': {
                            'service': 'object',
                            'method': 'execute',
                            'args': [
                                self.db_name, uid, 'admin',
                                'superset.analytics.hub',
                                'unlink',
                                [record_id]
                            ]
                        },
                        'id': 1
                    }
                    
                    requests.post(f"{self.odoo_url}/jsonrpc", json=delete_data, timeout=10)
                    print("🧹 Registro de prueba eliminado")
                    
                    return True
                else:
                    print("❌ Error en método get_dashboard_data_for_js")
                    return False
            else:
                print("❌ No se pudo crear registro de prueba")
                print(f"   Respuesta completa: {result}")
                
                # Intentar obtener más detalles del error
                if 'error' in result:
                    error_info = result['error']
                    if isinstance(error_info, dict):
                        print(f"   Tipo error: {error_info.get('name', 'Unknown')}")
                        print(f"   Mensaje: {error_info.get('message', 'No message')}")
                        if 'data' in error_info and 'debug' in error_info['data']:
                            print(f"   Debug: {error_info['data']['debug']}")
                
                return False
                
        except Exception as e:
            print(f"❌ Error probando funcionalidad: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Ejecutar test completo del entorno"""
        print("🚀 INICIANDO TESTS COMPLETOS DEL ENTORNO DE PAOLA")
        print("=" * 70)
        print(f"📍 Proyecto: {PROJECT_PATH}")
        print(f"🌐 Odoo URL: {self.odoo_url}")
        print(f"🗃️ Base de datos: {self.db_name}")
        print("=" * 70)
        
        # Test 1: Accesibilidad de Odoo
        if not self.check_odoo_accessibility():
            print("\n❌ TESTS ABORTADOS: Odoo no accesible")
            return False
        
        # Test 2: Listar bases de datos
        if not self.list_databases():
            print("\n❌ TESTS ABORTADOS: Sin bases de datos")
            return False
        
        # Test 3: Autenticación
        uid = self.test_authentication()
        if not uid:
            print("\n❌ TESTS ABORTADOS: Fallo en autenticación")
            return False
        
        # Test 4: Módulo instalado
        if not self.check_module_installed(uid):
            print("\n⚠️ TESTS LIMITADOS: Módulo no instalado")
            print("\n💡 PRÓXIMOS PASOS:")
            print("   1. Ir a Odoo → Apps")
            print("   2. Buscar 'eticco_superset_integration'")
            print("   3. Hacer clic en 'Instalar'")
            print("   4. Re-ejecutar este script")
            return False
        
        # Test 5: Funcionalidad básica
        if not self.test_module_functionality(uid):
            print("\n❌ TESTS FALLIDOS: Error en funcionalidad")
            return False
        
        # Test completo exitoso
        print("\n" + "=" * 70)
        print("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("=" * 70)
        print("🎯 ENTORNO LISTO PARA:")
        print("   • Tests de integración")
        print("   • Tests de escenarios de error")
        print("   • Desarrollo y debugging")
        print("   • Pruebas de usuario final")
        
        return True


def main():
    """Función principal"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Script de tests para el entorno de Paola

DESCRIPCIÓN:
  Verifica que el entorno Docker Compose esté correctamente configurado
  y que el módulo eticco_superset_integration funcione correctamente.

USO:
  python3 test_paola_env.py

REQUISITOS:
  - Docker y docker-compose corriendo
  - Odoo accesible en http://localhost:9179
  - Módulo en /desarrollo/0000-TEST-ODOO/odoo-test/extra_addons/

COMANDOS ÚTILES:
  cd /desarrollo/0000-TEST-ODOO/odoo-test/
  docker-compose up -d          # Iniciar Odoo
  docker-compose logs -f        # Ver logs
  docker-compose down           # Detener Odoo
        """)
        return
    
    print("🔧 Entorno: Paola - Docker Compose - Puerto 9179")
    print("📁 Proyecto: /desarrollo/0000-TEST-ODOO/odoo-test/")
    print()
    
    tester = PaolaEnvironmentTester()
    success = tester.run_comprehensive_test()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()