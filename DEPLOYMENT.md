# Deployment Report

## Platform

The final production-ready AI agent was deployed on Railway.

Public URL:

https://day12-agent-railway-production.up.railway.app

Railway project:

- Workspace: Thái Nhi's Projects
- Project: trustworthy-gratitude
- Environment: production
- Service: day12-agent-railway
- Region: sfo

## Application

The deployed app is the final root-level Day 12 production agent.

Main files:

- app/main.py
- app/config.py
- app/auth.py
- app/rate_limiter.py
- app/cost_guard.py
- Dockerfile
- docker-compose.yml
- requirements.txt
- railway.toml
- .env.example

## Environment Variables

Required environment variables:

- AGENT_API_KEY
- ENVIRONMENT
- RATE_LIMIT_PER_MINUTE
- MONTHLY_BUDGET_USD
- PORT

Railway values used for testing:

- AGENT_API_KEY=local-dev-key
- ENVIRONMENT=production
- RATE_LIMIT_PER_MINUTE=10
- MONTHLY_BUDGET_USD=10.0

The real production API key should be changed before public or long-term use.

## Health Check

Command:

    curl https://day12-agent-railway-production.up.railway.app/health

Observed result:

- HTTP 200
- status: ok
- environment: production
- version: 1.0.0

## Readiness Check

Command:

    curl https://day12-agent-railway-production.up.railway.app/ready

Observed result:

- HTTP 200
- ready: true

## Authentication Test

Command without API key:

    curl -i -X POST https://day12-agent-railway-production.up.railway.app/ask \
      -H "Content-Type: application/json" \
      -d '{"question":"No auth public test"}'

Observed result:

- HTTP 401 Unauthorized
- detail: Missing API key

Command with API key:

    curl -i -X POST https://day12-agent-railway-production.up.railway.app/ask \
      -H "X-API-Key: local-dev-key" \
      -H "X-User-ID: railway-user" \
      -H "Content-Type: application/json" \
      -d '{"question":"Hello final Railway app","user_id":"railway-user"}'

Observed result:

- HTTP 200 OK
- user_id: railway-user
- history_count: 2
- rate_limit: 10 requests per minute
- budget: 10 USD per month

## Docker Compose Local Test

Command:

    docker compose up -d --build

Observed result:

- agent container: healthy
- redis container: healthy
- app exposed at localhost:8000

Docker health result:

- GET /health returned HTTP 200
- storage: redis
- redis_connected: true

## Rate Limit Test

Local Docker test:

- Requests 1 to 10 returned HTTP 200.
- Request 11 returned HTTP 429.
- Request 12 returned HTTP 429.

This confirms the 10 requests per minute limit.

## Screenshots

Screenshots can be stored in the screenshots/ folder.

Suggested screenshots:

- Railway successful deployment
- Railway public URL
- Public /health response
- Public authenticated /ask response
- Docker Compose healthy containers
