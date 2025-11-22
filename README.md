# ui-story

A Django application for storing and comparing UI screenshots across different branches and projects. Supports OIDC authentication for secure uploads from GitLab CI/CD pipelines.

## Features

- **Screenshot Storage**: Upload screenshots with metadata including project, branch, datetime, pipeline URL, viewport size, and page name
- **OIDC Authentication**: Secure authentication using OpenID Connect (configured for GitLab)
- **Project Management**: View all projects and their branches
- **Screenshot Comparison**: Compare screenshots between branches (current vs default)
- **RESTful API**: Upload screenshots via API from CI/CD pipelines

## Setup

### Docker with Docker Compose (Recommended)

The easiest and most robust way to run the application is using Docker Compose with Gunicorn as the production web server.

#### Development Setup

For local development with hot-reloading:

```bash
# Use the development docker-compose configuration
docker-compose -f docker-compose.dev.yml up

# The application will be available at http://localhost:8000/
# Code changes will be reflected immediately (volume mounted)
```

#### Production Setup

For production deployment with proper security:

1. **Create environment configuration:**

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your configuration
nano .env  # or use your preferred editor
```

**IMPORTANT**: You must configure these required settings in `.env`:

- `SECRET_KEY`: Generate a secure random key (see below)
- `DEBUG`: Set to `False` for production
- `ALLOWED_HOSTS`: Set to your domain(s), e.g., `yourdomain.com,www.yourdomain.com`

**Generate a secure SECRET_KEY:**

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

2. **Start the application:**

```bash
# Build and start the services
docker-compose up -d

# Check logs
docker-compose logs -f web

# The application will be available at http://localhost:8000/
```

3. **Create a superuser (first time only):**

```bash
# Create an admin user to access Django admin
docker-compose exec web python manage.py createsuperuser
```

4. **Create API tokens for CI/CD:**

```bash
# Create a token for your CI/CD pipeline
docker-compose exec web python manage.py create_token <username>
```

**Environment Variables Reference:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | **Yes** | - | Django secret key. Must be unique and secret in production. |
| `DEBUG` | No | `False` | Enable debug mode. Always set to `False` in production. |
| `ALLOWED_HOSTS` | **Yes** | - | Comma-separated list of domains/IPs (e.g., `yourdomain.com,www.yourdomain.com`). |
| `OIDC_RP_CLIENT_ID` | No | - | OIDC client ID for web UI login (optional). |
| `OIDC_RP_CLIENT_SECRET` | No | - | OIDC client secret for web UI login (optional). |
| `OIDC_ALLOWED_PROJECTS` | No | - | Comma-separated list of allowed projects for JWT auth (optional). |

**Docker Compose Commands:**

```bash
# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f web

# Rebuild after code changes
docker-compose up -d --build

# Access shell in container
docker-compose exec web sh

# Run Django management commands
docker-compose exec web python manage.py <command>
```

**Data Persistence:**

Docker Compose creates named volumes for persistent data:
- `media_data`: Uploaded screenshot images
- `db_data`: SQLite database file

To backup your data:
```bash
# Backup database and media files
docker-compose exec web tar czf /tmp/backup.tar.gz /app/db.sqlite3 /app/media
docker cp $(docker-compose ps -q web):/tmp/backup.tar.gz ./backup.tar.gz
```

#### Using Pre-built Images

Instead of building locally, you can use pre-built images from GitHub Container Registry.

**For deployments without the source code:**

```bash
# Pull the latest image
docker pull ghcr.io/wipoulou/ui-story:latest

# Create a new directory for your deployment
mkdir ui-story-deploy && cd ui-story-deploy

# Download the example environment file
curl -O https://raw.githubusercontent.com/wipoulou/ui-story/main/.env.example

# Create .env file with your configuration
cp .env.example .env
nano .env

