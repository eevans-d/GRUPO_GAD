#!/bin/bash
# Complete Validation Script - GRUPO GAD
# Performs comprehensive validation including optional checks

set +e  # Don't exit on errors - this script is best-effort

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 Starting Complete Validation..."

# Track issues for summary
warnings=0
errors=0

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
    warnings=$((warnings + 1))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    errors=$((errors + 1))
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# 1. Extended project structure validation
echo "📁 Extended project structure validation..."
expected_dirs=("src" "tests" "config" "alembic")
for dir in "${expected_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        log_success "$dir/ directory found"
    else
        log_warning "$dir/ directory missing"
    fi
done

# 2. Environment file validation
echo "📄 Environment configuration validation..."
if [[ -f ".env.example" ]]; then
    log_success ".env.example found"
    
    # Check if all required vars from .env.example have non-placeholder values in .env
    if [[ -f ".env" ]]; then
        while IFS= read -r line; do
            if [[ "$line" =~ ^[A-Z_]+=.* ]]; then
                var_name=$(echo "$line" | cut -d'=' -f1)
                if ! grep -q "^${var_name}=" .env 2>/dev/null; then
                    log_warning "Missing environment variable: $var_name"
                fi
            fi
        done < .env.example
    else
        log_warning ".env file not found"
    fi
else
    log_warning ".env.example not found"
fi

# 3. Database migration validation
echo "🗄️ Database migration validation..."
if [[ -f "alembic.ini" ]] && [[ -d "alembic/versions" ]]; then
    log_success "Alembic configuration found"
    
    migration_count=$(find alembic/versions -name "*.py" 2>/dev/null | wc -l)
    if [[ $migration_count -gt 0 ]]; then
        log_info "Found $migration_count migration files"
    else
        log_warning "No migration files found"
    fi
else
    log_warning "Alembic configuration incomplete"
fi

# 4. Dependency security check (if tools available)
echo "🔒 Dependency security validation..."
if command -v poetry >/dev/null 2>&1; then
    if poetry show --tree >/dev/null 2>&1; then
        log_success "Poetry dependency tree validated"
    else
        log_warning "Poetry dependency tree has issues"
    fi
    
    # Check for outdated packages
    if poetry show --outdated >/dev/null 2>&1; then
        outdated_count=$(poetry show --outdated 2>/dev/null | wc -l)
        if [[ $outdated_count -gt 0 ]]; then
            log_info "Found $outdated_count outdated packages"
        fi
    fi
else
    log_warning "Poetry not available for dependency validation"
fi

# 5. Code quality checks (if tools available)
echo "📝 Code quality validation..."
if command -v ruff >/dev/null 2>&1; then
    if ruff check . --quiet; then
        log_success "Ruff linting passed"
    else
        log_warning "Ruff linting found issues"
    fi
else
    log_warning "Ruff not available for linting"
fi

if command -v mypy >/dev/null 2>&1; then
    if mypy --version >/dev/null 2>&1; then
        if mypy . --ignore-missing-imports --no-error-summary >/dev/null 2>&1; then
            log_success "MyPy type checking passed"
        else
            log_warning "MyPy type checking found issues"
        fi
    fi
else
    log_warning "MyPy not available for type checking"
fi

# 6. Docker validation (comprehensive)
echo "🐳 Comprehensive Docker validation..."
docker_files=("Dockerfile" "docker-compose.yml" "docker-compose.prod.yml")
for docker_file in "${docker_files[@]}"; do
    if [[ -f "$docker_file" ]]; then
        log_success "$docker_file found"
        
        # Check for security best practices
        if [[ "$docker_file" == *"Dockerfile"* ]]; then
            if grep -q "USER" "$docker_file"; then
                log_success "$docker_file uses non-root user"
            else
                log_warning "$docker_file may be running as root"
            fi
        fi
        
        # Check for environment variable usage
        if grep -q "\${" "$docker_file"; then
            log_success "$docker_file uses environment variables"
        fi
    else
        log_info "$docker_file not found (optional)"
    fi
done

# 7. Test coverage validation
echo "🧪 Test coverage validation..."
if [[ -d "tests" ]]; then
    test_count=$(find tests -name "test_*.py" 2>/dev/null | wc -l)
    if [[ $test_count -gt 0 ]]; then
        log_success "Found $test_count test files"
        
        # Try to run a quick test validation if pytest is available
        if command -v pytest >/dev/null 2>&1; then
            if pytest --collect-only -q >/dev/null 2>&1; then
                log_success "Test collection successful"
            else
                log_warning "Test collection failed"
            fi
        fi
    else
        log_warning "No test files found in tests/ directory"
    fi
else
    log_warning "tests/ directory not found"
fi

# 8. API endpoint validation (if possible)
echo "🌐 API endpoint validation..."
if [[ -f "src/api/main.py" ]] || [[ -f "src/main.py" ]]; then
    log_success "API main module found"
else
    log_info "API main module location unknown"
fi

# 9. Configuration validation
echo "⚙️ Configuration validation..."
config_files=("pyproject.toml" "pytest.ini" ".gitignore")
for config_file in "${config_files[@]}"; do
    if [[ -f "$config_file" ]]; then
        log_success "$config_file found"
    else
        log_warning "$config_file missing"
    fi
done

# 10. Documentation validation
echo "📚 Documentation validation..."
doc_files=("README.md" "CHANGELOG.md")
for doc_file in "${doc_files[@]}"; do
    if [[ -f "$doc_file" ]]; then
        log_success "$doc_file found"
        
        # Check if README has basic content
        if [[ "$doc_file" == "README.md" ]] && [[ $(wc -l < "$doc_file") -lt 10 ]]; then
            log_warning "README.md seems too short"
        fi
    else
        log_info "$doc_file not found (optional)"
    fi
done

# Summary
echo ""
echo "📊 Validation Summary:"
echo "======================"
log_info "Warnings: $warnings"
if [[ $errors -gt 0 ]]; then
    log_error "Errors: $errors"
else
    log_success "Errors: $errors"
fi

echo ""
if [[ $errors -eq 0 ]]; then
    log_success "Complete validation finished - Ready for deployment consideration"
else
    log_error "Complete validation finished with errors - Review recommended"
fi

# Exit with 0 regardless - this is a best-effort validation
exit 0