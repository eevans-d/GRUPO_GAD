# Sistema Multi-Agente IA - GRUPO_GAD

## Descripción General

Este directorio contiene la documentación completa del sistema de agentes IA diseñado para el proyecto GRUPO_GAD. El sistema implementa un enfoque multi-agente con roles especializados que trabajan de manera coordinada para realizar el ciclo completo de desarrollo de software.

## Estructura del Sistema

El sistema está organizado en **3 partes principales**:

### PARTE 1/3: Agentes Core y Arquitectura
**Archivo:** [`PROMPTS_AGENTES_IA_PARTE_1.md`](./PROMPTS_AGENTES_IA_PARTE_1.md)

Contiene los agentes fundamentales para la planificación y desarrollo:
- **Project Coordinator Agent**: Coordinación central, gestión de flujos y sincronización
- **Solution Architect Agent**: Diseño arquitectónico y estándares técnicos
- **Software Developer Agent**: Implementación de soluciones y testing

### PARTE 2/3: Agentes de Calidad y Seguridad
**Estado:** Por implementar

Incluirá:
- **QA Agent**: Testing comprehensivo y aseguramiento de calidad
- **Security Agent**: Análisis de seguridad y gestión de vulnerabilidades
- **Performance Agent**: Optimización y análisis de rendimiento

### PARTE 3/3: Agentes de Documentación y Operaciones
**Estado:** Por implementar

Incluirá:
- **Documentation Agent**: Generación y mantenimiento de documentación
- **DevOps Agent**: Deployment, CI/CD y operaciones

## Características del Sistema

### Arquitectura Multi-Agente
- **8 roles especializados** con responsabilidades claramente definidas
- **Workflows integrados** desde planificación hasta deployment
- **Protocolos de comunicación** estandarizados entre agentes
- **Estándares de calidad** integrados en cada fase

### Principios de Diseño
1. **Especialización**: Cada agente domina su área específica
2. **Colaboración**: Integración fluida entre agentes
3. **Trazabilidad**: Documentación completa de decisiones
4. **Calidad**: Validación continua en cada etapa
5. **Escalabilidad**: Fácil extensión con nuevos agentes

## Uso

### Para Coordinadores de Proyecto
Los prompts de agentes sirven como:
- Guía para estructurar el trabajo
- Plantillas para comunicación estandarizada
- Checklists para validación de entregas
- Marco para gestión de calidad

### Para Implementadores de Agentes IA
Los documentos definen:
- Comportamiento esperado de cada agente
- Protocolos de interacción
- Formatos de entrada/salida
- Criterios de validación

### Para Desarrolladores
Útil para:
- Comprender roles y responsabilidades
- Seguir estándares establecidos
- Integrar con el sistema de agentes
- Mantener consistencia en entregas

## Integración con GRUPO_GAD

Este sistema de agentes está diseñado específicamente para el proyecto GRUPO_GAD, considerando:

- **Arquitectura existente**: FastAPI, PostgreSQL/PostGIS, WebSockets, Telegram Bot
- **Stack tecnológico**: Python 3.11+, SQLAlchemy, Alembic, Pydantic
- **Convenciones del proyecto**: Logging estructurado, validación Pydantic v2, tests con pytest
- **Patrones establecidos**: Dependency injection, async/await, WebSocket heartbeat

Ver [copilot-instructions.md](../../.github/copilot-instructions.md) para detalles de la arquitectura del proyecto.

## Workflow Típico

```
1. Coordinator recibe requisito del usuario
   ↓
2. Coordinator crea plan y asigna a Architect
   ↓
3. Architect diseña solución y entrega especificaciones
   ↓
4. Coordinator valida diseño y asigna a Developer
   ↓
5. Developer implementa con tests
   ↓
6. QA valida implementación (PARTE 2)
   ↓
7. Security revisa seguridad (PARTE 2)
   ↓
8. Performance optimiza si necesario (PARTE 2)
   ↓
9. Documentation actualiza docs (PARTE 3)
   ↓
10. DevOps prepara deployment (PARTE 3)
    ↓
11. Coordinator consolida y cierra ciclo
```

## Extensibilidad

Para agregar nuevos agentes al sistema:

1. **Definir Rol**
   - Nombre y propósito claro
   - Responsabilidades específicas
   - Límites de actuación

2. **Protocolo de Operación**
   - Inputs esperados
   - Proceso de trabajo
   - Outputs a generar

3. **Criterios de Calidad**
   - Métricas de éxito
   - Estándares a seguir
   - Validaciones requeridas

4. **Integración**
   - Agentes con los que interactúa
   - Protocolos de comunicación
   - Dependencias

5. **Formato de Comunicación**
   - Templates de entrada/salida
   - Estructura de documentación
   - Metadatos requeridos

## Referencias

### Documentación Relacionada
- [Guía para Agentes de IA](../../.github/copilot-instructions.md)
- [Prompts Pasivos Avanzados](../README_PROMPTS_PASIVOS.md)
- [Blueprint Sistémico](../system/BLUEPRINT_SISTEMICO.md)
- [Checklist de Verificación](../deploy/CHECKLIST_VERIFICACION.md)

### Arquitectura del Proyecto
- [Análisis Arquitectónico](../../ARCHITECTURAL_ANALYSIS.md)
- [Especificación Técnica](../../ESPECIFICACION_TECNICA.md)
- [Project Overview](../PROJECT_OVERVIEW.md)

## Estado del Proyecto

| Parte | Estado | Agentes | Fecha |
|-------|--------|---------|-------|
| PARTE 1/3 | ✅ Completo | Coordinator, Architect, Developer | 2024 |
| PARTE 2/3 | 🔄 Pendiente | QA, Security, Performance | - |
| PARTE 3/3 | 🔄 Pendiente | Documentation, DevOps | - |

## Contribución

Para mejorar o extender estos prompts:

1. Revisa el agente existente más similar
2. Mantén la estructura y formato consistente
3. Define claramente roles e interfaces
4. Documenta integraciones con otros agentes
5. Incluye ejemplos de uso
6. Actualiza este README

## Notas Importantes

### Compatibilidad con Copilot Pro
Estos prompts están optimizados para uso con GitHub Copilot Pro y agentes IA similares que tienen:
- Acceso completo al repositorio
- Capacidad de análisis de código
- Generación de código y documentación
- Ejecución de validaciones

### No Invasivo
Los prompts son **descriptivos y guías**, no ejecutan cambios automáticamente:
- Proporcionan estructura y mejores prácticas
- Definen estándares y formatos
- Guían la toma de decisiones
- Facilitan la validación de calidad

Los cambios al código siempre requieren revisión y aprobación humana.

---

**Sistema Multi-Agente IA para GRUPO_GAD**  
*Elevando el desarrollo de software mediante coordinación inteligente y especialización*
