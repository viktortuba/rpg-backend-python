#!/usr/bin/env bash
# End-to-end smoke test for the RPG backend
# Prerequisites: services running via docker compose up --build
# Usage: bash test_scripts/e2e.sh

set -euo pipefail

ACCOUNT="http://localhost:8001"
CHARACTER="http://localhost:8002"
COMBAT="http://localhost:8003"

GREEN="\033[32m"
RED="\033[31m"
BOLD="\033[1m"
RESET="\033[0m"

pass() { echo -e "${GREEN}✓ $1${RESET}"; }
fail() { echo -e "${RED}✗ $1${RESET}"; exit 1; }
step() { echo -e "\n${BOLD}==> $1${RESET}"; }
json() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }

# ── Health checks ────────────────────────────────────────────────────
step "Health checks"
curl -sf "$ACCOUNT/api/health"   | grep -q '"ok"' && pass "account_service healthy"
curl -sf "$CHARACTER/api/health" | grep -q '"ok"' && pass "character_service healthy"
curl -sf "$COMBAT/api/health"    | grep -q '"ok"' && pass "combat_service healthy"

# ── Register users ───────────────────────────────────────────────────
step "Register users"
SUFFIX=$RANDOM
curl -sf -X POST "$ACCOUNT/api/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"player1_$SUFFIX\",\"email\":\"p1_$SUFFIX@test.com\",\"password\":\"pass1234\"}" \
  | grep -q "player1" && pass "player1 registered"

curl -sf -X POST "$ACCOUNT/api/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"player2_$SUFFIX\",\"email\":\"p2_$SUFFIX@test.com\",\"password\":\"pass1234\"}" \
  | grep -q "player2" && pass "player2 registered"

curl -sf -X POST "$ACCOUNT/api/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"gm1_$SUFFIX\",\"email\":\"gm1_$SUFFIX@test.com\",\"password\":\"pass1234\",\"role\":\"GameMaster\"}" \
  | grep -q "GameMaster" && pass "GameMaster registered"

# ── Login ────────────────────────────────────────────────────────────
step "Login"
TOKEN1=$(curl -sf -X POST "$ACCOUNT/api/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"player1_$SUFFIX\",\"password\":\"pass1234\"}" | json "['access_token']")
pass "player1 JWT obtained (role=User)"

TOKEN2=$(curl -sf -X POST "$ACCOUNT/api/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"player2_$SUFFIX\",\"password\":\"pass1234\"}" | json "['access_token']")
pass "player2 JWT obtained (role=User)"

GM_TOKEN=$(curl -sf -X POST "$ACCOUNT/api/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"gm1_$SUFFIX\",\"password\":\"pass1234\"}" | json "['access_token']")
pass "GameMaster JWT obtained"

# ── GM list characters (empty) ───────────────────────────────────────
step "Authorization checks"
CHAR_LIST=$(curl -sf "$CHARACTER/api/character" -H "Authorization: Bearer $GM_TOKEN")
echo "$CHAR_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); assert isinstance(data, list)" && pass "GM can list characters"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CHARACTER/api/character" \
  -H "Authorization: Bearer $TOKEN1")
[ "$HTTP_CODE" = "403" ] && pass "Regular user gets 403 on character list"

# ── Get seeded classes ───────────────────────────────────────────────
step "Fetch seeded classes"
CLASSES=$(curl -sf "$CHARACTER/api/classes" -H "Authorization: Bearer $TOKEN1")
CLASS_ID=$(echo "$CLASSES" | python3 -c "import sys,json; classes=json.load(sys.stdin); print(classes[0]['id'])")
CLASS_NAME=$(echo "$CLASSES" | python3 -c "import sys,json; classes=json.load(sys.stdin); print(classes[0]['name'])")
pass "Classes available: $CLASS_NAME (id=$CLASS_ID)"

