#!/bin/bash

# Script para ejecutar tests del módulo Superset en el entorno de Paola
# Adaptado para Docker Compose en /desarrollo/0000-TEST-ODOO/odoo-test/

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración específica del entorno de Paola
PROJECT_PATH="/desarrollo/0000-TEST-ODOO/odoo-test"
MODULE_PATH="$PROJECT_PATH/extra_addons/eticco_superset_integration"
ODOO_URL="http://localhost:9179"
DB_NAME="${DB_NAME:-test_superset}"
MODULE_NAME="eticco_superset_integration"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  TESTS MÓDULO SUPERSET - PAOLA ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}Entorno: Docker Compose${NC}"
    echo -e "${BLUE}Puerto: 9179${NC}"
    echo -e "${BLUE}Proyecto: $PROJECT_PATH${NC}"
}

print_step() {
    echo -e "${YELLOW}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_environment() {
    print_step "Verificando entorno..."
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "$PROJECT_PATH/docker-compose.yaml" ]; then
        print_error "docker-compose.yaml no encontrado en $PROJECT_PATH"
        echo "Ejecuta desde: cd $PROJECT_PATH && $0"
        exit 1
    fi
    
    # Verificar módulo
    if [ ! -d "$MODULE_PATH" ]; then
        print_error "Módulo $MODULE_NAME no encontrado en $MODULE_PATH"
        exit 1
    fi
    
    # Verificar tests
    if [ ! -d "$MODULE_PATH/tests" ]; then
        print_error "Directorio tests no encontrado en $MODULE_PATH"
        exit 1
    fi
    
    print_success "Entorno verificado"
}

check_odoo_running() {
    print_step "Verificando Odoo en $ODOO_URL..."
    
    if curl -s -I "$ODOO_URL/web/database/selector" | grep -q "200 OK"; then
        print_success "Odoo está corriendo y accesible"
        return 0
    else
        print_error "Odoo no está accesible en $ODOO_URL"
        echo ""
        echo "💡 Para iniciar Odoo:"
        echo "   cd $PROJECT_PATH"
        echo "   docker-compose up -d"
        echo ""
        echo "💡 Para ver logs:"
        echo "   docker-compose logs -f"
        return 1
    fi
}

run_docker_tests() {
    print_step "Ejecutando tests via Docker Compose..."
    
    # Cambiar al directorio del proyecto
    cd "$PROJECT_PATH"
    
    # Comando para ejecutar tests dentro del contenedor
    local test_cmd="python3 -m pytest /opt/odoo/extra_addons/eticco_superset_integration/tests/ -v --tb=short"
    
    echo -e "${BLUE}Comando ejecutado:${NC}"
    echo "docker-compose exec odoo $test_cmd"
    echo ""
    
    # Ejecutar tests
    if docker-compose exec -T odoo bash -c "$test_cmd"; then
        print_success "Tests ejecutados via Docker"
        return 0
    else
        # Fallback: intentar con python unittest
        print_step "Reintentando con unittest..."
        local unittest_cmd="cd /opt/odoo/extra_addons/eticco_superset_integration && python3 -m unittest discover tests/ -v"
        
        if docker-compose exec -T odoo bash -c "$unittest_cmd"; then
            print_success "Tests ejecutados con unittest"
            return 0
        else
            print_error "Error ejecutando tests"
            return 1
        fi
    fi
}

run_odoo_internal_tests() {
    print_step "Ejecutando tests con framework interno de Odoo..."
    
    cd "$PROJECT_PATH"
    
    # Usar el framework de tests interno de Odoo
    local odoo_test_cmd="odoo-bin -d $DB_NAME --test-enable --stop-after-init --log-level=info --addons-path=/opt/odoo/extra_addons -i $MODULE_NAME"
    
    echo -e "${BLUE}Comando ejecutado:${NC}"
    echo "docker-compose exec odoo $odoo_test_cmd"
    echo ""
    
    if docker-compose exec -T odoo bash -c "$odoo_test_cmd"; then
        print_success "Tests de Odoo completados"
        return 0
    else
        print_error "Error en tests de Odoo"
        return 1
    fi
}

