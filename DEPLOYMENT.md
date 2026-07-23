# Build and deployment

The deployment serves Angular and the API at one origin: the frontend proxies
`/api/*` to FastAPI. This avoids browser CORS issues and means only the frontend
service needs public exposure.

## Local Docker Compose

1. Copy `.env.example` to `.env` and replace `POSTGRES_PASSWORD` and
   `SECRET_KEY` (and optionally `OPENAI_API_KEY`).
2. Start the full stack:

   ```sh
   docker compose up --build
   ```

3. Open `http://localhost:8080`. The frontend sends API calls through the same
   origin at `/api`; use `docker compose exec backend` for backend troubleshooting.

The `migrate` container runs Alembic before the backend starts. To reset local
data, intentionally remove the named `postgres-data` volume with Docker.

## Build and publish images

Build the two images from the repository root, replacing the registry and tag:

```sh
docker build -t ghcr.io/your-org/finance-ai-backend:1.0.0 finance-ai-backend
docker build -t ghcr.io/your-org/finance-ai-frontend:1.0.0 finance-ai-frontend
docker push ghcr.io/your-org/finance-ai-backend:1.0.0
docker push ghcr.io/your-org/finance-ai-frontend:1.0.0
```

## Kubernetes with Helm

Create a private `values-production.yaml` outside source control. At a minimum,
provide immutable image tags, a unique database password, an application secret,
and the public hostname.

```yaml
backend:
  image: { repository: ghcr.io/your-org/finance-ai-backend, tag: "1.0.0" }
frontend:
  image: { repository: ghcr.io/your-org/finance-ai-frontend, tag: "1.0.0" }
database:
  password: a-strong-database-password
secrets:
  secretKey: a-long-random-application-secret
  openaiApiKey: ""
config:
  corsOrigins: "https://finance-ai.example.com"
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: finance-ai.example.com
      paths: [{ path: /, pathType: Prefix }]
```

Validate and deploy:

```sh
helm lint helm/finance-ai
helm upgrade --install finance-ai helm/finance-ai --namespace finance-ai --create-namespace --values values-production.yaml --wait
```

The chart includes a persistent single-replica PostgreSQL instance for simple
deployments and runs Alembic after installation and before upgrades. For a
production platform, point the app at a managed PostgreSQL service by adapting
the chart secret and disabling the bundled database resources.
