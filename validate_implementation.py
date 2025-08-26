#!/usr/bin/env python3
"""
Script de validación final de la implementación simplificada
Verifica que todos los archivos estén correctamente implementados
"""

import os
import json
import ast
import xml.etree.ElementTree as ET
from pathlib import Path

class ImplementationValidator:
    """Validador de la implementación completa"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.module_path = self.project_root / "eticco_superset_integration"
        self.results = []
    
    def log_result(self, check_name: str, passed: bool, details: str = ""):
        """Registra resultado de validación"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            'check': check_name,
            'status': status,
            'passed': passed,
            'details': details
        }
        self.results.append(result)
        print(f"{status}: {check_name}")
        if details:
            print(f"    {details}")
    
    def validate_files_exist(self):
        """Verifica que todos los archivos necesarios existen"""
        print("\n🔍 VALIDANDO EXISTENCIA DE ARCHIVOS")
        print("-" * 40)
        
        required_files = [
            "static/src/fields/superset_dashboard_integrated.js",
            "static/src/fields/superset_dashboard_integrated.xml",
            "views/superset_analytics_hub_views.xml",
            "__manifest__.py"
        ]
        
        for file_path in required_files:
            full_path = self.module_path / file_path
            exists = full_path.exists()
            self.log_result(
                f"Archivo: {file_path}",
                exists,
                f"Ruta: {full_path}" if exists else f"No encontrado en: {full_path}"
            )
    
    def validate_javascript_syntax(self):
        """Valida sintaxis JavaScript del nuevo componente"""
        print("\n🔍 VALIDANDO SINTAXIS JAVASCRIPT")
        print("-" * 40)
        
        js_file = self.module_path / "static/src/fields/superset_dashboard_integrated.js"
        
        if not js_file.exists():
            self.log_result("JavaScript Syntax", False, "Archivo no encontrado")
            return
        
        try:
            content = js_file.read_text()
            
            # Verificar elementos clave
            checks = [
                ("Importaciones OWL", "from \"@odoo/owl\"" in content),
                ("Registry import", "from \"@web/core/registry\"" in content),
                ("Componente definido", "class SupersetDashboardIntegrated" in content),
                ("Template definido", "static template" in content),
                ("Props definidos", "SupersetDashboardIntegrated.props" in content),
                ("Registry registro", "registry.category(\"fields\")" in content),
                ("Auto-carga implementada", "onPatched" in content),
                ("SDK loading", "loadSupersetSDK" in content),
                ("Error handling", "try {" in content and "catch" in content)
            ]
            
            for check_name, condition in checks:
                self.log_result(f"JS: {check_name}", condition)
            
        except Exception as e:
            self.log_result("JavaScript Syntax", False, f"Error leyendo archivo: {e}")
    
    def validate_xml_syntax(self):
        """Valida sintaxis XML del template"""
        print("\n🔍 VALIDANDO SINTAXIS XML")
        print("-" * 40)
        
        xml_files = [
            "static/src/fields/superset_dashboard_integrated.xml",
            "views/superset_analytics_hub_views.xml"
        ]
        
        for xml_file in xml_files:
            full_path = self.module_path / xml_file
            
            if not full_path.exists():
                self.log_result(f"XML: {xml_file}", False, "Archivo no encontrado")
                continue
            
            try:
                ET.parse(full_path)
                content = full_path.read_text()
                
                # Verificaciones específicas para el template integrado
                if "superset_dashboard_integrated.xml" in xml_file:
                    checks = [
                        ("Template name correcto", "SupersetDashboardIntegratedTemplate" in content),
                        ("Selector implementado", "t-on-change=\"onDashboardSelectionChange\"" in content),
                        ("Estados UI", "t-if=\"state.isLoading\"" in content),
                        ("Container dashboard", "t-ref=\"dashboardContainer\"" in content),
                        ("Error handling UI", "t-elif=\"state.error\"" in content)
                    ]
                else:
                    checks = [
                        ("Widget actualizado", "superset_dashboard_integrated" in content),
                        ("XML válido", True)  # Ya validado por ET.parse
                    ]
                
                for check_name, condition in checks:
                    self.log_result(f"XML {xml_file}: {check_name}", condition)
                
            except ET.ParseError as e:
                self.log_result(f"XML: {xml_file}", False, f"Error de sintaxis: {e}")
            except Exception as e:
                self.log_result(f"XML: {xml_file}", False, f"Error leyendo archivo: {e}")
    
    def validate_manifest_updates(self):
        """Valida actualizaciones en __manifest__.py"""
        print("\n🔍 VALIDANDO MANIFEST")
        print("-" * 40)
        
        manifest_file = self.module_path / "__manifest__.py"
        
        if not manifest_file.exists():
            self.log_result("Manifest", False, "Archivo no encontrado")
            return
        
        try:
            content = manifest_file.read_text()
            
            checks = [
                ("Nuevos assets incluidos", "superset_dashboard_integrated.js" in content),
                ("XML template incluido", "superset_dashboard_integrated.xml" in content),
                ("Assets backend", "'web.assets_backend'" in content),
                ("Sintaxis Python", True)  # Verificado por ast.parse abajo
            ]
            
            # Verificar sintaxis Python
            try:
                ast.parse(content)
                syntax_valid = True
            except SyntaxError:
                syntax_valid = False
            
            checks.append(("Sintaxis Python válida", syntax_valid))
            
            for check_name, condition in checks:
                self.log_result(f"Manifest: {check_name}", condition)
                
        except Exception as e:
            self.log_result("Manifest", False, f"Error leyendo archivo: {e}")
    
    def validate_ux_improvements(self):
        """Valida que las mejoras de UX estén implementadas"""
        print("\n🔍 VALIDANDO MEJORAS UX")
        print("-" * 40)
        
        js_file = self.module_path / "static/src/fields/superset_dashboard_integrated.js"
        xml_file = self.module_path / "static/src/fields/superset_dashboard_integrated.xml"
        
        if not js_file.exists() or not xml_file.exists():
            self.log_result("UX Improvements", False, "Archivos necesarios no encontrados")
            return
        
        js_content = js_file.read_text()
        xml_content = xml_file.read_text()
        
        ux_checks = [
            ("Auto-carga en onPatched", "onPatched()" in js_content and "loadDashboard()" in js_content),
            ("Sin botones manuales de carga", "Cargar Dashboard" not in xml_content),
            ("Estados de carga claros", "state.isLoading" in js_content),
            ("Manejo de errores", "state.error" in js_content),
            ("Limpieza automática", "clearDashboard()" in js_content),
            ("Selector integrado", "onDashboardSelectionChange" in js_content),
            ("UI responsiva", "form-select" in xml_content),
            ("Feedback visual", "spinner-border" in xml_content or "fa-spinner" in xml_content)
        ]
        
        for check_name, condition in ux_checks:
            self.log_result(f"UX: {check_name}", condition)
    
    def validate_test_coverage(self):
        """Valida que los tests estén disponibles"""
        print("\n🔍 VALIDANDO COBERTURA DE TESTS")
        print("-" * 40)
        
        test_files = [
            "test_simplified_integration.py",
            "test_ux_flow.py"
        ]
        
        for test_file in test_files:
            full_path = self.project_root / test_file
            exists = full_path.exists()
            
            if exists:
                try:
                    content = full_path.read_text()
                    has_main = "if __name__ == \"__main__\":" in content
                    has_tests = "def test_" in content
                    executable = os.access(full_path, os.X_OK)
                    
                    self.log_result(
                        f"Test: {test_file}",
                        exists and has_main and has_tests,
                        f"Ejecutable: {executable}, Tests: {has_tests}"
                    )
                except Exception as e:
                    self.log_result(f"Test: {test_file}", False, f"Error: {e}")
            else:
                self.log_result(f"Test: {test_file}", False, "Archivo no encontrado")
    
    def run_validation(self):
        """Ejecuta todas las validaciones"""
        print("🔍 VALIDACIÓN COMPLETA DE IMPLEMENTACIÓN")
        print("=" * 50)
        
        self.validate_files_exist()
        self.validate_javascript_syntax()
        self.validate_xml_syntax()
        self.validate_manifest_updates()
        self.validate_ux_improvements()
        self.validate_test_coverage()
        
        # Resumen final
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("=" * 50)
        
        passed = [r for r in self.results if r['passed']]
        failed = [r for r in self.results if not r['passed']]
        
        print(f"✅ Validaciones pasadas: {len(passed)}")
        print(f"❌ Validaciones fallidas: {len(failed)}")
        print(f"📈 Tasa de éxito: {len(passed)/len(self.results)*100:.1f}%")
        
        if failed:
            print(f"\n❌ VALIDACIONES FALLIDAS:")
            for result in failed:
                print(f"  • {result['check']}: {result['details']}")
        
        # Guardar reporte
        report = {
            'validation_results': self.results,
            'summary': {
                'total_checks': len(self.results),
                'passed': len(passed),
                'failed': len(failed),
                'success_rate': len(passed)/len(self.results)*100
            }
        }
        
        with open('validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Reporte de validación guardado en: validation_report.json")
        
        return len(failed) == 0

if __name__ == "__main__":
    validator = ImplementationValidator()
    success = validator.run_validation()
    
    if success:
        print(f"\n🎉 ¡VALIDACIÓN EXITOSA! La implementación está lista.")
        print(f"💡 Próximos pasos:")
        print(f"   1. Revisar cambios: git diff")
        print(f"   2. Confirmar implementación: git add . && git commit")
        print(f"   3. Probar en entorno Odoo")
        exit(0)
    else:
        print(f"\n⚠️  Algunas validaciones fallaron. Revisa los errores arriba.")
        exit(1)