# Create docker-compose.yml using the pre-built image
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  web:
    image: ghcr.io/wipoulou/ui-story:latest
    ports:
      - "8000:8000"
    volumes:
      - media_data:/app/media
      - db_data:/app
    env_file:
      - .env
    restart: unless-stopped

volumes:
  media_data:
  db_data:
EOF

# Start the application
docker-compose up -d
```

**If you've already cloned the repository**, you can modify the existing `docker-compose.yml` to use the pre-built image instead of building locally. Just change the `build: .` line to `image: ghcr.io/wipoulou/ui-story:latest`.

### Local Installation

1. Install dependencies using uv:
```bash
uv sync
```

2. Configure environment variables for OIDC (optional):
```bash
export OIDC_RP_CLIENT_ID="your-client-id"
export OIDC_RP_CLIENT_SECRET="your-client-secret"
export OIDC_OP_AUTHORIZATION_ENDPOINT="https://gitlab.com/oauth/authorize"
export OIDC_OP_TOKEN_ENDPOINT="https://gitlab.com/oauth/token"
export OIDC_OP_USER_ENDPOINT="https://gitlab.com/oauth/userinfo"
export OIDC_OP_JWKS_ENDPOINT="https://gitlab.com/oauth/discovery/keys"
```

3. Run migrations:
```bash
uv run python manage.py migrate
```

4. Create a superuser:
```bash
uv run python manage.py createsuperuser
```

5. Run the development server:
```bash
uv run python manage.py runserver
```

## Usage

### Web Interface

- Visit `http://localhost:8000/` to view projects
- Click on a project to see its branches
- Click on a branch to see screenshots grouped by timestamp
- Click on a screenshot to compare it with the default branch

### API Upload

Upload screenshots via POST to `/api/upload/`:

**Using Token Authentication (recommended for CI/CD):**

First, create a token for your user in Django admin or via shell:
```python
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

user = User.objects.get(username='your-username')
token = Token.objects.create(user=user)
print(token.key)
```

Then use the token in API requests:
```bash
curl -X POST http://localhost:8000/api/upload/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -F "project=my-project" \
  -F "branch=feature-branch" \
  -F "page_name=homepage" \
  -F "viewport_size=1920x1080" \
  -F "image=@screenshot.png" \
  -F "pipeline_url=https://gitlab.com/my-project/-/pipelines/123" \
  -F "timestamp=2024-01-01T12:00:00Z" \
  -F 'metadata={"browser": "chrome", "version": "120"}'
```

**Using JWT from CI/CD (GitLab/GitHub):**

The application supports JWT authentication from multiple OIDC providers. GitLab and GitHub Actions are supported by default:

```bash
# GitLab CI/CD - use CI_JOB_JWT
curl -X POST http://localhost:8000/api/upload/ \
  -H "Authorization: Bearer $CI_JOB_JWT" \
  -F "project=my-project" \
  -F "branch=feature-branch" \
  -F "page_name=homepage" \
  -F "viewport_size=1920x1080" \
  -F "image=@screenshot.png" \
  -F "pipeline_url=$CI_PIPELINE_URL" \
  -F "timestamp=$(date -Iseconds)"

# GitHub Actions - use ACTIONS_ID_TOKEN_REQUEST_TOKEN
curl -X POST http://localhost:8000/api/upload/ \
  -H "Authorization: Bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
  -F "project=$GITHUB_REPOSITORY" \
  -F "branch=$GITHUB_REF_NAME" \
  -F "page_name=homepage" \
  -F "viewport_size=1920x1080" \
  -F "image=@screenshot.png" \
  -F "pipeline_url=$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID" \
  -F "timestamp=$(date -Iseconds)"
```

