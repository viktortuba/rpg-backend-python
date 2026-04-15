#!/usr/bin/env bash
# Run unit tests for all (or specific) services inside Docker.
# Tests use an in-memory SQLite DB — no running Postgres or Redis required.
#
# Usage:
#   bash test_scripts/run_tests.sh              # run all three services
#   bash test_scripts/run_tests.sh account      # run account_service only
#   bash test_scripts/run_tests.sh character    # run character_service only
#   bash test_scripts/run_tests.sh combat       # run combat_service only

set -euo pipefail

SERVICES=("account" "character" "combat")

if [ $# -gt 0 ]; then
  SERVICES=("$@")
fi

PASS=0
FAIL=0

for svc in "${SERVICES[@]}"; do
  echo ""
  echo "══════════════════════════════════════════════"
  echo "  Testing: ${svc}_service"
  echo "══════════════════════════════════════════════"
  if docker compose run --rm "${svc}_service" pytest; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
  fi
done

echo ""
echo "══════════════════════════════════════════════"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "══════════════════════════════════════════════"

[ "$FAIL" -eq 0 ]
