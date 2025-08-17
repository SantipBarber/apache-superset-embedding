#!/bin/bash

# setup_embedding.sh
# Script principal para configurar embedding en Superset
# Versión mejorada con todas las lecciones aprendidas

# Configuración
SUPERSET_URL="http://192.168.1.137:8088"
USERNAME="admin"
PASSWORD="admin"
# ⚠️ IMPORTANTE: URLs DEBEN terminar en barra final "/"
ALLOWED_DOMAINS='["http://192.168.1.137:3000/", "http://192.168.1.137:3001/", "http://localhost:3000/", "http://localhost:3001/", "http://localhost:8080/", "http://localhost:8069/", "http://192.168.1.137:8069/"]'

echo "🚀 Configurando embedding en Superset..."

# Función para extraer código HTTP (compatible con macOS)
extract_http_code() {
    local response="$1"
    echo "$response" | tail -1
}

# Función para extraer body (compatible con macOS)
extract_body() {
    local response="$1"
    local line_count=$(echo "$response" | wc -l | tr -d ' ')
    local body_lines=$((line_count - 1))
    if [ $body_lines -gt 0 ]; then
        echo "$response" | head -n $body_lines
    else
        echo ""
    fi
}

# Función para debug de respuestas
debug_response() {
    local response="$1"
    local context="$2"
    
    echo "🐛 DEBUG [$context]:"
    echo "   Longitud de respuesta: ${#response}"
    echo "   Primeros 200 caracteres: ${response:0:200}"
    if echo "$response" | grep -q "<!DOCTYPE\|<html"; then
        echo "   ⚠️  Respuesta parece ser HTML (error de servidor)"
    elif [ -n "$response" ] && echo "$response" | jq . >/dev/null 2>&1; then
        echo "   ✅ Respuesta es JSON válido"
    else
        echo "   ❌ Respuesta no es JSON válido o está vacía"
    fi
    echo "---"
}

# Función para probar conectividad básica
test_basic_connectivity() {
    echo "🔌 Probando conectividad básica..."
    
    # Probar endpoint de salud
    local health_response=$(curl -s -w "\n%{http_code}" "${SUPERSET_URL}/health" 2>&1)
    local health_code=$(extract_http_code "$health_response")
    local health_body=$(extract_body "$health_response")
    
    echo "📡 Health check - HTTP $health_code"
    
    if [ "$health_code" = "200" ]; then
        echo "✅ Superset responde correctamente"
        echo "   Respuesta: $health_body"
    else
        echo "❌ Superset no responde correctamente"
        echo "   Respuesta: $health_body"
        return 1
    fi
    
    # Probar acceso a la página principal
    local main_response=$(curl -s -w "\n%{http_code}" "${SUPERSET_URL}/" 2>&1)
    local main_code=$(extract_http_code "$main_response")
    
    echo "📡 Página principal - HTTP $main_code"
    
    if [ "$main_code" = "200" ] || [ "$main_code" = "302" ]; then
        echo "✅ Página principal accesible"
    else
        echo "⚠️  Problema con página principal (esto puede ser normal)"
    fi
}

