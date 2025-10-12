#!/bin/bash
# Script de limpieza inteligente del repositorio GRUPO_GAD
# Fecha: 12 Octubre 2025
# Propósito: Eliminar archivos duplicados, versiones anteriores y redundantes

echo "🧹 LIMPIEZA DE REPOSITORIO GRUPO_GAD"
echo "======================================"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Contador
DELETED=0
KEPT=0

echo "📋 Análisis de archivos a eliminar..."
echo ""

# Función para eliminar archivo
delete_file() {
    local file="$1"
    local reason="$2"
    
    if [ -f "$file" ]; then
        echo -e "${YELLOW}🗑️  Eliminando:${NC} $file"
        echo "   Razón: $reason"
        rm "$file"
        ((DELETED++))
    fi
}

# Función para mantener archivo
keep_file() {
    local file="$1"
    echo -e "${GREEN}✓ Manteniendo:${NC} $file"
    ((KEPT++))
}

echo "1️⃣ Documentación de Sprint (Consolidación)"
echo "-------------------------------------------"

# Eliminar versiones anteriores del cierre de jornada
delete_file "CIERRE_JORNADA_20251011.md" "Versión anterior (existe CIERRE_JORNADA_20251011_FINAL.md)"
keep_file "CIERRE_JORNADA_20251011_FINAL.md"

# Eliminar resumen redundante
delete_file "RESUMEN_JORNADA_20251011.md" "Redundante (contenido consolidado en CIERRE_JORNADA_20251011_FINAL.md)"

# Eliminar sprint optimización (consolidado en SPRINT_RESUMEN_EJECUTIVO_FINAL.md)
delete_file "SPRINT_OPTIMIZACION_20251011.md" "Redundante (consolidado en SPRINT_RESUMEN_EJECUTIVO_FINAL.md)"

# Eliminar TODO (contenido movido a PLAN_POST_DESARROLLO_COMPLETO.md)
delete_file "TODO_PROXIMA_SESION.md" "Obsoleto (contenido en PLAN_POST_DESARROLLO_COMPLETO.md)"

echo ""
echo "2️⃣ Reportes de Cleanup Antiguos"
echo "--------------------------------"

# Eliminar reportes de cleanup antiguos (del 10 de octubre)
delete_file "CLEANUP_ANALYSIS_REPORT.md" "Reporte de limpieza anterior (10 Oct, ya aplicado)"
delete_file "EXECUTIVE_CLEANUP_SUMMARY.md" "Reporte de limpieza anterior (10 Oct, ya aplicado)"

echo ""
echo "3️⃣ Documentación Consolidada"
echo "------------------------------"

# Mantener documentos principales
keep_file "BASELINE_PERFORMANCE.md"
keep_file "FASE2_TESTS_RESULTS.md"
keep_file "FASE3_QUERY_OPTIMIZATION_RESULTS.md"
keep_file "FASE4_CACHE_REDIS_RESULTS.md"
keep_file "SPRINT_COMPLETION_REPORT.md"
keep_file "SPRINT_RESUMEN_EJECUTIVO_FINAL.md"
keep_file "PLAN_POST_DESARROLLO_COMPLETO.md"

echo ""
echo "4️⃣ Archivos Lock Redundantes"
echo "------------------------------"

# Eliminar requirements.lock (usamos requirements.txt)
if [ -f "requirements.lock" ]; then
    delete_file "requirements.lock" "Obsoleto (Dockerfile.api usa requirements.txt)"
fi

# Eliminar poetry.lock si existe (no usamos Poetry)
if [ -f "poetry.lock" ]; then
    delete_file "poetry.lock" "No usamos Poetry (usamos pip + requirements.txt)"
fi

echo ""
echo "5️⃣ Scripts de Limpieza Antiguos"
echo "--------------------------------"

# Eliminar script de cleanup anterior
if [ -f "cleanup_repo.sh" ]; then
    delete_file "cleanup_repo.sh" "Script de limpieza anterior (ya ejecutado)"
fi

echo ""
echo "======================================"
echo "📊 RESUMEN DE LIMPIEZA"
echo "======================================"
echo -e "${RED}🗑️  Archivos eliminados: $DELETED${NC}"
echo -e "${GREEN}✓ Archivos conservados: $KEPT${NC}"
echo ""

if [ $DELETED -gt 0 ]; then
    echo "✅ Limpieza completada exitosamente"
    echo ""
    echo "📝 Archivos eliminados:"
    echo "  - Versiones anteriores de documentación de sprint"
    echo "  - Reportes de cleanup antiguos"
    echo "  - Archivos lock redundantes"
    echo "  - Scripts de limpieza ya aplicados"
else
    echo "ℹ️  No se encontraron archivos para eliminar"
fi

echo ""
echo "🎯 Próximo paso: git add -A && git commit"
