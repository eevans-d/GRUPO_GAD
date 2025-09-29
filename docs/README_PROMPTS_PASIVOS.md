# Prompts Pasivos Avanzados - GRUPO_GAD

## 📝 Descripción

Este directorio contiene **4 prompts pasivos avanzados** diseñados para **Copilot Pro en modo agente autónomo**. Estos prompts implementan un enfoque **sistémico, forense y no invasivo** para analizar, validar y gobernar el proyecto GRUPO_GAD.

## 🎯 Características Clave

- ✅ **No invasivos**: Solo observan, correlacionan, validan y guían — nunca modifican código
- ✅ **Rigor forense**: Cada afirmación incluye evidencia `archivo:línea`
- ✅ **Estado real vs documentado**: Distinguen implementación de intención
- ✅ **Criterios objetivos**: Comandos copy-paste para verificar cada claim
- ✅ **Enfoque sistémico**: Modelan interdependencias y puntos de falla

## 📁 Estructura de Archivos

```
docs/
├── system/
│   └── BLUEPRINT_SISTEMICO.md          # Modelo dependencial forense
├── deploy/
│   └── CHECKLIST_VERIFICACION.md       # Verificación pre-despliegue condicional
├── roadmap/
│   └── HOJA_RUTA_PRODUCCION.md         # Secuencia estratégica hacia producción
├── governance/
│   └── GOBERNANZA_CICLO_VIDA.md        # Gobernanza post-despliegue
└── README_PROMPTS_PASIVOS.md           # Este archivo
```

## 🚀 Uso con Copilot Pro

### Prompt A: Blueprint Sistémico
**Propósito**: Modela el proyecto como red de componentes interdependientes  
**Input**: Acceso total al repositorio  
**Output**: `docs/system/BLUEPRINT_SISTEMICO.md`

```
Instrucción para Copilot Pro:
"Analiza GRUPO_GAD usando el Prompt Pasivo A del archivo prompts_pasivos_avanzados_GRUPO_GAD.md. 
Genera el blueprint sistémico completo con evidencia forense archivo:línea para cada componente."
```

### Prompt B: Checklist Verificación
**Propósito**: Verificación objetiva pre-despliegue  
**Input**: Sistema en ejecución local  
**Output**: `docs/deploy/CHECKLIST_VERIFICACION.md`

```
Instrucción para Copilot Pro:
"Ejecuta el Prompt Pasivo B. Verifica cada nivel del checklist con comandos reales. 
Solo marca ✅ si tienes evidencia objetiva. Bloquea despliegue si hay FAIL items."
```

### Prompt C: Hoja de Ruta Estratégica  
**Propósito**: Secuencia lógica de cierre de brechas  
**Input**: Gaps identificados en Blueprint y Checklist  
**Output**: `docs/roadmap/HOJA_RUTA_PRODUCCION.md`

```
Instrucción para Copilot Pro:
"Usa el Prompt Pasivo C para crear hoja de ruta estratégica. 
Solo incluye tareas que cierren brechas reales identificadas. 
Cada tarea debe tener criterio de aceptación objetivo."
```

### Prompt D: Guía de Gobernanza
**Propósito**: Definir evolución y mantenimiento post-despliegue  
**Input**: Contratos del sistema actual  
**Output**: `docs/governance/GOBERNANZA_CICLO_VIDA.md`

```
Instrucción para Copilot Pro:
"Aplica el Prompt Pasivo D para definir gobernanza de ciclo de vida. 
Identifica contratos críticos existentes y define proceso de evolución sin romperlos."
```

## 🔧 Validación Automática

### Script de Validación
El archivo `scripts/validate_pre_deploy.sh` implementa automáticamente el Checklist de Verificación:

```bash
# Ejecutar validación completa
bash scripts/validate_pre_deploy.sh

# Exit code 0 = APTO PARA DESPLIEGUE
# Exit code 1 = BLOQUEAR DESPLIEGUE
```

### Integración en CI/CD
```yaml
# .github/workflows/pre-deploy-validation.yml
name: Pre-Deploy Validation
on:
  pull_request:
    branches: [main]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run pre-deploy validation
        run: bash scripts/validate_pre_deploy.sh
```

## 📊 Métricas de Éxito