# Función para hacer login y obtener token
get_auth_token() {
    echo "📝 Obteniendo token de autenticación..."
    
    # Intentar login (simplificado, sabemos que funciona)
    local response=$(curl -s -w "\n%{http_code}" -X POST \
        "${SUPERSET_URL}/api/v1/security/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\", \"provider\": \"db\"}")
    
    local http_code=$(extract_http_code "$response")
    local body=$(extract_body "$response")
    
    echo "📡 Respuesta de login - HTTP $http_code"
    
    # Debug más simple para identificar el problema
    echo "🐛 DEBUG LOGIN:"
    echo "   Response length: ${#response}"
    echo "   HTTP Code: $http_code"
    echo "   Body length: ${#body}"
    echo "   Body preview: ${body:0:100}..."
    
    if [ "$http_code" != "200" ]; then
        echo "❌ Error HTTP $http_code en login"
        echo "Respuesta completa: $body"
        return 1
    fi
    
    # Verificar si tenemos JSON válido
    if [ -z "$body" ]; then
        echo "❌ Error: Respuesta de login está vacía"
        echo "🔍 Raw response: '$response'"
        return 1
    fi
    
    # Verificar que es JSON válido antes de usar jq
    if ! echo "$body" | jq . >/dev/null 2>&1; then
        echo "❌ Error: Respuesta de login no es JSON válido"
        echo "Body content: '$body'"
        echo "Raw response: '$response'"
        return 1
    fi
    
    local token=$(echo "$body" | jq -r '.access_token // empty' 2>/dev/null)
    
    if [ -z "$token" ] || [ "$token" = "null" ]; then
        echo "❌ Error: No se encontró access_token en la respuesta"
        echo "Body JSON: $body"
        echo "Available keys: $(echo "$body" | jq -r 'keys[]' 2>/dev/null)"
        return 1
    fi
    
    echo "✅ Token obtenido exitosamente: ${token:0:30}..."
    echo "$token"
}

