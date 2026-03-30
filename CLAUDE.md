# M.I.E.Z — AI Assistant Guidelines

## Stack

- **Backend**: Django 6, Django REST Framework, SimpleJWT, PostgreSQL (via `dj-database-url`)
- **Frontend**: React + Vite, TypeScript
- **Auth**: Cookie-based JWT (`access_token` / `refresh_token` httpOnly cookies)
- **Infrastructure**: Docker Compose, EC2 (Ubuntu), GitHub Actions CI/CD

---

## Backend — Implementation Rules

### Use Django and DRF built-ins. Never reimplement what already exists.

| Need | Use this |
|------|----------|
| User model | Extend `AbstractUser` (already done in `api/models.py`) |
| Authentication | `CustomAuthentication` in `core/authenticate.py` (reads JWT from cookies) |
| Password hashing | `user.set_password()` — never hash manually |
| Permission checks | `permission_classes = [IsAuthenticated]` on views |
| Object lookup with 404 | `get_object_or_404(Model, ...)` |
| Pagination | Subclass `PageNumberPagination` (see `EmployeePagination` in `api/views.py`) |
| Serialization / validation | DRF `ModelSerializer` — use `is_valid(raise_exception=True)` |
| DB aggregations | `queryset.aggregate()` / `.annotate()` — not raw SQL or Python loops |
| Filtering querysets | ORM `.filter()` with `Q` objects — not manual list filtering |
| Choices fields | `models.TextChoices` inner class (see `User.Role`) |
| Slug generation | `models.SlugField` — auto-populate via `slugify()` in `save()` or serializer |

### Models

- All models live in `api/models.py`.
- `User` extends `AbstractUser` — never create a separate profile model. Add fields directly to `User`.
- `AUTH_USER_MODEL = 'api.User'` — always use `get_user_model()` in code that references the user model, not a direct import.
- Every new model needs a migration: run `python manage.py makemigrations` after any model change.
- Use `select_related()` for FK fields and `prefetch_related()` for M2M to avoid N+1 queries.

### Views

- Use `APIView` (DRF) for all API endpoints — not Django's raw `JsonResponse` views (the `is_even` view is a legacy exception).
- Role-based access: check `request.user.role` against `User.Role` choices — do not hardcode role strings.
- Return DRF `Response` objects, not raw `JsonResponse`, so content negotiation and status codes work correctly.

### URLs

- All API routes are prefixed `/api/` — register new routes in `api/urls.py`, not in `core/urls.py`.

---

## Backend — Testing Rules

- Use Django's `TestCase` (not plain `unittest.TestCase`) — it wraps each test in a transaction and rolls back automatically.
- Use `APIClient` from `rest_framework.test` for endpoint tests — not the raw Django test `Client`.
- **Never mock the database.** Tests run against a real SQLite DB (configured in CI via `DATABASE_URL=sqlite:///test.db`). Mocking the ORM hides real query bugs.
- Create test users with `User.objects.create_user(...)` — never `User.objects.create(...)` (skips password hashing).
- For authenticated endpoint tests, log in via the login endpoint and let the cookie be set, or force-authenticate with `client.force_authenticate(user=user)`.
- Test file location: `backend/api/tests/` as a package, or `backend/api/tests.py`. One file per domain area (e.g. `test_auth.py`, `test_employees.py`, `test_departments.py`).
- Each test method should test one behaviour. Name tests as `test_<action>_<expected_outcome>` (e.g. `test_login_with_invalid_password_returns_401`).
- Always test both the happy path and the main failure cases (missing fields, wrong role, unauthenticated).
- Run tests: `python manage.py test` from `backend/`.

---

## Deployment

- **Local dev**: `docker-compose.yaml` — includes live-reload volume mounts.
- **Production**: `docker-compose.prod.yml` — no volume mounts; `npm install` and pip packages come from the built image.
- After any model change, migrations must be run on the target environment — they are not automatic.
  - Locally: `docker exec miez-backend-1 python manage.py migrate`
  - EC2: `docker exec <backend_container_id> python manage.py migrate`
- The CI/CD pipeline (`deploy.yml`) runs migrations automatically on every deploy to `main`.
- Never commit `.env` — local `.env` and EC2 `.env` are managed separately.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Full Postgres URL (`postgresql://user:pass@host:port/db`) |
| `DJANGO_SECRET_KEY` | Django secret key — insecure default used locally only |
| `DEBUG` | `True` locally, `False` on EC2 |
| `POSTGRES_DB` | Database name (used by docker-compose) |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |
