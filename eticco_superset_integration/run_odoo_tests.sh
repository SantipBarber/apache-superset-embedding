#!/bin/bash

# Script para ejecutar tests del módulo Superset con Odoo real
# Requiere tener Odoo instalado y configurado

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
ODOO_BIN="odoo-bin"
DB_NAME="superset_test_db"
MODULE_NAME="eticco_superset_integration"
ADDONS_PATH="."

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  TESTS MÓDULO SUPERSET - ODOO  ${NC}"
    echo -e "${BLUE}================================${NC}"
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

check_requirements() {
    print_step "Verificando requisitos..."
    
    # Verificar odoo-bin
    if ! command -v $ODOO_BIN &> /dev/null; then
        print_error "odoo-bin no encontrado. Instala Odoo primero."
        echo "Alternativamente, especifica la ruta: ODOO_BIN=/path/to/odoo-bin $0"
        exit 1
    fi
    
    # Verificar módulo
    if [ ! -d "$MODULE_NAME" ]; then
        print_error "Módulo $MODULE_NAME no encontrado en el directorio actual"
        exit 1
    fi
    
    # Verificar tests
    if [ ! -d "$MODULE_NAME/tests" ]; then
        print_error "Directorio tests no encontrado en $MODULE_NAME"
        exit 1
    fi
    
    print_success "Requisitos verificados"
}

create_test_db() {
    print_step "Creando base de datos de test..."
    
    # Eliminar DB si existe
    dropdb $DB_NAME 2>/dev/null || true
    
    # Crear nueva DB
    createdb $DB_NAME
    
    print_success "Base de datos $DB_NAME creada"
}

install_module() {
    print_step "Instalando módulo $MODULE_NAME..."
    
    $ODOO_BIN -d $DB_NAME -i $MODULE_NAME --addons-path=$ADDONS_PATH --stop-after-init --log-level=warn
    
    if [ $? -eq 0 ]; then
        print_success "Módulo instalado correctamente"
    else
        print_error "Error instalando módulo"
        exit 1
    fi
}

run_tests() {
    print_step "Ejecutando tests del módulo..."
    
    echo -e "${BLUE}Comando ejecutado:${NC}"
    echo "$ODOO_BIN -d $DB_NAME --addons-path=$ADDONS_PATH --test-enable --stop-after-init --log-level=info"
    echo ""
    
    $ODOO_BIN -d $DB_NAME --addons-path=$ADDONS_PATH --test-enable --stop-after-init --log-level=info
    
    TEST_EXIT_CODE=$?
    
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        print_success "Todos los tests pasaron"
    else
        print_error "Algunos tests fallaron (exit code: $TEST_EXIT_CODE)"
        return $TEST_EXIT_CODE
    fi
}

run_specific_test() {
    local test_file=$1
    print_step "Ejecutando test específico: $test_file"
    
    # Para tests específicos, usar --test-file
    $ODOO_BIN -d $DB_NAME --addons-path=$ADDONS_PATH --test-enable --test-file=$MODULE_NAME/tests/$test_file --stop-after-init --log-level=info
}

cleanup() {
    print_step "Limpiando..."
    dropdb $DB_NAME 2>/dev/null || true
    print_success "Limpieza completada"
}

show_usage() {
    echo -e "${BLUE}USO:${NC}"
    echo "  $0 [opciones] [test_específico]"
    echo ""
    echo -e "${BLUE}OPCIONES:${NC}"
    echo "  -h, --help          Mostrar esta ayuda"
    echo "  -d, --database      Nombre de la base de datos de test (default: $DB_NAME)"
    echo "  -a, --addons-path   Ruta de addons (default: $ADDONS_PATH)"
    echo "  -o, --odoo-bin      Ejecutable de Odoo (default: $ODOO_BIN)"
    echo "  --no-cleanup        No eliminar base de datos al final"
    echo ""
    echo -e "${BLUE}TESTS ESPECÍFICOS:${NC}"
    echo "  test_superset_utils.py      - Tests de utilidades"
    echo "  test_analytics_hub.py       - Tests del hub de analytics"
    echo "  test_configuration_flow.py  - Tests del flujo de configuración"
    echo "  test_integration.py         - Tests de integración"
    echo ""
    echo -e "${BLUE}EJEMPLOS:${NC}"
    echo "  $0                                    # Ejecutar todos los tests"
    echo "  $0 test_superset_utils.py             # Test específico"
    echo "  $0 -d my_test_db                      # Con DB personalizada"
    echo "  $0 --no-cleanup                       # Mantener DB después"
    echo ""
    echo -e "${BLUE}VARIABLES DE ENTORNO:${NC}"
    echo "  ODOO_BIN=/path/to/odoo-bin $0         # Odoo personalizado"
    echo "  ADDONS_PATH=/path/to/addons $0        # Addons path personalizado"
}

# Procesar argumentos
CLEANUP=true
SPECIFIC_TEST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -d|--database)
            DB_NAME="$2"
            shift 2
            ;;
        -a|--addons-path)
            ADDONS_PATH="$2"
            shift 2
            ;;
        -o|--odoo-bin)
            ODOO_BIN="$2"
            shift 2
            ;;
        --no-cleanup)
            CLEANUP=false
            shift
            ;;
        test_*.py)
            SPECIFIC_TEST="$1"
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
    
    # Verificar requisitos
    check_requirements
    
    # Crear DB de test
    create_test_db
    
    # Instalar módulo
    install_module
    
    # Ejecutar tests
    if [ -n "$SPECIFIC_TEST" ]; then
        run_specific_test "$SPECIFIC_TEST"
        TEST_RESULT=$?
    else
        run_tests
        TEST_RESULT=$?
    fi
    
    # Limpiar si es necesario
    if [ "$CLEANUP" = true ]; then
        cleanup
    else
        print_step "Base de datos $DB_NAME mantenida para inspección"
    fi
    
    # Resultado final
    echo ""
    if [ $TEST_RESULT -eq 0 ]; then
        print_success "¡TESTS COMPLETADOS EXITOSAMENTE!"
    else
        print_error "TESTS FALLIDOS"
    fi
    
    exit $TEST_RESULT
}

# Ejecutar solo si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi