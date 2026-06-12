# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1 — Anti-patterns found in basic app

1. Hardcoded `OPENAI_API_KEY` inside source code.
   - Risk: secret can be leaked when pushed to GitHub.

2. Hardcoded `DATABASE_URL` with username and password.
   - Risk: exposes database credentials and cannot change between environments.

3. Config values such as `DEBUG` and `MAX_TOKENS` are hardcoded.
   - Risk: app cannot be configured safely for dev/staging/production.

4. Uses `print()` for logging and logs the API key.
   - Risk: logs are unstructured and may leak secrets.

5. No `/health` endpoint.
   - Risk: cloud platform cannot detect whether the service is alive.

6. Binds to `localhost`.
   - Risk: app only accepts local traffic and may fail inside a cloud/container environment.

7. Hardcoded port `8000`.
   - Risk: platforms such as Railway/Render inject `PORT` dynamically.

8. `reload=True` is enabled.
   - Risk: debug reload should not run in production.

### Exercise 1.2 — Basic version run result

I successfully ran the basic localhost version from `01-localhost-vs-production/develop`.

Test commands:

```bash
curl http://localhost:8000/
curl -X POST "http://localhost:8000/ask?question=Hello"
```

Observed results:

GET / returned 200 OK with message: Hello! Agent is running on my machine :)
POST /ask?question=Hello returned 200 OK with an agent answer.
The server log showed the request was handled successfully.
The server also printed the hardcoded API key in logs, confirming this is an unsafe localhost-only anti-pattern.

Conclusion: the basic version works locally, but it is not production-ready.

### Exercise 1.3 — Localhost vs Production comparison

| Area | Basic localhost version | Production version | Why it matters |
|---|---|---|---|
| Configuration | Values are hardcoded in source code. | Values are loaded from environment variables in `config.py`. | Cloud deployments need different config for dev, staging, and production without changing code. |
| Secrets | API key and database URL are hardcoded. | Secrets are read from environment variables and are not logged. | Hardcoded secrets can leak through GitHub or logs. |
| Host binding | App binds to `localhost`. | App binds to `0.0.0.0`. | Containers and cloud platforms need the app to accept external traffic inside the container network. |
| Port | Port `8000` is hardcoded. | Port is read from `PORT` environment variable. | Platforms such as Railway and Render inject the port dynamically. |
| Logging | Uses `print()` and logs sensitive values. | Uses structured JSON logging and does not log secrets. | Production logs must be searchable, parseable, and safe. |
| Health checks | No `/health` endpoint. | Provides `/health`, `/ready`, and `/metrics`. | Cloud platforms use these endpoints to restart unhealthy containers and route traffic safely. |
| Reload mode | `reload=True` is enabled. | Reload is only enabled when `DEBUG=true`. | Auto-reload is useful in development but unsafe and inefficient in production. |
| Shutdown | No graceful shutdown handling. | Uses lifespan hooks and SIGTERM handling. | Cloud platforms stop and replace containers; graceful shutdown prevents broken in-flight requests. |

Production test results:

- `GET /` returned app metadata and `status: running`.
- `GET /health` returned `status: ok`.
- `GET /ready` returned `ready: true`.
- `POST /ask` returned a mock agent answer.
- The server ran on `0.0.0.0:8000`, which is suitable for container/cloud deployment.

Conclusion: the production version follows 12-factor principles better than the basic localhost version.

## Part 2: Docker

### Exercise 2.1 — Basic Dockerfile

1. Base image là gì?

The base image is `python:3.11`.

This means the container starts from an official Python 3.11 image that already includes Python and common system dependencies.

2. Working directory là gì?

The working directory is `/app`.

The line `WORKDIR /app` means all following commands such as `COPY`, `RUN`, and `CMD` will run inside `/app` in the container.

3. Tại sao COPY requirements.txt trước?

`requirements.txt` is copied before the application code to use Docker layer caching.

Dependencies usually change less often than source code. If only `app.py` changes, Docker can reuse the cached dependency installation layer instead of running `pip install` again. This makes rebuilds faster.

4. CMD vs ENTRYPOINT khác nhau thế nào?

`CMD` defines the default command that runs when the container starts. It is easy to override when running `docker run`.

`ENTRYPOINT` defines the main executable of the container. Arguments passed to `docker run` are usually appended to the entrypoint.

For this lab, `CMD ["python", "app.py"]` is enough because the container simply starts the FastAPI app.

### Exercise 2.2 — Build and run develop Docker image

Build command:

docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .

Image size observed:

- DISK USAGE: 1.66GB
- CONTENT SIZE: 424MB

Run command:

docker run -d --name my-agent-develop -p 8000:8000 my-agent:develop

Test results:

- `GET /health` returned `status: ok` and `container: true`.
- `POST /ask?question=What%20is%20Docker%3F` returned a mock agent answer.
- Sending JSON body to `/ask` returned a validation error because this develop version expects `question` as a query parameter.

Conclusion: the develop Docker image builds and runs successfully, but it is still basic and not fully production-ready.

### Exercise 2.3 — Multi-stage build

Stage 1: Builder

The first stage uses `python:3.11-slim AS builder`.

Its job is to install build dependencies such as `gcc` and `libpq-dev`, then install Python packages from `requirements.txt` into `/root/.local`.

