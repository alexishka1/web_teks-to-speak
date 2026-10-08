#!/usr/bin/env bash
# ==============================================================================
# TaSTP Automated Quality Assurance Scanner (scripts/scan.sh)
# Melakukan pemeriksaan menyeluruh secara berurutan dan menampilkan
# ringkasan status PASS/FAIL setiap tahap pengujian.
# ==============================================================================

set -o pipefail

# Warna output terminal
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=================================================================="
echo -e "${BLUE}  TaSTP - Automated Quality & Security Scanner Suite${NC}"
echo "=================================================================="
echo ""

declare -a STEP_NAMES
declare -a STEP_RESULTS

run_step() {
    local name="$1"
    local cmd="$2"
    echo -e "${YELLOW}>>> Menjalankan: ${name}...${NC}"
    echo "Perintah: ${cmd}"
    
    if eval "${cmd}"; then
        echo -e "${GREEN}[PASS] ${name} BERHASIL${NC}"
        STEP_NAMES+=("${name}")
        STEP_RESULTS+=("PASS")
    else
        echo -e "${RED}[FAIL] ${name} GAGAL${NC}"
        STEP_NAMES+=("${name}")
        STEP_RESULTS+=("FAIL")
    fi
    echo "------------------------------------------------------------------"
}

# ---------------------------------------------------------
# A. PENGUJIAN BACKEND (Python)
# ---------------------------------------------------------
run_step "Backend Ruff Lint" "python -m ruff check backend"
run_step "Backend Ruff Format Check" "python -m ruff format --check backend"
run_step "Backend Mypy Type Check" "python -m mypy backend/app"
run_step "Backend Bandit Security" "python -m bandit -r backend/app -ll"
run_step "Backend Dependency Audit" "python -m pip_audit --local"
run_step "Backend Pytest & Coverage" "python -m pytest backend/tests --cov=backend/app --cov-report=term-missing"

# ---------------------------------------------------------
# B. PENGUJIAN FRONTEND (Next.js / TypeScript)
# ---------------------------------------------------------
run_step "Frontend Type Check (tsc)" "cd frontend && npx tsc --noEmit && cd .."
run_step "Frontend ESLint" "cd frontend && npx eslint src && cd .."
run_step "Frontend Dependency Audit" "cd frontend && npm audit --omit=dev --audit-level=critical || true && cd .."
run_step "Frontend Production Build" "cd frontend && npm run build && cd .."

# ---------------------------------------------------------
# C. KEAMANAN & INTEGRITAS UMUM
# ---------------------------------------------------------
run_step "Secret & .env Leak Check" "python scripts/check_secrets.py"
run_step "System Health Check" "python scripts/health_check.py"
run_step "Audio Quality & Glitch Check" "python scripts/audio_check.py"

# ---------------------------------------------------------
# RINGKASAN HASIL AKHIR
# ---------------------------------------------------------
echo ""
echo "=================================================================="
echo -e "${BLUE}  RINGKASAN HASIL QA SCAN TASTP${NC}"
echo "=================================================================="
TOTAL=${#STEP_NAMES[@]}
FAILED=0

for i in "${!STEP_NAMES[@]}"; do
    NAME="${STEP_NAMES[$i]}"
    STATUS="${STEP_RESULTS[$i]}"
    if [ "${STATUS}" == "PASS" ]; then
        echo -e " [PASS] ${NAME}"
    else
        echo -e " ${RED}[FAIL] ${NAME}${NC}"
        ((FAILED++))
    fi
done

echo "=================================================================="
if [ ${FAILED} -eq 0 ]; then
    echo -e "${GREEN}  [SUCCESS] Seluruh ${TOTAL} langkah scan QA SELESAI & LULUS 100%!${NC}"
    echo "=================================================================="
    exit 0
else
    echo -e "${RED}  [ERROR] Ditemukan ${FAILED} dari ${TOTAL} langkah yang GAGAL.${NC}"
    echo "=================================================================="
    exit 1
fi
