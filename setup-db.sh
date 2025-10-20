#!/bin/bash

# 🚀 GRUPO_GAD - PostgreSQL Setup Script
# Interactive tool to configure DATABASE_URL

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     🐘 GRUPO_GAD - PostgreSQL Setup for Fly.io         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${YELLOW}Choose PostgreSQL provider:${NC}\n"
echo "1) ${GREEN}Supabase${NC}    ⭐ Recommended (5min setup)"
echo "2) ${GREEN}Render${NC}      ⚡ Faster (3min setup)"
echo "3) ${GREEN}Railway${NC}     🔄 Reuse existing"
echo "4) ${GREEN}Manual${NC}      🔧 Paste DATABASE_URL directly"
echo "5) ${RED}Exit${NC}"
echo ""

read -p "Enter option (1-5): " OPTION

case $OPTION in
    1)
        echo -e "\n${BLUE}📘 Supabase Setup:${NC}"
        echo "1. Go to https://supabase.com"
        echo "2. Sign up or Login"
        echo "3. Create new project 'grupo-gad-db'"
        echo "4. Go to Settings → Database → Connection pooling"
        echo "5. Copy the 'postgresql://...' URL"
        echo ""
        read -p "Paste your Supabase CONNECTION STRING: " DATABASE_URL
        ;;
    2)
        echo -e "\n${BLUE}⚡ Render Setup:${NC}"
        echo "1. Go to https://render.com/dashboard"
        echo "2. Click 'New +' → PostgreSQL"
        echo "3. Name: grupo-gad-db"
        echo "4. Select Free tier"
        echo "5. Copy the DATABASE_URL"
        echo ""
        read -p "Paste your Render DATABASE_URL: " DATABASE_URL
        ;;
    3)
        echo -e "\n${BLUE}🔄 Railway Reuse:${NC}"
        echo "1. Go to https://railway.app/dashboard"
        echo "2. Find existing PostgreSQL plugin"
        echo "3. Copy connection string"
        echo ""
        read -p "Paste your Railway DATABASE_URL: " DATABASE_URL
        ;;
    4)
        echo -e "\n${BLUE}🔧 Manual Entry:${NC}"
        read -p "Paste DATABASE_URL: " DATABASE_URL
        ;;
    5)
        echo -e "${YELLOW}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL cannot be empty${NC}"
    exit 1
fi

# Validate format
if [[ ! $DATABASE_URL =~ ^postgresql:// ]]; then
    echo -e "${RED}ERROR: URL must start with 'postgresql://'${NC}"
    exit 1
fi

echo -e "\n${GREEN}✅ DATABASE_URL validated${NC}"
echo ""
echo -e "${YELLOW}Next step: Configure in Fly.io${NC}"
echo ""
echo "Running: ${BLUE}flyctl secrets set DATABASE_URL=...${NC}"
echo ""

# Setup PATH and TOKEN
export PATH="/home/eevan/.fly/bin:$PATH"
if [ -z "$FLY_API_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  FLY_API_TOKEN not set${NC}"
    echo "Set it with: ${BLUE}export FLY_API_TOKEN='your-token'${NC}"
    exit 1
fi

# Set the secret
flyctl secrets set DATABASE_URL="$DATABASE_URL" -a grupo-gad

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ DATABASE_URL configured in Fly.io${NC}"
    echo ""
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo ""
    echo "1. Uncomment 'release_command' in fly.toml:"
    echo "   ${BLUE}release_command = \"alembic upgrade head\"${NC}"
    echo ""
    echo "2. Commit changes:"
    echo "   ${BLUE}git add fly.toml && git commit -m 'enable: release_command'${NC}"
    echo ""
    echo "3. Redeploy:"
    echo "   ${BLUE}flyctl deploy --local-only -a grupo-gad${NC}"
    echo ""
    echo "4. Verify:"
    echo "   ${BLUE}flyctl logs -a grupo-gad --follow${NC}"
    echo ""
else
    echo -e "\n${RED}❌ Failed to set DATABASE_URL${NC}"
    exit 1
fi