This stage is only used during image build time. It is not the final deployed image.

Stage 2: Runtime

The second stage uses `python:3.11-slim AS runtime`.

Its job is to run the application with only the files needed at runtime:

- installed Python packages copied from the builder stage
- application source code
- `utils/mock_llm.py`

It also creates and uses a non-root user called `appuser`, which is safer for production.

Why is the image smaller?

The advanced image is smaller because the final runtime stage does not include build tools, temporary build files, or unnecessary dependencies from the builder stage. Only the installed runtime packages and application files are copied into the final image.

Image size comparison:

| Image | Disk usage | Content size |
|---|---:|---:|
| `my-agent:develop` | 1.66GB | 424MB |
| `my-agent:advanced` | 236MB | 56.6MB |

Conclusion: the multi-stage production image is much smaller and more secure than the single-stage develop image.

### Exercise 2.4 — Docker Compose stack

Services started:

- `agent`: FastAPI AI agent service.
- `redis`: cache for sessions and rate limiting.
- `qdrant`: vector database for RAG-style retrieval.
- `nginx`: reverse proxy and load balancer exposed on host ports 80 and 443.

Architecture diagram:

User / Browser / curl
  |
  v
Nginx reverse proxy on localhost:80
  |
  v
Agent service on internal Docker network, port 8000
  |
  +--> Redis on internal Docker network, port 6379
  |
  +--> Qdrant on internal Docker network, port 6333

How services communicate:

- The user sends requests to Nginx through `localhost:80`.
- Nginx proxies requests to the `agent` service using the Docker service name `agent:8000`.
- The agent can connect to Redis using `redis://redis:6379/0`.
- The agent can connect to Qdrant using `http://qdrant:6333`.
- Redis and Qdrant are not exposed directly to the host machine; they only communicate through the internal Docker network.

Test results:

- `docker compose ps` showed `agent`, `redis`, and `qdrant` as healthy.
- `GET http://localhost/health` returned `status: ok`.
- `POST http://localhost/ask` returned a mock agent answer.
- Nginx successfully routed requests from `localhost:80` to the internal agent service.

Conclusion: the Docker Compose stack successfully runs a production-like multi-service architecture with reverse proxy, cache, vector database, and internal networking.

## Part 3: Cloud Deployment

### Exercise 3.1 — Deploy Railway

Railway project:

- Project name: `trustworthy-gratitude`
- Service name: `day12-agent-railway`
- Public URL: `https://day12-agent-railway-production.up.railway.app`

Deployment result:

- Railway deployment completed successfully.
- Railway health check on `/health` succeeded.
- The service started successfully using the Railway-provided `PORT` environment variable.
- The app listened on `0.0.0.0`, which is required for cloud deployment.
- Environment variables were set on Railway for `PORT`, `ENVIRONMENT`, and `AGENT_API_KEY`.

Public URL test commands:

curl https://day12-agent-railway-production.up.railway.app/health

curl -X POST https://day12-agent-railway-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello from public Railway URL"}'

Observed results:

- `GET /health` returned `status: ok`, `platform: Railway`, and a timestamp.
- `POST /ask` returned the question, an agent answer, and `platform: Railway`.

Conclusion: the agent was successfully deployed to Railway and is reachable through a public HTTPS URL.

### Exercise 3.2 — Render vs Railway configuration

Railway uses `railway.toml`, while Render uses `render.yaml`.

Key differences:

| Area | Railway `railway.toml` | Render `render.yaml` |
|---|---|---|
| Build system | Uses `builder = "NIXPACKS"`, so Railway auto-detects the Python app. | Uses explicit `runtime: python` and `buildCommand: pip install -r requirements.txt`. |
| Start command | Uses `startCommand = "uvicorn app:app --host 0.0.0.0 --port $PORT"`. | Also uses `startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT`. |
| Health check | Defines `healthcheckPath = "/health"` and `healthcheckTimeout = 30`. | Defines `healthCheckPath: /health`. |
| Infrastructure definition | Focuses mainly on build and deploy behavior for one service. | Defines infrastructure more explicitly, including web service, region, plan, Redis service, and environment variables. |
| Environment variables | Set using Railway Dashboard or Railway CLI. | Some variables are defined in `render.yaml`; secrets can be manually set in the Render Dashboard using `sync: false`, or generated with `generateValue: true`. |
| Extra services | The Railway example only deploys the web agent service. | The Render blueprint also defines a Redis service named `agent-cache`. |
| Auto deploy | Railway can deploy from CLI using `railway up`. | Render uses `autoDeploy: true`, so it redeploys automatically when code is pushed to GitHub. |
| Region/plan | Not specified in `railway.toml`. | Explicitly sets `region: singapore` and `plan: free`. |

Similarities:

- Both platforms inject the `PORT` environment variable.
- Both require the app to bind to `0.0.0.0`.
- Both use `/health` as the cloud health check endpoint.
- Both can store secrets outside the source code.
- Both are suitable for deploying the FastAPI agent publicly.

Conclusion:

Railway is simpler for quick CLI-based deployment and prototypes. Render is more explicit as infrastructure-as-code because `render.yaml` can describe the web service, Redis service, region, plan, environment variables, health checks, and auto-deploy behavior in one file.
