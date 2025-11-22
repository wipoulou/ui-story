# ui-story

A Django application for storing and comparing UI screenshots across different branches and projects. Supports OIDC authentication for secure uploads from GitLab CI/CD pipelines.

## Features

- **Screenshot Storage**: Upload screenshots with metadata including project, branch, datetime, pipeline URL, viewport size, and page name
- **OIDC Authentication**: Secure authentication using OpenID Connect (configured for GitLab)
- **Project Management**: View all projects and their branches
- **Screenshot Comparison**: Compare screenshots between branches (current vs default)
- **RESTful API**: Upload screenshots via API from CI/CD pipelines

## Setup

### Docker (Recommended)

The easiest way to run the application is using Docker:

```bash
# Build and run with docker-compose
docker-compose up

# Or build and run manually
docker build -t ui-story .
docker run -p 8000:8000 -e SECRET_KEY=your-secret-key ui-story
```

The application will be available at `http://localhost:8000/`

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

### Docker Image

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

**Using docker-compose in production:**
```yaml
version: '3.8'
services:
  web:
    image: ghcr.io/wipoulou/ui-story:latest
    ports:
      - "8000:8000"
    volumes:
      - media_data:/app/media
      - db_data:/app/db.sqlite3
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - OIDC_RP_CLIENT_ID=${OIDC_RP_CLIENT_ID}
      - OIDC_RP_CLIENT_SECRET=${OIDC_RP_CLIENT_SECRET}
volumes:
  media_data:
  db_data:
```

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
