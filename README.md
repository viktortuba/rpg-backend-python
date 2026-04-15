# RPG Backend

Microservice-based RPG game backend built with Python and FastAPI. See [REQUIREMENTS.md](REQUIREMENTS.md) for the full project specification.

## Services

| Service | Port | Responsibility |
|---|---|---|
| Account | 8001 | Registration, login, JWT issuance |
| Character | 8002 | Characters, items, classes, Redis caching |
| Combat | 8003 | Turn-based duels, item transfer on win |

## Start

```bash
cd backend
bash setup_env.sh         # generates .env with a secure JWT_SECRET
docker compose up --build
```

To regenerate the secret (e.g. after a key rotation): `bash setup_env.sh --force`

API docs for each service: `http://localhost:<port>/docs`

## Test

Tests run inside Docker — no local Python install needed.

```bash
cd backend

# All services
bash test_scripts/run_tests.sh

# Single service
bash test_scripts/run_tests.sh account
bash test_scripts/run_tests.sh character
bash test_scripts/run_tests.sh combat
```

## End-to-end smoke test

Requires all services to be running.

```bash
cd backend
bash test_scripts/e2e.sh
```
