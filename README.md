# 🎯 Apache Superset Embedding - Integración con Aplicaciones Externas

[![Estado del Proyecto](https://img.shields.io/badge/Estado-Completado-brightgreen)](https://github.com)
[![Apache Superset](https://img.shields.io/badge/Apache%20Superset-Compatible-blue)](https://superset.apache.org/)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-yellow)](LICENSE)

## 📄 **Descripción**

Proyecto completo para integrar **Apache Superset** en aplicaciones externas (especialmente **Odoo**) usando iframes con autenticación transparente mediante guest tokens. La solución permite embeber dashboards de Superset directamente en otras aplicaciones web sin requerir login adicional.

## ✅ **Estado Actual**

- **✅ 100% Funcional** - Listo para implementación en producción
- **✅ Configuración CORS** completa con autenticación guest token
- **✅ Aplicación de ejemplo** funcionando perfectamente
- **✅ Documentación completa** y guías paso a paso

## 🚀 **Demo Rápida**

1. **Configurar Superset** con los archivos de configuración incluidos
2. **Ejecutar script de embedding**: `./setup_embedding.sh`
3. **Abrir ejemplo**: `python3 -m http.server 8080` → http://localhost:8080/iframe-example.html

## 📁 **Estructura del Proyecto**

```
embedded_superset/
├── README.md                                    # 📖 Este archivo - Guía principal
├── iframe-example.html                          # 🚀 Aplicación de ejemplo funcionando
├── setup_embedding.sh                           # 🔧 Script de configuración automática
├── README_INTEGRATION.md                        # 📋 Documentación técnica completa
├── CONFIGURATION_CHANGES.md                     # ⚙️ Detalles de cambios de configuración
├── .gitignore                                   # 🚫 Excluye carpeta superset/ del repo
└── config_files/                                # 📁 Archivos de configuración preparados
    ├── superset_config_docker.py                # ⚡ Configuración core de Superset
    └── docker-compose-non-dev.yml               # 🐳 Configuración Docker corregida

# Después de seguir las instrucciones de instalación:
└── superset/                                    # 📁 Repositorio oficial de Superset (no en GitHub)
    ├── docker-compose-non-dev.yml               # ← Copiado desde config_files/
    └── docker/pythonpath_dev/
        └── superset_config_docker.py            # ← Copiado desde config_files/
```

### **⚠️ Nota Importante**
- La carpeta `superset/` NO se incluye en este repositorio (está en `.gitignore`)
- Los usuarios deben clonar Superset oficialmente y aplicar nuestras configuraciones
- Esto garantiza que siempre usen la **última versión** de Apache Superset

## 📚 **Documentación**

| Documento | Descripción |
|-----------|-------------|
| **[README_INTEGRATION.md](README_INTEGRATION.md)** | 📋 **Guía técnica completa** - Configuración paso a paso, flujo de autenticación, y roadmap para Odoo |
| **[CONFIGURATION_CHANGES.md](CONFIGURATION_CHANGES.md)** | ⚙️ **Documentación técnica detallada** - Todos los cambios realizados en archivos de configuración |
| **[iframe-example.html](iframe-example.html)** | 🚀 **Aplicación de ejemplo** - Implementación completa HTML/JavaScript funcionando |

---

## 🔑 **Características Principales**

### **✅ Configuración CORS Funcional**
- URLs deben terminar obligatoriamente en barra final `/`
- Configuración completa para múltiples dominios y puertos
- Compatible con desarrollo local y producción

### **✅ Autenticación Guest Token**
- Sistema de guest tokens automático para acceso sin login
- Integración con SDK oficial de Superset
- Flujo de autenticación transparente para usuarios finales

### **✅ Configuración de Seguridad**
- CSRF y Talisman configurados para development y production
- Row Level Security (RLS) preparado para permisos granulares
- Configuración de iframe embedding habilitada

### **✅ SDK Oficial Integrado**
- Uso del SDK oficial `@superset-ui/embedded-sdk`
- Configuración automática de tamaño de iframe
- Manejo robusto de errores y estados de carga

## 🛠️ **Instalación y Configuración**

### **1. Prerequisitos**
- Docker y Docker Compose
- `jq` para procesamiento JSON
- `curl` para llamadas API
- `git` para clonar repositorios

### **2. Instalación Completa (Paso a Paso)**

#### **Paso 1: Clonar este repositorio**
```bash
git clone https://github.com/tu-usuario/embedded_superset.git
cd embedded_superset
```

#### **Paso 2: Descargar e instalar Apache Superset**
```bash
# Clonar repositorio oficial de Superset (siempre última versión)
git clone https://github.com/apache/superset.git
cd superset

# Configurar variables de entorno (opcional)
cp .env.example .env
# Editar .env si necesitas personalizar puertos o configuraciones
```

#### **Paso 3: Aplicar configuraciones para embedding**
```bash
# Volver al directorio del proyecto
cd ..

# Copiar archivos de configuración preparados
cp config_files/superset_config_docker.py superset/docker/pythonpath_dev/
cp config_files/docker-compose-non-dev.yml superset/

# Verificar que los archivos se copiaron correctamente
ls -la superset/docker/pythonpath_dev/superset_config_docker.py
ls -la superset/docker-compose-non-dev.yml
```

#### **Paso 4: Iniciar Superset**
```bash
cd superset

# Construir e iniciar Superset (primera vez)
docker-compose -f docker-compose-non-dev.yml up -d

# Esperar a que Superset esté listo (puede tomar varios minutos)
echo "Esperando a que Superset esté listo..."
timeout 300 bash -c 'until curl -f http://localhost:8088/health; do sleep 5; done'
echo "✅ Superset está funcionando!"
```

#### **Paso 5: Configurar embedding en dashboards**
```bash
# Volver al directorio del proyecto
cd ..

# Ejecutar script de configuración automática
./setup_embedding.sh
```

#### **Paso 6: Probar la aplicación de ejemplo**
```bash
# Iniciar servidor web simple
python3 -m http.server 8080

# Abrir en navegador: http://localhost:8080/iframe-example.html
echo "🚀 Aplicación de ejemplo disponible en: http://localhost:8080/iframe-example.html"
```

### **3. Configuración Rápida (Si ya tienes Superset)**
Si ya tienes Apache Superset instalado:

```bash
# 1. Clonar este repositorio
git clone https://github.com/tu-usuario/embedded_superset.git
cd embedded_superset

# 2. Copiar configuraciones a tu instalación existente
cp config_files/superset_config_docker.py [ruta-a-tu-superset]/docker/pythonpath_dev/
cp config_files/docker-compose-non-dev.yml [ruta-a-tu-superset]/

# 3. Reiniciar Superset
cd [ruta-a-tu-superset]
docker-compose -f docker-compose-non-dev.yml restart superset

# 4. Configurar embedding
cd [ruta-a-este-proyecto]
./setup_embedding.sh

# 5. Probar ejemplo
python3 -m http.server 8080
```

## 🔧 **Configuración Técnica**

### **Archivos Modificados:**
1. **`superset_config_docker.py`** - Configuración principal
   - Feature flags para embedding
   - Configuración CORS con URLs correctas
   - Guest token configuration
   - Configuración de seguridad

2. **`docker-compose-non-dev.yml`** - Montaje de volúmenes corregido
   - Rutas de archivos de configuración corregidas
   - Montaje adecuado de pythonpath_dev

### **Configuración Crítica:**
```python
# En superset_config_docker.py
FEATURE_FLAGS = {"EMBEDDED_SUPERSET": True}  # ⚠️ CRÍTICO
ENABLE_CORS = True
CORS_OPTIONS = {
    "origins": ["http://localhost:3000/"],  # ⚠️ Barra final obligatoria
}
WTF_CSRF_ENABLED = False  # Para development
GUEST_TOKEN_JWT_SECRET = "clave-minimo-32-caracteres"
```

---

## 🎨 **Aplicación de Ejemplo**

### **HTML/iframe Example**
```bash
python3 -m http.server 8080
# Abrir: http://localhost:8080/iframe-example.html
```

**Características:**
- ✅ **Interfaz estilo Odoo** - Simulación realista de integración
- ✅ **SDK oficial integrado** - Uso de `@superset-ui/embedded-sdk`
- ✅ **Autenticación automática** - Guest tokens transparentes
- ✅ **Manejo de errores** - Estados de carga y error robusto
- ✅ **Responsive design** - Compatible con diferentes tamaños de pantalla
- ✅ **Lista de dashboards** - Carga automática de dashboards disponibles

## 🎯 **Uso en Producción**

### **Para Odoo**
El ejemplo HTML incluido (`iframe-example.html`) simula exactamente cómo se vería la integración en Odoo:

1. **Controlador Python** para generar guest tokens
2. **Vista XML** con el SDK de Superset embebido
3. **Verificación de permisos** basada en usuarios/grupos de Odoo
4. **URLs de embedding** configuradas en modelo de datos

### **Para Otras Aplicaciones**
La configuración es compatible con cualquier aplicación web que pueda:
- Hacer llamadas HTTP a APIs REST
- Renderizar JavaScript y crear iframes
- Manejar autenticación de usuarios

---

## 🔐 **Configuración de Producción**

### **Seguridad Reforzada**
Para uso en producción, modifica `superset_config_docker.py`:

```python
# ⚠️ CRÍTICO: Activar CSRF con excepciones específicas
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = [
    'superset.views.core.dashboard_embedded',
    'superset.security.api.guest_token'
]

# ⚠️ CRÍTICO: CORS restrictivo solo para dominios de producción
CORS_OPTIONS = {
    "origins": [
        "https://tu-odoo-produccion.com/",
        "https://tu-dominio-corporativo.com/",
    ],
}

# ⚠️ CRÍTICO: Secret JWT ultra seguro (64+ caracteres)
GUEST_TOKEN_JWT_SECRET = "clave-super-ultra-segura-produccion-64-caracteres-minimo"
```

## 🤝 **Contribuir**

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📞 **Soporte**

- **Documentación técnica**: Ver [README_INTEGRATION.md](README_INTEGRATION.md)
- **Configuración detallada**: Ver [CONFIGURATION_CHANGES.md](CONFIGURATION_CHANGES.md)
- **Aplicación de ejemplo**: Ver [iframe-example.html](iframe-example.html)

## 📄 **Licencia**

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 🏆 **Estado Final**

**✅ PROYECTO COMPLETADO EXITOSAMENTE**

- **🔧 Técnicamente sólido** - Configuración correcta y probada
- **📚 Bien documentado** - Guías completas y detalladas  
- **🚀 Escalable** - Listo para implementación en Odoo
- **🛡️ Seguro** - Configuraciones para development y production
- **🔄 Reproducible** - Scripts automáticos y pasos claros

**🎯 Listo para:** Implementación inmediata en Odoo usando los patrones, configuraciones y código probados.

