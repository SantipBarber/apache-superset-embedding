#!/bin/bash

# Script principal para configurar embedding en Apache Superset
# Versión genérica - FUNCIONAL
# Fecha: 18 de Agosto, 2025

# ⚠️ CONFIGURAR ESTAS VARIABLES SEGÚN TU ENTORNO
SUPERSET_URL="http://localhost:8088"  # Cambiar por la IP/URL de tu Superset
USERNAME="admin"                      # Usuario administrador de Superset
PASSWORD="admin"                      # Contraseña del administrador

# URLs que deben estar habilitadas para embedding
# ⚠️ AGREGAR LAS URLs DE TU APLICACIÓN
ALLOWED_DOMAINS='[
    "http://localhost:8080",
    "http://localhost:8080/",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8080/"
]'

# Nota: Agregar aquí las URLs específicas de tu entorno

echo "🚀 Configuración de Embedding para Superset"
echo "============================================"

# Función para obtener token
get_token() {
    local response=$(curl -s -X POST "${SUPERSET_URL}/api/v1/security/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\", \"provider\": \"db\"}")
    
    echo "$response" | jq -r '.access_token'
}

# Función para listar dashboards
list_dashboards() {
    local token=$1
    echo "📊 DASHBOARDS DISPONIBLES:"
    echo "=========================="
    
    local response=$(curl -s -H "Authorization: Bearer $token" \
        "${SUPERSET_URL}/api/v1/dashboard/")
    
    echo "$response" | jq -r '.result[] | select(.published == true) | 
        "ID: \(.id) | UUID: \(.uuid) | Título: \(.dashboard_title)"' | 
        head -10
    
    echo ""
}

# Función para habilitar embedding en un dashboard específico
enable_embedding() {
    local token=$1
    local dashboard_id=$2
    
    echo "🔧 Habilitando embedding para dashboard ID: $dashboard_id"
    
    local response=$(curl -s -X PUT \
        "${SUPERSET_URL}/api/v1/dashboard/${dashboard_id}/embedded" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "{\"allowed_domains\": $ALLOWED_DOMAINS}")
    
    local embed_uuid=$(echo "$response" | jq -r '.result.uuid // empty')
    
    if [ -n "$embed_uuid" ] && [ "$embed_uuid" != "null" ]; then
        echo "✅ Embedding habilitado exitosamente"
        echo "   🆔 UUID para SDK: $embed_uuid"
        echo "   🌐 Dominios permitidos: http://localhost:8080"
        echo ""
        return 0
    else
        echo "❌ Error habilitando embedding:"
        echo "$response" | jq '.message // .'
        echo ""
        return 1
    fi
}

# Función para obtener dashboards con embedding ya habilitado
get_embedded_dashboards() {
    local token=$1
    echo "📋 DASHBOARDS CON EMBEDDING HABILITADO:"
    echo "======================================"
    
    local response=$(curl -s -H "Authorization: Bearer $token" \
        "${SUPERSET_URL}/api/v1/dashboard/")
    
    local count=0
    local js_config="let dashboards = ["
    
    echo "$response" | jq -r '.result[] | select(.published == true) | "\(.id)|\(.uuid)|\(.dashboard_title)"' | \
    while IFS='|' read -r dashboard_id dashboard_uuid dashboard_title; do
        if [ -n "$dashboard_id" ] && [ "$dashboard_id" != "null" ]; then
            # Verificar si tiene embedding habilitado
            local embed_check=$(curl -s -H "Authorization: Bearer $token" \
                "${SUPERSET_URL}/api/v1/dashboard/${dashboard_id}/embedded" 2>/dev/null)
            
            if echo "$embed_check" | jq -e '.result.uuid' >/dev/null 2>&1; then
                local embed_uuid=$(echo "$embed_check" | jq -r '.result.uuid')
                echo "✅ $dashboard_title"
                echo "   Dashboard UUID: $dashboard_uuid"
                echo "   Embedding UUID: $embed_uuid"
                echo "   ---"
                
                # Guardar para generar configuración JavaScript
                if [ $count -gt 0 ]; then
                    js_config+=","
                fi
                js_config+="
    {
        id: \"$embed_uuid\",
        dashboard_title: \"$(echo "$dashboard_title" | sed 's/"/\\"/g')\",
        uuid: \"$embed_uuid\",
        dashboard_uuid: \"$dashboard_uuid\"
    }"
                count=$((count + 1))
            fi
        fi
    done
    
    if [ $count -eq 0 ]; then
        echo "⚠️  No hay dashboards con embedding habilitado"
        echo ""
        echo "💡 Para habilitar embedding:"
        echo "   1. Ve a Superset: $SUPERSET_URL"
        echo "   2. Abre un dashboard"
        echo "   3. Haz clic en Settings → Embed dashboard"
        echo "   4. Agrega estos dominios:"
        echo "      - http://localhost:8080"
        echo "      - http://127.0.0.1:8080"
        echo ""
    else
        js_config+="
];"
        echo ""
        echo "🎯 CONFIGURACIÓN JAVASCRIPT PARA TU APLICACIÓN:"
        echo "=============================================="
        echo "$js_config"
    fi
    
    echo ""
}

# Función principal
main() {
    echo "🔑 Obteniendo token de acceso..."
    TOKEN=$(get_token)
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo "❌ Error: No se pudo obtener token de acceso"
        echo "💡 Verifica:"
        echo "   - Que Superset esté corriendo en $SUPERSET_URL"
        echo "   - Que las credenciales admin/admin sean correctas"
        exit 1
    fi
    
    echo "✅ Token obtenido exitosamente"
    echo ""
    
    # Listar dashboards disponibles
    list_dashboards "$TOKEN"
    
    # Mostrar dashboards con embedding ya habilitado
    get_embedded_dashboards "$TOKEN"
    
    # Ofrecer habilitar embedding para un dashboard específico
    echo "🔧 HABILITAR EMBEDDING PARA UN DASHBOARD:"
    echo "========================================"
    echo "Para habilitar embedding en un dashboard específico, ejecuta:"
    echo "./setup_embedding_working.sh enable <dashboard_id>"
    echo ""
    echo "Ejemplo: ./setup_embedding_working.sh enable 1"
    echo ""
}

# Función para habilitar embedding en un dashboard específico (modo enable)
enable_mode() {
    local dashboard_id=$1
    
    if [ -z "$dashboard_id" ]; then
        echo "❌ Error: Debes especificar un dashboard ID"
        echo "Uso: ./setup_embedding_working.sh enable <dashboard_id>"
        exit 1
    fi
    
    echo "🔑 Obteniendo token de acceso..."
    TOKEN=$(get_token)
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo "❌ Error: No se pudo obtener token de acceso"
        exit 1
    fi
    
    enable_embedding "$TOKEN" "$dashboard_id"
}

# Verificar parámetros
if [ "$1" = "enable" ]; then
    enable_mode "$2"
else
    main
fi