**Using Session Authentication:**
```bash
# Login first to establish session
curl -X POST http://localhost:8000/api/upload/ \
  -b cookies.txt -c cookies.txt \
  -F "project=my-project" \
  -F "branch=feature-branch" \
  -F "page_name=homepage" \
  -F "viewport_size=1920x1080" \
  -F "image=@screenshot.png" \
  -F "pipeline_url=https://gitlab.com/my-project/-/pipelines/123" \
  -F "timestamp=2024-01-01T12:00:00Z" \
  -F 'metadata={"browser": "chrome", "version": "120"}'
```

### GitLab CI/CD Integration

GitLab CI/CD can use JWT tokens for authentication. The JWT is automatically verified against GitLab's JWKS endpoint:

```yaml
screenshot_upload:
  stage: test
  id_tokens:
    CI_JOB_JWT:
      aud: https://your-ui-story-instance.com
  script:
    - |
      curl -X POST https://your-ui-story-instance.com/api/upload/ \
        -H "Authorization: Bearer $CI_JOB_JWT" \
        -F "project=$CI_PROJECT_PATH" \
        -F "branch=$CI_COMMIT_REF_NAME" \
        -F "page_name=homepage" \
        -F "viewport_size=1920x1080" \
        -F "image=@screenshot.png" \
        -F "pipeline_url=$CI_PIPELINE_URL" \
        -F "timestamp=$(date -Iseconds)"
```

### GitHub Actions Integration

GitHub Actions can also use JWT tokens:

```yaml
name: Upload Screenshots
on: [push]

jobs:
  upload:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - name: Get OIDC token
        id: oidc
        run: |
          TOKEN=$(curl -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
            "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=https://your-ui-story-instance.com" | jq -r .value)
          echo "token=$TOKEN" >> $GITHUB_OUTPUT
      - name: Upload screenshot
        run: |
          curl -X POST https://your-ui-story-instance.com/api/upload/ \
            -H "Authorization: Bearer ${{ steps.oidc.outputs.token }}" \
            -F "project=$GITHUB_REPOSITORY" \
            -F "branch=$GITHUB_REF_NAME" \
            -F "page_name=homepage" \
            -F "viewport_size=1920x1080" \
            -F "image=@screenshot.png" \
            -F "pipeline_url=$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID" \
            -F "timestamp=$(date -Iseconds)"
```

## Development

### Code Quality

Run ruff for linting and formatting:
```bash
uv run ruff check .
uv run ruff format .
```

### Running Tests

```bash
uv run python manage.py test
```

### Creating API Tokens

For CI/CD integration, create API tokens:

**Using management command (easiest):**
```bash
uv run python manage.py create_token <username>
```

**Via Django shell:**
```bash
uv run python manage.py shell
```

Then in the Python shell:
```python
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create or get user
user = User.objects.get(username='ci-user')

# Create token
token = Token.objects.create(user=user)
print(f"Token: {token.key}")
```

**Via Django admin:**
Visit http://localhost:8000/admin/authtoken/tokenproxy/

### Database

The default configuration uses SQLite. For production, configure PostgreSQL or MySQL in `config/settings.py`.

### Multi-Provider JWT Authentication

The application supports JWT authentication from multiple OIDC providers simultaneously:

**Built-in providers:**
- GitLab (https://gitlab.com)
- GitHub Actions (https://github.com)

**Adding custom providers:**

Set the `OIDC_PROVIDERS` environment variable or update `config/settings.py`:

```python
OIDC_PROVIDERS = {
    "https://custom-provider.com": {
        "jwks_endpoint": "https://custom-provider.com/.well-known/jwks.json",
    }
}
```

**Project authorization:**

Optionally restrict which projects can upload screenshots:

```bash
export OIDC_ALLOWED_PROJECTS="group/project1,group/project2,owner/repo"
```

### Environment Variables

Configure these environment variables for production:

- `SECRET_KEY`: Django secret key (required for production)
- `DEBUG`: Set to `False` for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `OIDC_ALLOWED_PROJECTS`: Comma-separated list of allowed projects for JWT auth (optional)
- `OIDC_RP_CLIENT_ID`: OIDC client ID (for web UI login)
- `OIDC_RP_CLIENT_SECRET`: OIDC client secret (for web UI login)
- `OIDC_OP_AUTHORIZATION_ENDPOINT`: OIDC authorization URL
- `OIDC_OP_TOKEN_ENDPOINT`: OIDC token URL
- `OIDC_OP_USER_ENDPOINT`: OIDC user info URL
- `OIDC_OP_JWKS_ENDPOINT`: OIDC JWKS URL

## Deployment

### Production Deployment with Docker Compose

The recommended way to deploy ui-story in production is using Docker Compose. See the [Docker with Docker Compose](#docker-with-docker-compose-recommended) section above for detailed setup instructions.

**Quick production deployment:**

1. Create `.env` file with your configuration (see `.env.example`)
2. Ensure `SECRET_KEY`, `DEBUG=False`, and `ALLOWED_HOSTS` are properly set
3. Run `docker-compose up -d`
4. Create superuser: `docker-compose exec web python manage.py createsuperuser`
5. Create API tokens: `docker-compose exec web python manage.py create_token <username>`

### Using Pre-built Docker Images

The repository includes a GitHub Action that automatically builds and pushes Docker images to GitHub Container Registry (ghcr.io) on every push to main and on tags.

**Pull and run the latest image:**
```bash
docker pull ghcr.io/wipoulou/ui-story:latest
docker run -p 8000:8000 \
  -e SECRET_KEY=your-production-secret \
  -e DEBUG=False \
  -e ALLOWED_HOSTS=yourdomain.com \
  -v /path/to/media:/app/media \
  ghcr.io/wipoulou/ui-story:latest
```

See the [Using Pre-built Images](#using-pre-built-images) section for docker-compose configuration with pre-built images.

### Reverse Proxy Setup (Recommended)

For production deployments, it's recommended to use a reverse proxy like Nginx or Traefik in front of the application:

**Example with Nginx:**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Optional: Serve media files directly through Nginx for better performance
    # Update the path to match your Docker volume mount or host directory
    # location /media/ {
    #     alias /var/lib/docker/volumes/ui-story_media_data/_data/;
    # }

    client_max_body_size 100M;  # Allow large screenshot uploads
}
```

**Example with Traefik and Docker Compose:**

```yaml
version: '3.8'

services:
  web:
    image: ghcr.io/wipoulou/ui-story:latest
    volumes:
      - media_data:/app/media
      - db_data:/app
    env_file:
      - .env
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ui-story.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.ui-story.entrypoints=websecure"
      - "traefik.http.routers.ui-story.tls.certresolver=letsencrypt"
      - "traefik.http.services.ui-story.loadbalancer.server.port=8000"

  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=your-email@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt_data:/letsencrypt
    restart: unless-stopped

volumes:
  media_data:
  db_data:
  letsencrypt_data:
```

### Production Database

While SQLite is suitable for small to medium deployments, for larger production deployments consider using PostgreSQL or MySQL. Update your `.env` file and modify `config/settings.py` accordingly.

### GitHub Actions

The `.github/workflows/docker-build.yml` workflow:
- Builds Docker images on push to main and on tags
- Pushes images to GitHub Container Registry
- Tags images with branch name, git SHA, and semantic versions
- Uses layer caching for faster builds

## Models

### Project
- `name`: Unique project name
- `default_branch`: Name of the default branch (e.g., "main")

### Branch
- `project`: Foreign key to Project
- `name`: Branch name

### Screenshot
- `project`: Foreign key to Project
- `branch`: Foreign key to Branch
- `page_name`: Name of the page/component
- `viewport_size`: Viewport dimensions (e.g., "1920x1080")
- `image`: Uploaded screenshot image
- `pipeline_url`: URL to CI/CD pipeline (optional)
- `metadata`: JSON field for additional metadata
- `timestamp`: When the screenshot was taken
