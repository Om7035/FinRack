# API and .env Reference (Simple Guide)

Use this guide to fill your `.env` file quickly. Each section tells you: what it is, where to get the keys, and what to paste.

Tip: Copy `.env.example` to `.env` first.

```bash
cp .env.example .env
```

## Backend Core

- DATABASE_URL / DATABASE_URL_SYNC
  - What: PostgreSQL connection strings (async/sync)
  - Default for local Docker: `postgresql+asyncpg://postgres:postgres@localhost:5432/finrack` and `postgresql://postgres:postgres@localhost:5432/finrack`
  - Where: If using docker-compose from this repo, keep defaults. Otherwise set your DB host/user/pass.

- REDIS_URL
  - What: Redis connection string
  - Default local: `redis://localhost:6379/0`
  - Where: If using docker-compose, keep default.

- RABBITMQ_URL
  - What: RabbitMQ URL for Celery/queue
  - Default local: `amqp://guest:guest@localhost:5672/`
  - Where: If using docker-compose, keep default.

## Storage (Receipts via MinIO)

- MINIO_ENDPOINT
  - What: MinIO endpoint host:port
  - Default local: `localhost:9000`
  - Where: docker-compose MinIO service.

- MINIO_ACCESS_KEY / MINIO_SECRET_KEY
  - What: MinIO credentials
  - Default local: `minioadmin` / `minioadmin`
  - Where: docker-compose env, or update to your MinIO user.

- MINIO_BUCKET
  - What: Bucket for receipts
  - Default: `finrack-receipts` (auto-created on first upload)

- MINIO_SECURE
  - What: Use HTTPS to connect to MinIO
  - Local default: `False`

## Auth

- JWT_SECRET
  - What: Secret key for signing JWT tokens
  - Where: Generate securely
  - How: PowerShell: `[Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))`
  - Paste: Set `JWT_SECRET=your_generated_secret`

- JWT_ALGORITHM / JWT_ACCESS_TOKEN_EXPIRE_MINUTES / JWT_REFRESH_TOKEN_EXPIRE_DAYS
  - What: JWT settings (keep defaults unless you need changes)

## CORS

- CORS_ORIGINS
  - What: Comma-separated allowed origins for frontend
  - Local dev: `http://localhost:3000,http://127.0.0.1:3000`

## Banking (Plaid)

- PLAID_CLIENT_ID / PLAID_SECRET / PLAID_ENV
  - What: API keys to link bank accounts
  - Where to get:
    - Sign up: https://plaid.com/
    - Dashboard → Team Settings → Keys
    - Set `PLAID_ENV=sandbox` for development
  - Paste: `PLAID_CLIENT_ID=...`, `PLAID_SECRET=...`, `PLAID_ENV=sandbox`

## AI/LLM Providers

- GROQ_API_KEY
  - What: Fast LLM API key
  - Where: https://console.groq.com/ (API Keys)
  - Paste: `GROQ_API_KEY=...`

- ANTHROPIC_API_KEY (optional)
  - Where: https://console.anthropic.com/ (API Keys)

- OPENROUTER_API_KEY (optional)
  - Where: https://openrouter.ai/ (Dashboard → API Keys)

- OLLAMA_BASE_URL (optional local models)
  - What: Local LLM endpoint
  - Default: `http://localhost:11434`
  - Install: `winget install Ollama.Ollama`, then run `ollama serve`

## Messaging (Optional)

- TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_PHONE_NUMBER
  - What: SMS notifications
  - Where: https://www.twilio.com/ (Console → Account → Keys & Credentials; buy a phone number)

- SENDGRID_API_KEY / SENDGRID_FROM_EMAIL
  - What: Email notifications
  - Where: https://sendgrid.com/ (Dashboard → API Keys)
  - Recommended from email: a verified sender/domain

## AWS (Optional)

- AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION
  - What: Use if you switch OCR to AWS Textract or S3 storage
  - Where: AWS Console → IAM → Create user → Access keys
  - Region: e.g., `us-east-1`

## Security (Optional)

- ENCRYPTION_KEY
  - What: App-level encryption key if you choose to encrypt sensitive fields
  - How: Same generation method as `JWT_SECRET`

## Frontend

- NEXT_PUBLIC_API_URL
  - What: Base URL for the backend API used by the frontend
  - Local dev: `http://localhost:8000`
  - Paste in `frontend/.env.local` or `.env`: `NEXT_PUBLIC_API_URL=http://localhost:8000`

## Quick Setup Checklist

1) Copy example env
```bash
cp .env.example .env
```
2) Fill required keys:
- Database/Redis/RabbitMQ (keep defaults if using docker-compose)
- JWT_SECRET (generate new)
- Plaid: `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV=sandbox`
- GROQ_API_KEY (optional but recommended)
3) Frontend env
```bash
cd frontend
# create .env.local
# add: NEXT_PUBLIC_API_URL=http://localhost:8000
```
4) Start services
```powershell
docker-compose up -d
```
5) Run backend
```powershell
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```
6) Run frontend
```powershell
cd frontend
pnpm install --no-frozen-lockfile
pnpm dev
```

## Helpful Links
- Plaid: https://plaid.com/ (Docs: https://plaid.com/docs/)
- Groq: https://groq.com/ (Console: https://console.groq.com/)
- Anthropic: https://www.anthropic.com/ (Console: https://console.anthropic.com/)
- OpenRouter: https://openrouter.ai/
- Twilio: https://www.twilio.com/
- SendGrid: https://sendgrid.com/
- MinIO: https://min.io/
- Ollama: https://ollama.com/

---
If you get stuck, open `WINDSURF_BUILD_GUIDE.md` → “Prerequisites & Setup” and “User Action Checklist.”

