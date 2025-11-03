# FinRack API and Environment Variables Reference

This comprehensive guide explains all environment variables required for setting up FinRack. Follow this guide to properly configure your `.env` file for both development and production environments.

## Quick Start

First, copy the example environment file:

```bash
cp .env.example .env
```

Then update the required variables as described in the sections below.

## Required Environment Variables

These variables must be configured for the application to function properly.

### Database Configuration

**DATABASE_URL** and **DATABASE_URL_SYNC**
- **Purpose**: PostgreSQL connection strings for async and sync database operations
- **Default (Docker)**: 
  - `postgresql+asyncpg://postgres:postgres@localhost:5432/finrack` (async)
  - `postgresql://postgres:postgres@localhost:5432/finrack` (sync)
- **When to Change**: Only if using a custom database setup outside of Docker
- **Format**: `postgresql[+driver]://user:password@host:port/database`

**REDIS_URL**
- **Purpose**: Redis connection string for caching and session storage
- **Default (Docker)**: `redis://localhost:6379/0`
- **When to Change**: Only if using a custom Redis setup outside of Docker

**RABBITMQ_URL**
- **Purpose**: RabbitMQ URL for Celery task queue processing
- **Default (Docker)**: `amqp://guest:guest@localhost:5672/`
- **When to Change**: Only if using a custom RabbitMQ setup outside of Docker

### Authentication & Security

**JWT_SECRET**
- **Purpose**: Secret key for signing JWT tokens (critical for security)
- **Generation**: Create a strong random secret
  - PowerShell: `[Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))`
- **Requirements**: Minimum 32 characters, should be unique and secret
- **Warning**: Never commit this value to version control

**JWT_ALGORITHM**
- **Purpose**: Algorithm used for JWT token signing
- **Default**: `HS256` (recommended)
- **When to Change**: Only for advanced security requirements

**JWT_ACCESS_TOKEN_EXPIRE_MINUTES**
- **Purpose**: Duration before access tokens expire
- **Default**: `30` minutes
- **When to Change**: Adjust based on security requirements

**JWT_REFRESH_TOKEN_EXPIRE_DAYS**
- **Purpose**: Duration before refresh tokens expire
- **Default**: `7` days
- **When to Change**: Adjust based on security requirements

### CORS Configuration

**CORS_ORIGINS**
- **Purpose**: Comma-separated list of allowed origins for frontend requests
- **Development Default**: `http://localhost:3000,http://127.0.0.1:3000`
- **Production Example**: `https://yourdomain.com,https://www.yourdomain.com`
- **Warning**: Never use wildcard (*) in production

## Banking Integration (Required for Core Functionality)

### Plaid API Keys

**PLAID_CLIENT_ID**, **PLAID_SECRET**, **PLAID_ENV**
- **Purpose**: API keys for connecting to bank accounts via Plaid
- **Where to Get**:
  1. Sign up at [Plaid.com](https://plaid.com/)
  2. Navigate to Dashboard → Team Settings → Keys
  3. Set `PLAID_ENV=sandbox` for development
- **Requirements**: All three values must be provided for banking features to work
- **Warning**: Use `PLAID_ENV=sandbox` for development and `PLAID_ENV=production` for production

## AI/LLM Providers (At Least One Required)

Choose at least one LLM provider for AI agent functionality.

### Groq (Recommended - Fast Inference)

**GROQ_API_KEY**
- **Purpose**: API key for Groq's fast LLM inference
- **Where to Get**: [Groq Console](https://console.groq.com/) → API Keys
- **Requirements**: Required for AI agents if using Groq
- **Note**: Free tier available with rate limits

### Anthropic Claude (Optional)

**ANTHROPIC_API_KEY**
- **Purpose**: API key for Anthropic's Claude models
- **Where to Get**: [Anthropic Console](https://console.anthropic.com/) → API Keys
- **Requirements**: Optional but recommended for advanced AI features
- **Cost**: Paid service with usage-based pricing

### OpenRouter (Optional Fallback)

**OPENROUTER_API_KEY**
- **Purpose**: API key for OpenRouter (routes to multiple LLM providers)
- **Where to Get**: [OpenRouter Dashboard](https://openrouter.ai/) → API Keys
- **Requirements**: Optional fallback provider
- **Cost**: Paid service with usage-based pricing

### Ollama (Local Models - Optional)

**OLLAMA_BASE_URL**
- **Purpose**: Base URL for locally hosted Ollama models
- **Default**: `http://localhost:11434`
- **Installation**: 
  - Windows: `winget install Ollama.Ollama`
  - Run: `ollama serve`
- **Requirements**: Optional for local development without API costs
- **Note**: Requires downloading models separately (e.g., `ollama pull llama2`)

## Storage Configuration (Required for Receipt Processing)

### MinIO (S3-Compatible Storage)

**MINIO_ENDPOINT**
- **Purpose**: MinIO endpoint host and port
- **Default (Docker)**: `localhost:9000`
- **When to Change**: Only for custom MinIO deployments

**MINIO_ACCESS_KEY**, **MINIO_SECRET_KEY**
- **Purpose**: Credentials for accessing MinIO storage
- **Default (Docker)**: `minioadmin` / `minioadmin`
- **Security**: Change in production environments

**MINIO_BUCKET**
- **Purpose**: Bucket name for storing receipt images
- **Default**: `finrack-receipts`
- **Note**: Automatically created on first upload

**MINIO_SECURE**
- **Purpose**: Enable HTTPS for MinIO connections
- **Default**: `False` (for local development)
- **Production**: Set to `True` with valid SSL certificates

## Messaging Services (Optional but Recommended)

### Twilio (SMS Notifications)

**TWILIO_ACCOUNT_SID**, **TWILIO_AUTH_TOKEN**, **TWILIO_PHONE_NUMBER**
- **Purpose**: Credentials for sending SMS notifications
- **Where to Get**:
  1. Sign up at [Twilio.com](https://www.twilio.com/)
  2. Console → Account → Keys & Credentials
  3. Purchase a phone number for sending SMS
- **Requirements**: All three values required for SMS features
- **Cost**: Paid service with usage-based pricing

### SendGrid (Email Notifications)

**SENDGRID_API_KEY**, **SENDGRID_FROM_EMAIL**
- **Purpose**: Credentials for sending email notifications
- **Where to Get**:
  1. Sign up at [SendGrid.com](https://sendgrid.com/)
  2. Dashboard → API Keys → Create API Key
  3. Set up a verified sender/domain
- **Requirements**: Both values required for email features
- **Cost**: Free tier available with daily limits

## AWS Services (Optional)

### AWS Credentials (for Textract OCR or S3)

**AWS_ACCESS_KEY_ID**, **AWS_SECRET_ACCESS_KEY**, **AWS_REGION**
- **Purpose**: Credentials for AWS services (Textract OCR or S3 storage)
- **Where to Get**:
  1. AWS Console → IAM → Create user → Access keys
  2. Attach appropriate policies (TextractFullAccess or S3FullAccess)
- **Requirements**: All three values required for AWS features
- **Cost**: Paid service with usage-based pricing
- **Note**: Optional if using MinIO for storage and local OCR

## Application Configuration

**APP_NAME**
- **Purpose**: Application name identifier
- **Default**: `FinRack`

**APP_VERSION**
- **Purpose**: Current application version
- **Default**: `0.1.0`

**DEBUG**
- **Purpose**: Enable detailed logging and error messages
- **Development**: `True`
- **Production**: `False` (for security)

**LOG_LEVEL**
- **Purpose**: Verbosity of application logs
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Default**: `INFO`

## Additional Security (Optional)

**ENCRYPTION_KEY**
- **Purpose**: Application-level encryption key for sensitive data
- **Generation**: Same method as JWT_SECRET
- **Requirements**: 32-character minimum
- **Note**: Optional but recommended for enhanced security

## Frontend Configuration

**NEXT_PUBLIC_API_URL**
- **Purpose**: Base URL for backend API calls from the frontend
- **Development**: `http://localhost:8000`
- **Production**: `https://your-api-domain.com`
- **Location**: Set in `frontend/.env.local` or `frontend/.env`

## Setup Checklist

1. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

2. **Configure required services**
   - Database/Redis/RabbitMQ (keep defaults if using docker-compose)
   - Generate secure JWT_SECRET
   - Set up Plaid integration (PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV=sandbox)

3. **Choose AI provider(s)**
   - Option A: Get GROQ_API_KEY (recommended for speed)
   - Option B: Get ANTHROPIC_API_KEY (for advanced features)
   - Option C: Set up Ollama locally (free option)

4. **Configure frontend**
   ```bash
   cd frontend
   # Create .env.local
   # Add: NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

5. **Start infrastructure services**
   ```powershell
   docker-compose up -d
   ```

6. **Run backend**
   ```powershell
   cd backend
   poetry install
   poetry run alembic upgrade head
   poetry run uvicorn app.main:app --reload
   ```

7. **Run frontend**
   ```powershell
   cd frontend
   pnpm install --no-frozen-lockfile
   pnpm dev
   ```

## Service Provider Links

- [Plaid](https://plaid.com/) - Banking integration ([Docs](https://plaid.com/docs/))
- [Groq](https://groq.com/) - Fast LLM inference ([Console](https://console.groq.com/))
- [Anthropic](https://www.anthropic.com/) - Claude AI models ([Console](https://console.anthropic.com/))
- [OpenRouter](https://openrouter.ai/) - Multi-model routing
- [Twilio](https://www.twilio.com/) - SMS notifications
- [SendGrid](https://sendgrid.com/) - Email delivery
- [MinIO](https://min.io/) - S3-compatible storage
- [Ollama](https://ollama.com/) - Local LLM hosting

---
If you encounter issues, refer to `WINDSURF_BUILD_GUIDE.md` → "Prerequisites & Setup" and "User Action Checklist."