# ── Create characters ────────────────────────────────────────────────
step "Create characters"
CHAR1=$(curl -sf -X POST "$CHARACTER/api/character" \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Hero_$SUFFIX\",\"health\":100,\"mana\":50,\"base_strength\":10,\"base_agility\":5,\"base_intelligence\":8,\"base_faith\":3,\"class_id\":\"$CLASS_ID\"}")
CHAR1_ID=$(echo "$CHAR1" | json "['id']")
echo "$CHAR1" | grep -q "Hero_$SUFFIX" && pass "Character 1 created: Hero_$SUFFIX"
echo "$CHAR1" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['effective_stats']['strength'] == 10" \
  && pass "Effective stats computed correctly"

CHAR2=$(curl -sf -X POST "$CHARACTER/api/character" \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Villain_$SUFFIX\",\"health\":80,\"mana\":60,\"base_strength\":7,\"base_agility\":8,\"base_intelligence\":10,\"base_faith\":5,\"class_id\":\"$CLASS_ID\"}")
CHAR2_ID=$(echo "$CHAR2" | json "['id']")
echo "$CHAR2" | grep -q "Villain_$SUFFIX" && pass "Character 2 created: Villain_$SUFFIX"

# ── Create and grant item ────────────────────────────────────────────
step "Items"
ITEM=$(curl -sf -X POST "$CHARACTER/api/items" \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d '{"base_name":"Ancient Blade","bonus_strength":10,"bonus_agility":3}')
ITEM_ID=$(echo "$ITEM" | json "['id']")
echo "$ITEM" | grep -q "of Strength" && pass "Item name suffix correct: Ancient Blade of Strength"

curl -sf -X POST "$CHARACTER/api/items/grant" \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d "{\"character_id\":\"$CHAR1_ID\",\"item_id\":\"$ITEM_ID\"}" | grep -q "granted" && pass "Item granted to Hero"

CHAR1_DETAIL=$(curl -sf "$CHARACTER/api/character/$CHAR1_ID" \
  -H "Authorization: Bearer $TOKEN1")
echo "$CHAR1_DETAIL" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['effective_stats']['strength'] == 20" \
  && pass "Effective strength updated with item bonus (10+10=20)"

# ── GM list all items ────────────────────────────────────────────────
ITEMS=$(curl -sf "$CHARACTER/api/items" -H "Authorization: Bearer $GM_TOKEN")
echo "$ITEMS" | python3 -c "import sys,json; assert len(json.load(sys.stdin)) >= 1" && pass "GM can list items"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CHARACTER/api/items" \
  -H "Authorization: Bearer $TOKEN1")
[ "$HTTP_CODE" = "403" ] && pass "Regular user gets 403 on item list"

# ── Combat ───────────────────────────────────────────────────────────
step "Combat"
DUEL=$(curl -sf -X POST "$COMBAT/api/challenge" \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d "{\"challenger_id\":\"$CHAR1_ID\",\"defender_id\":\"$CHAR2_ID\"}")
DUEL_ID=$(echo "$DUEL" | json "['id']")
echo "$DUEL" | grep -q "active" && pass "Duel created and active"

ATTACK=$(curl -sf -X POST "$COMBAT/api/$DUEL_ID/attack" \
  -H "Authorization: Bearer $TOKEN1")
echo "$ATTACK" | grep -q "dealt" && pass "Attack action performed"
echo "$ATTACK" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['value'] > 0" \
  && pass "Attack dealt positive damage"

HEAL=$(curl -sf -X POST "$COMBAT/api/$DUEL_ID/heal" \
  -H "Authorization: Bearer $TOKEN1")
echo "$HEAL" | grep -q "healed" && pass "Heal action performed"

# Test cooldown
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$COMBAT/api/$DUEL_ID/attack" \
  -H "Authorization: Bearer $TOKEN1")
[ "$HTTP_CODE" = "429" ] && pass "Attack cooldown enforced (429)"

step "All tests passed!"