# Función para obtener dashboards
get_dashboards() {
    local token=$1
    echo "📊 Obteniendo lista de dashboards..."
    
    local response=$(curl -s -w "\n%{http_code}" -X GET \
        "${SUPERSET_URL}/api/v1/dashboard/" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" 2>&1)
    
    local http_code=$(extract_http_code "$response")
    local body=$(extract_body "$response")
    
    echo "📡 Respuesta de dashboards - HTTP $http_code"
    debug_response "$body" "DASHBOARDS"
    
    if [ "$http_code" != "200" ]; then
        echo "❌ Error HTTP $http_code obteniendo dashboards"
        echo "Respuesta: $body"
        return 1
    fi
    
    # Verificar JSON válido
    if ! echo "$body" | jq . >/dev/null 2>&1; then
        echo "❌ Error: Respuesta de dashboards no es JSON válido"
        echo "Respuesta: $body"
        return 1
    fi
    
    echo "$body"
}

# Función para habilitar embedding en un dashboard específico
enable_dashboard_embedding() {
    local token=$1
    local dashboard_id=$2
    local dashboard_uuid=$3
    local dashboard_title=$4
    
    echo "🔧 Habilitando embedding para: ${dashboard_title} (ID: ${dashboard_id})"
    
    # Verificar estado actual
    local check_response=$(curl -s -w "\n%{http_code}" -X GET \
        "${SUPERSET_URL}/api/v1/dashboard/${dashboard_id}/embedded" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" 2>&1)
    
    local check_http_code=$(extract_http_code "$check_response")
    local check_body=$(extract_body "$check_response")
    
    echo "🔍 Verificando estado actual - HTTP $check_http_code"
    
    if [ "$check_http_code" = "200" ]; then
        echo "ℹ️  Dashboard ya tiene configuración de embedding"
        if echo "$check_body" | jq -e '.allowed_domains' >/dev/null 2>&1; then
            echo "✅ Embedding ya configurado para: ${dashboard_title}"
            return 0
        fi
    fi
    
    # Habilitar embedding
    local embed_response=$(curl -s -w "\n%{http_code}" -X PUT \
        "${SUPERSET_URL}/api/v1/dashboard/${dashboard_id}/embedded" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" \
        -d "{\"allowed_domains\": ${ALLOWED_DOMAINS}}" 2>&1)
    
    local embed_http_code=$(extract_http_code "$embed_response")
    local embed_body=$(extract_body "$embed_response")
    
    echo "📡 Respuesta de embedding - HTTP $embed_http_code"
    debug_response "$embed_body" "EMBEDDING"
    
    if [ "$embed_http_code" = "200" ] || [ "$embed_http_code" = "201" ]; then
        echo "✅ Embedding habilitado para: ${dashboard_title}"
        echo "   UUID: ${dashboard_uuid}"
        echo "   Dominios permitidos: ${ALLOWED_DOMAINS}"
        return 0
    else
        echo "❌ Error HTTP $embed_http_code habilitando embedding para: ${dashboard_title}"
        echo "   Respuesta: $embed_body"
        return 1
    fi
}

# Función principal
main() {
    echo "============================================"
    echo "🔧 CONFIGURACIÓN AUTOMÁTICA DE EMBEDDING"
    echo "============================================"
    
    # Verificar conectividad básica
    if ! test_basic_connectivity; then
        echo "❌ Error: No se puede conectar a Superset"
        echo "💡 Verifica que Superset esté corriendo en $SUPERSET_URL"
        exit 1
    fi
    
    # Obtener token de autenticación
    TOKEN=$(get_auth_token)
    if [ $? -ne 0 ]; then
        echo "❌ Error: No se pudo autenticar"
        echo ""
        echo "💡 Posibles soluciones:"
        echo "   1. Verifica que las credenciales admin/admin sean correctas"
        echo "   2. Verifica que superset_config_docker.py esté configurado:"
        echo "      - FEATURE_FLAGS = {'EMBEDDED_SUPERSET': True}"
        echo "      - WTF_CSRF_ENABLED = False"
        echo "      - ENABLE_CORS = True"
        echo "   3. Reinicia completamente Docker:"
        echo "      docker-compose -f docker-compose-non-dev.yml down"
        echo "      docker-compose -f docker-compose-non-dev.yml up -d"
        echo "   4. Verifica los logs de Superset:"
        echo "      docker-compose -f docker-compose-non-dev.yml logs superset"
        echo ""
        exit 1
    fi
    
    # Obtener dashboards
    echo "📊 Obteniendo dashboards..."
    DASHBOARDS_JSON=$(get_dashboards "$TOKEN")
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: No se pudieron obtener dashboards"
        echo "💡 Verifica permisos del usuario admin"
        exit 1
    fi
    
    # Contar dashboards
    local dashboard_count=$(echo "$DASHBOARDS_JSON" | jq '.result | length' 2>/dev/null || echo "0")
    echo "📈 Encontrados $dashboard_count dashboards"
    
    if [ "$dashboard_count" = "0" ]; then
        echo "⚠️  No se encontraron dashboards. Crea algunos dashboards primero."
        exit 0
    fi
    
    # Procesar dashboards
    local processed=0
    local enabled=0
    
    echo "$DASHBOARDS_JSON" | jq -r '.result[] | select(.published == true) | "\(.id)|\(.uuid)|\(.dashboard_title)"' 2>/dev/null | \
    while IFS='|' read -r dashboard_id dashboard_uuid dashboard_title; do
        if [ -n "$dashboard_id" ] && [ "$dashboard_id" != "null" ]; then
            processed=$((processed + 1))
            echo "📋 Procesando dashboard $processed: $dashboard_title"
            
            if enable_dashboard_embedding "$TOKEN" "$dashboard_id" "$dashboard_uuid" "$dashboard_title"; then
                enabled=$((enabled + 1))
            fi
            echo "---"
        fi
    done
    
    echo "============================================"
    echo "✅ CONFIGURACIÓN COMPLETADA"
    echo "============================================"
    echo "🔗 Dashboards disponibles en:"
    echo "   ${SUPERSET_URL}/dashboard/list/"
    echo ""
    echo "🚀 Para usar en tu aplicación React:"
    echo "   - Los dashboards están habilitados para embedding"
    echo "   - Dominios permitidos: ${ALLOWED_DOMAINS}"
    echo "   - Usa los UUIDs para embedding"
    echo "============================================"
}

# Verificar dependencias
if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq no está instalado"
    echo "💡 Instala jq: brew install jq  (macOS) o apt-get install jq (Ubuntu)"
    exit 1
fi

# Ejecutar función principal
main
