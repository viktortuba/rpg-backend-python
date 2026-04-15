#!/usr/bin/env bash
# Generates backend/.env with a cryptographically secure JWT_SECRET.
# Safe to re-run: will not overwrite an existing .env unless --force is passed.
#
# Usage:
#   bash setup_env.sh           # create .env if it does not exist
#   bash setup_env.sh --force   # overwrite existing .env

set -euo pipefail

ENV_FILE="$(dirname "$0")/.env"

if [ -f "$ENV_FILE" ] && [ "${1:-}" != "--force" ]; then
  echo ".env already exists. Use --force to overwrite."
  exit 0
fi

JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

cat > "$ENV_FILE" <<EOF
JWT_SECRET=$JWT_SECRET
JWT_EXPIRE_HOURS=24
EOF

echo ".env created with a secure JWT_SECRET."