### Durante Análisis (Prompts A-B)
- **Trazabilidad**: 100% afirmaciones con evidencia `archivo:línea`
- **Precisión**: 0 falsos positivos en estado de implementación
- **Cobertura**: Todos los componentes críticos identificados

### Durante Planificación (Prompt C)
- **Relevancia**: Solo tareas que cierren gaps reales
- **Verificabilidad**: Cada tarea con criterio objetivo
- **Estimación**: Horas estimadas vs reales < 20% diferencia

### Durante Gobernanza (Prompt D)
- **Contratos preservados**: 100% compatibilidad backward
- **Tiempo de respuesta**: Procesos de evolución claros y documentados
- **Sunset planning**: Plan de descontinuación completo si es necesario

## 🔄 Flujo de Trabajo Recomendado

### 1. Análisis Inicial
```bash
# Ejecutar Prompt A - Blueprint Sistémico
# Input: Repository completo
# Output: docs/system/BLUEPRINT_SISTEMICO.md
```

### 2. Validación Estado Actual
```bash
# Ejecutar Prompt B - Checklist Verificación  
bash scripts/validate_pre_deploy.sh
# Output: docs/deploy/CHECKLIST_VERIFICACION.md + validation results
```

### 3. Planificación Estratégica
```bash
# Ejecutar Prompt C - Hoja de Ruta
# Input: Gaps identificados en pasos 1-2
# Output: docs/roadmap/HOJA_RUTA_PRODUCCION.md
```

### 4. Definición de Gobernanza
```bash
# Ejecutar Prompt D - Ciclo de Vida
# Input: Contratos actuales del sistema
# Output: docs/governance/GOBERNANZA_CICLO_VIDA.md
```

### 5. Implementación y Monitoreo
```bash
# Seguir roadmap del paso 3
# Aplicar gobernanza del paso 4
# Re-validar con paso 2 antes de cada despliegue
```

## 🎯 Casos de Uso Específicos

### Para DevOps/SRE
- Usar **Prompt B** antes de cada despliegue para validación automática
- Usar **Prompt D** para definir SLOs y alertas
- Usar script `validate_pre_deploy.sh` en pipelines CI/CD

### Para Arquitectos de Software  
- Usar **Prompt A** para análisis de dependencias y puntos de falla
- Usar **Prompt C** para priorizar deuda técnica
- Usar **Prompt D** para evolución de contratos sin romper backward compatibility

### Para Product Managers
- Usar **Prompt C** para estimaciones y roadmap de producción
- Usar **Prompt D** para planificar sunset de features/versiones
- Usar métricas de **Prompt A** para entender riesgos técnicos

### Para Equipos de Desarrollo
- Usar **Prompt A** antes de cambios arquitectónicos grandes
- Usar **Prompt B** como gate de calidad antes de merge
- Usar **Prompt C** para planning de sprints técnicos

## ⚠️ Limitaciones y Consideraciones

### Lo que SÍ hacen estos prompts:
- ✅ Observan y analizan estado real del sistema
- ✅ Validan configuración y funcionalidad sin modificar
- ✅ Generan documentación de estado y procesos
- ✅ Proveen comandos verificables para cada claim

### Lo que NO hacen estos prompts:
- ❌ No modifican código fuente
- ❌ No implementan fixes automáticamente  
- ❌ No toman decisiones de negocio
- ❌ No reemplazan testing funcional/unitario

### Dependencias para Uso Óptimo:
- Docker y docker-compose funcionales
- Acceso a base de datos PostgreSQL  
- Curl disponible para verificar endpoints
- Git repository completo y actualizado

## 📞 Soporte y Contribución

### Actualización de Prompts
Los prompts evolucionan con el proyecto. Para actualizarlos:

1. Revisar cambios en arquitectura del sistema
2. Actualizar criterios de verificación en Prompt B
3. Ajustar contratos identificados en Prompt D
4. Re-generar documentación usando prompts actualizados

### Reporting Issues
Si encuentras inconsistencias entre prompts y realidad del sistema:

1. Verificar que el sistema esté actualizado (`git pull`)
2. Ejecutar `scripts/validate_pre_deploy.sh` para estado actual
3. Comparar outputs con documentación generada
4. Actualizar prompts según sea necesario

---

**Estos prompts pasivos avanzados elevan el análisis de GRUPO_GAD de nivel operativo a nivel estratégico-sistémico, sin tocar una línea de código.**