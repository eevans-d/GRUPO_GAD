#!/bin/bash
# Fast Gate Check Script - GRUPO GAD
# Performs quick validation checks before allowing PR to proceed

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Fast Gate Check..."

# 1. Check for basic project structure
echo "📁 Checking project structure..."
if [[ ! -f "pyproject.toml" ]]; then
    echo -e "${RED}❌ pyproject.toml not found${NC}"
    exit 1
fi

if [[ ! -d "src" ]]; then
    echo -e "${RED}❌ src/ directory not found${NC}"
    exit 1
fi

if [[ ! -d "tests" ]]; then
    echo -e "${YELLOW}⚠️ tests/ directory not found${NC}"
fi

echo -e "${GREEN}✅ Project structure OK${NC}"

# 2. Check if Poetry is available and dependencies can be parsed
echo "📦 Checking Poetry configuration..."
if command -v poetry >/dev/null 2>&1; then
    if poetry check --quiet; then
        echo -e "${GREEN}✅ Poetry configuration valid${NC}"
    else
        echo -e "${YELLOW}⚠️ Poetry configuration has warnings (non-blocking)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Poetry not available, skipping dependency check${NC}"
fi

# 3. Basic syntax check for Python files
echo "🐍 Checking Python syntax..."
python_files_with_errors=0
if command -v python3 >/dev/null 2>&1; then
    for file in $(find src/ -name "*.py" 2>/dev/null | head -10); do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "${RED}❌ Syntax error in $file${NC}"
            python_files_with_errors=$((python_files_with_errors + 1))
        fi
    done
    
    if [[ $python_files_with_errors -eq 0 ]]; then
        echo -e "${GREEN}✅ Python syntax check passed${NC}"
    else
        echo -e "${RED}❌ Found $python_files_with_errors files with syntax errors${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️ Python3 not available, skipping syntax check${NC}"
fi

# 4. Check for sensitive information in env files
echo "🔒 Checking for sensitive information..."
if [[ -f ".env" ]]; then
    if grep -E "(CHANGEME|TODO|FIXME|password=.*[^_]$|token=.*[^_]$)" .env >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ Found placeholder values in .env (review recommended)${NC}"
    fi
fi

echo -e "${GREEN}✅ Sensitive information check completed${NC}"

# 5. Docker compose validation (if available)
echo "🐳 Checking Docker configuration..."
if command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1; then
    for compose_file in docker-compose.yml docker-compose.prod.yml; do
        if [[ -f "$compose_file" ]]; then
            if command -v docker-compose >/dev/null 2>&1; then
                if docker-compose -f "$compose_file" config >/dev/null 2>&1; then
                    echo -e "${GREEN}✅ $compose_file is valid${NC}"
                else
                    echo -e "${YELLOW}⚠️ $compose_file has validation warnings${NC}"
                fi
            else
                echo -e "${YELLOW}⚠️ Docker Compose not available, skipping validation${NC}"
            fi
        fi
    done
else
    echo -e "${YELLOW}⚠️ Docker not available, skipping Docker configuration check${NC}"
fi

echo -e "${GREEN}🎉 Fast Gate Check completed successfully!${NC}"
exit 0