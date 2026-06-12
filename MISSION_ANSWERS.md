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
