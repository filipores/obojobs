#!/usr/bin/env bash
# colors.sh - Central Color Definitions for RALPH
# Shared library for all Ralph modes
# Avoids duplicate definitions in individual modules

# Standard colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color
BOLD='\033[1m'

# Export for subshells
export RED GREEN YELLOW BLUE PURPLE CYAN NC BOLD
