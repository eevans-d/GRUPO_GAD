#!/usr/bin/env bash
set -euo pipefail

# Create a bare mirror backup of the repo for safe experiments (pushes, history rewrite)
REPO_DIR=$(pwd)
BACKUP_DIR="${REPO_DIR}/backups/git-mirror-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"

echo "Creating bare mirror in $BACKUP_DIR"
git clone --mirror "$REPO_DIR" "$BACKUP_DIR"

echo "Backup created. Verify contents and move to safe storage."
