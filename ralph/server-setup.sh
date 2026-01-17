#!/bin/bash
# Ralph Server Setup Script
# Führe aus mit: bash server-setup.sh

set -e

echo "=========================================="
echo "       Ralph Server Setup"
echo "=========================================="
echo ""

# 1. System Update
echo "[1/7] System Update..."
apt update && apt upgrade -y

# 2. Basis-Tools
echo "[2/7] Basis-Tools installieren..."
apt install -y \
    git \
    curl \
    wget \
    jq \
    tmux \
    htop \
    unzip \
    build-essential

# 3. Node.js 20 LTS
echo "[3/7] Node.js 20 LTS installieren..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
npm install -g npm@latest

# 4. Python 3 + pip
echo "[4/7] Python 3 installieren..."
apt install -y python3 python3-pip python3-venv

# 5. Claude CLI
echo "[5/7] Claude CLI installieren..."
npm install -g @anthropic-ai/claude-code

# 6. Playwright Dependencies (für Test/Explore Mode)
echo "[6/7] Playwright Dependencies installieren..."
npx playwright install-deps chromium

# 7. Git konfigurieren
echo "[7/7] Git konfigurieren..."
git config --global user.name "Ralph Server"
git config --global user.email "ralph@server.local"
git config --global init.defaultBranch main

echo ""
echo "=========================================="
echo "       Setup abgeschlossen!"
echo "=========================================="
echo ""
echo "Nächste Schritte:"
echo "  1. Claude CLI authentifizieren:"
echo "     claude auth login"
echo ""
echo "  2. SSH-Key für GitHub generieren:"
echo "     ssh-keygen -t ed25519 -C 'ralph-server'"
echo "     cat ~/.ssh/id_ed25519.pub"
echo "     -> Füge den Key bei GitHub hinzu"
echo ""
echo "  3. Projekt klonen:"
echo "     git clone git@github.com:DEIN-USER/obojobs.git"
echo ""
echo "  4. Ralph starten (in tmux):"
echo "     tmux new -s ralph"
echo "     cd obojobs/ralph/feature"
echo "     ./ralph.sh"
echo ""
