#!/bin/bash

echo "🎯 VERIFICACIÓN FINAL DE LA INTEGRACIÓN"
echo "======================================"

# Verificar Superset
echo "1. ✅ Verificando Superset..."
if curl -s http://192.168.1.137:8088/health | grep -q "OK"; then
    echo "   ✅ Superset funcionando en http://192.168.1.137:8088"
else
    echo "   ❌ Superset no responde"
fi

# Verificar CORS
echo "2. ✅ Verificando CORS..."
CORS_HEADER=$(curl -s -H "Origin: http://localhost:8080" -I http://192.168.1.137:8088/health | grep -i "access-control-allow-origin")
if [ -n "$CORS_HEADER" ]; then
    echo "   ✅ CORS configurado: $CORS_HEADER"
else
    echo "   ❌ CORS no configurado"
fi

# Verificar servidor web
echo "3. ✅ Verificando servidor web..."
if curl -s -I http://localhost:8080/iframe-example.html | grep -q "200 OK"; then
    echo "   ✅ Servidor web funcionando en http://localhost:8080"
else
    echo "   ❌ Servidor web no responde"
fi

# Verificar login
echo "4. ✅ Verificando login..."
TOKEN=$(curl -s -X POST http://192.168.1.137:8088/api/v1/security/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin", "provider": "db"}' | \
    jq -r '.access_token // empty')

if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo "   ✅ Login funcionando"
else
    echo "   ❌ Error en login"
    exit 1
fi

# Verificar guest token
echo "5. ✅ Verificando guest token..."
GUEST_TOKEN=$(curl -s -X POST "http://192.168.1.137:8088/api/v1/security/guest_token/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"user": {"username": "guest_user", "first_name": "Guest", "last_name": "User"}, "resources": [{"type": "dashboard", "id": "c664bf36-c689-4b54-8969-dc478bbb57a9"}], "rls": []}' | \
    jq -r '.token // empty')

if [ -n "$GUEST_TOKEN" ] && [ "$GUEST_TOKEN" != "null" ]; then
    echo "   ✅ Guest token generado exitosamente"
    echo "   Token: ${GUEST_TOKEN:0:50}..."
else
    echo "   ❌ Error generando guest token"
fi

echo ""
echo "🚀 CONFIGURACIÓN COMPLETADA:"
echo "=========================="
echo "✅ Embedding habilitado manualmente en Superset"
echo "✅ UUIDs configurables en la aplicación:"
echo "   - Obtener desde interfaz de Superset"
echo "   - Dashboard > Settings > Embed dashboard"
echo "   - Copiar UUID y actualizar archivos"
echo ""
echo "🎯 PRUEBA LA APLICACIÓN:"
echo "======================"
echo "1. Abre $APP_URL/iframe-example.html"
echo "2. Selecciona cualquier dashboard del dropdown"
echo "3. Haz clic en 'Cargar Dashboard'"
echo ""
echo "📊 Si ves errores, compártelos para análisis final"