run_standalone_tests() {
    print_step "Ejecutando tests standalone (sin Odoo)..."
    
    cd "$MODULE_PATH"
    
    # Tests que no requieren Odoo corriendo
    local python_tests=(
        "test_production_error_scenarios.py"
        # Agregar otros tests standalone aquí
    )
    
    for test_file in "${python_tests[@]}"; do
        if [ -f "$test_file" ]; then
            print_step "Ejecutando $test_file..."
            
            # Modificar temporalmente la URL para el entorno de Paola
            sed -i.bak 's|http://localhost:8069|http://localhost:9179|g' "$test_file"
            
            if python3 "$test_file" "$ODOO_URL" "$DB_NAME"; then
                print_success "$test_file completado"
            else
                print_error "Error en $test_file"
            fi
            
            # Restaurar archivo original
            mv "$test_file.bak" "$test_file" 2>/dev/null || true
        fi
    done
}

install_test_dependencies() {
    print_step "Instalando dependencias de test..."
    
    cd "$PROJECT_PATH"
    
    # Instalar pytest y otras dependencias en el contenedor
    local deps_cmd="pip3 install pytest requests"
    
    if docker-compose exec -T odoo bash -c "$deps_cmd"; then
        print_success "Dependencias instaladas"
    else
        print_error "Error instalando dependencias"
    fi
}

show_usage() {
    echo -e "${BLUE}USO:${NC}"
    echo "  $0 [opciones]"
    echo ""
    echo -e "${BLUE}OPCIONES:${NC}"
    echo "  -h, --help          Mostrar esta ayuda"
    echo "  --docker            Solo tests via Docker (default)"
    echo "  --odoo              Tests con framework interno Odoo"
    echo "  --standalone        Solo tests standalone"
    echo "  --all               Todos los tipos de tests"
    echo "  --install-deps      Instalar dependencias primero"
    echo ""
    echo -e "${BLUE}EJEMPLOS:${NC}"
    echo "  $0                      # Tests via Docker"
    echo "  $0 --all               # Todos los tests"
    echo "  $0 --standalone        # Solo tests standalone"
    echo ""
    echo -e "${BLUE}REQUISITOS:${NC}"
    echo "  - Docker y docker-compose instalados"
    echo "  - Proyecto en: $PROJECT_PATH"
    echo "  - Odoo corriendo en puerto 9179"
}

# Procesar argumentos
TEST_TYPE="docker"
INSTALL_DEPS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        --docker)
            TEST_TYPE="docker"
            shift
            ;;
        --odoo)
            TEST_TYPE="odoo"
            shift
            ;;
        --standalone)
            TEST_TYPE="standalone"
            shift
            ;;
        --all)
            TEST_TYPE="all"
            shift
            ;;
        --install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        *)
            print_error "Opción desconocida: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Script principal
main() {
    print_header
    
    # Verificaciones
    check_environment
    
    if [ "$TEST_TYPE" != "standalone" ]; then
        check_odoo_running || exit 1
    fi
    
    # Instalar dependencias si se solicita
    if [ "$INSTALL_DEPS" = true ]; then
        install_test_dependencies
    fi
    
    # Ejecutar tests según el tipo
    case $TEST_TYPE in
        "docker")
            run_docker_tests
            ;;
        "odoo")
            run_odoo_internal_tests
            ;;
        "standalone")
            run_standalone_tests
            ;;
        "all")
            print_step "Ejecutando todos los tipos de tests..."
            run_standalone_tests
            echo ""
            run_docker_tests
            echo ""
            run_odoo_internal_tests
            ;;
    esac
    
    TEST_RESULT=$?
    
    # Resultado final
    echo ""
    if [ $TEST_RESULT -eq 0 ]; then
        print_success "¡TESTS COMPLETADOS EXITOSAMENTE!"
    else
        print_error "ALGUNOS TESTS FALLARON"
    fi
    
    exit $TEST_RESULT
}

# Ejecutar solo si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi