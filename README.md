# ui-story

A Django application for storing and comparing UI screenshots across different branches and projects. Supports OIDC authentication for secure uploads from GitLab CI/CD pipelines.

## Features

- **Screenshot Storage**: Upload screenshots with metadata including project, branch, datetime, pipeline URL, viewport size, and page name
- **OIDC Authentication**: Secure authentication using OpenID Connect (configured for GitLab)
- **Project Management**: View all projects and their branches
- **Screenshot Comparison**: Compare screenshots between branches (current vs default)
- **RESTful API**: Upload screenshots via API from CI/CD pipelines

## Setup

### Installation

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

```bash
curl -X POST http://localhost:8000/api/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
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

Add to your `.gitlab-ci.yml`:

```yaml
screenshot_upload:
  stage: test
  script:
    - # Run your UI tests and capture screenshots
    - |
      curl -X POST https://your-ui-story-instance.com/api/upload/ \
        -H "Authorization: Bearer $CI_JOB_TOKEN" \
        -F "project=$CI_PROJECT_NAME" \
        -F "branch=$CI_COMMIT_REF_NAME" \
        -F "page_name=homepage" \
        -F "viewport_size=1920x1080" \
        -F "image=@screenshot.png" \
        -F "pipeline_url=$CI_PIPELINE_URL" \
        -F "timestamp=$(date -Iseconds)"
```

## Development

### Code Quality

Run ruff for linting and formatting:
```bash
uv run ruff check .
uv run ruff format .
```

### Database

The default configuration uses SQLite. For production, configure PostgreSQL or MySQL in `config/settings.py`.

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
