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

Add to your `.gitlab-ci.yml`:

```yaml
screenshot_upload:
  stage: test
  before_script:
    # Create a token for API access (do this once in Django admin and store in CI/CD variables)
    - export UI_STORY_TOKEN=$UI_STORY_API_TOKEN
  script:
    - # Run your UI tests and capture screenshots
    - |
      curl -X POST https://your-ui-story-instance.com/api/upload/ \
        -H "Authorization: Token $UI_STORY_TOKEN" \
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

### Environment Variables

Configure these environment variables for production:

- `SECRET_KEY`: Django secret key (required for production)
- `DEBUG`: Set to `False` for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `OIDC_RP_CLIENT_ID`: OIDC client ID
- `OIDC_RP_CLIENT_SECRET`: OIDC client secret
- `OIDC_OP_AUTHORIZATION_ENDPOINT`: OIDC authorization URL
- `OIDC_OP_TOKEN_ENDPOINT`: OIDC token URL
- `OIDC_OP_USER_ENDPOINT`: OIDC user info URL
- `OIDC_OP_JWKS_ENDPOINT`: OIDC JWKS URL

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
