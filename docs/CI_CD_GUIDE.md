# Guía de CI/CD para GRUPO_GAD

Este documento describe los pipelines de Integración Continua (CI) y Entrega Continua (CD) implementados para el proyecto GRUPO_GAD.

## Arquitectura de Pipelines

### 1. Pipeline de CI (Integración Continua)

**Archivo**: `.github/workflows/ci-enhanced.yml`

**Triggers**:
- Push a cualquier branch
- Pull Request a branches principales (main, master, develop)

**Jobs**:

1. **static-analysis**: Análisis estático de código
   - Code formatting check (ruff)
   - Type checking (mypy)
   - Security scan (Semgrep)
   - Dependency audit (pip-audit)

2. **test**: Tests unitarios e integración
   - Tests unitarios con SQLite en memoria
   - Tests de integración con PostgreSQL y Redis
   - Cobertura de código con Codecov

3. **docker-build**: Validación de construcción Docker
   - Build de imagen API sin push
   - Validación de Dockerfile

4. **e2e-test**: Tests End-to-End (solo branches principales)
   - Levanta todo el stack con Docker Compose
   - Tests de smoke en endpoints reales
   - Tests de WebSocket

5. **quality-gate**: Validación final
   - Verifica que todos los jobs anteriores sean exitosos
   - Actúa como gate para el pipeline de CD

### 2. Pipeline de CD (Entrega Continua)

**Archivo**: `.github/workflows/cd.yml`

**Triggers**:
- Completion exitosa del workflow CI en branches principales
- Trigger manual con selección de ambiente

**Jobs**:

1. **check-ci**: Verificación previa
   - Valida que el CI fue exitoso

2. **build-and-push-images**: Construcción y publicación
   - Build de imágenes Docker para producción
   - Push a GitHub Container Registry
   - Cache optimizado para builds rápidos

3. **deploy-staging**: Despliegue a Staging
   - Deploy automático a ambiente de staging
   - Smoke tests post-deployment
   - Ambiente protegido con revisiones manuales

4. **deploy-production**: Despliegue a Producción
   - Deploy a producción solo con aprobación manual
   - Smoke tests post-deployment
   - Notificaciones de éxito/fallo

### 3. Pipeline de Release

**Archivo**: `.github/workflows/release.yml`

**Triggers**:
- Push de tags con formato `v*.*.*`
- Trigger manual con input de versión

**Jobs**:

1. **validate-release**: Validación de release
   - Valida formato de versión semántica
   - Determina si es pre-release

2. **build-release-artifacts**: Artefactos de release
   - Build de imágenes tagged para release
   - Push con tags semánticos

3. **generate-changelog**: Generación de changelog
   - Changelog automático basado en commits
   - Comparación con tag anterior

4. **create-github-release**: Creación de GitHub Release
   - Release note automático
   - Incluye changelog y instrucciones de deployment

## Configuración de Ambientes

### Variables de Entorno Requeridas

**Para CI**:
- `CODECOV_TOKEN`: Token para subir cobertura a Codecov (opcional)

**Para CD**:
- `STAGING_SERVER_HOST`: Host del servidor de staging
- `STAGING_SSH_KEY`: Clave SSH para staging
- `PROD_SERVER_HOST`: Host del servidor de producción
- `PROD_SSH_KEY`: Clave SSH para producción

**Para Release**:
- `GITHUB_TOKEN`: Automáticamente disponible (permisos de contents:write requeridos)

### Secrets de GitHub

Configurar en Settings → Secrets and Variables → Actions:

```
STAGING_SERVER_HOST=staging.grupogad.com
STAGING_SSH_KEY=<ssh-private-key>
PROD_SERVER_HOST=grupogad.com
PROD_SSH_KEY=<ssh-private-key>
CODECOV_TOKEN=<codecov-token>
```

### Ambientes Protegidos

Configurar en Settings → Environments:

**staging**:
- Deployment protection: Ninguna
- Environment secrets: Variables específicas de staging

**production**:
- Deployment protection: Required reviewers
- Environment secrets: Variables específicas de producción
- Deployment branches: Solo main/master

## Flujos de Trabajo

### Desarrollo Normal

1. **Feature Branch**:
   ```bash
   git checkout -b feature/nueva-funcionalidad
   # Desarrollar funcionalidad
   git push origin feature/nueva-funcionalidad
   ```
   
2. **Pull Request**:
   - Se ejecuta CI pipeline completo
   - Review de código requerido
   - CI debe pasar antes de merge

3. **Merge a Main**:
   - CI se ejecuta nuevamente
   - CD despliega automáticamente a staging
   - Producción requiere aprobación manual

### Release

1. **Crear Release**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Pipeline Automático**:
   - Validación de versión
   - Build de artefactos
   - Creación de GitHub Release
   - Imágenes Docker taggeadas

### Rollback

Para rollback en producción:

1. **Identificar versión anterior**:
   ```bash
   # Ver releases disponibles
   docker images ghcr.io/eevans-d/grupo_gad/api
   ```

2. **Deploy versión anterior**:
   - Usar el workflow de CD manualmente
   - Especificar la imagen anterior en el docker-compose

## Monitoreo de Pipelines

### Métricas Importantes

- **Tiempo de CI**: Objetivo < 15 minutos
- **Tiempo de CD a Staging**: Objetivo < 10 minutos
- **Tiempo de CD a Producción**: Objetivo < 15 minutos
- **Tasa de éxito de CI**: Objetivo > 95%
- **Cobertura de código**: Objetivo > 80%

### Alertas

Configurar notificaciones para:
- Fallos de CI en main/master
- Fallos de deployment a staging
- Fallos de deployment a producción
- Cobertura de código por debajo del umbral

## Mejores Prácticas

### Para Desarrolladores

1. **Commits**:
   - Usar conventional commits para changelog automático
   - Ejemplo: `feat: agregar endpoint de usuarios`

2. **Tests**:
   - Escribir tests antes de abrir PR
   - Mantener cobertura > 80%

3. **Branches**:
   - Feature branches para nuevas funcionalidades
   - Hotfix branches para fixes urgentes

### Para DevOps

1. **Secrets**:
   - Rotar secrets regularmente
   - Usar secrets específicos por ambiente

2. **Monitoring**:
   - Monitorear logs de deployment
   - Configurar alertas de fallo

3. **Rollback**:
   - Tener plan de rollback documentado
   - Practicar rollbacks en staging

## Troubleshooting

### CI Falla

1. **Tests fallan**:
   ```bash
   # Ejecutar localmente
   make test
   make test-cov
   ```

2. **Lint falla**:
   ```bash
   # Corregir formato
   make fmt
   make lint
   ```

3. **Type checking falla**:
   ```bash
   # Revisar tipos
   make type
   ```

### CD Falla

1. **Build falla**:
   - Verificar Dockerfile
   - Revisar logs de build

2. **Deploy falla**:
   - Verificar conectividad a servidores
   - Revisar logs del servidor

3. **Smoke tests fallan**:
   - Verificar que servicios estén running
   - Revisar configuración de red

## Próximos Pasos

1. **Implementar Blue-Green Deployment**
2. **Añadir Tests de Performance**
3. **Configurar Monitoring avanzado**
4. **Implementar Feature Flags**
5. **Añadir Tests de Seguridad automatizados**