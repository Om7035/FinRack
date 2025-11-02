# 🏦 FinRack - AI-Powered Financial Platform

Production-grade financial management platform with 7 autonomous AI agents.

## 🚀 Features

- **Multi-Agent AI System**: 7 specialized agents for comprehensive financial management
- **Bank Integration**: Connect 11,000+ banks via Plaid
- **Smart Budgeting**: AI-powered budget recommendations
- **Fraud Detection**: Real-time anomaly detection
- **Investment Tracking**: Portfolio analysis and recommendations
- **Goal Planning**: Intelligent financial goal tracking
- **Natural Language Interface**: Chat with your finances

## 🏗️ Tech Stack

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL + pgvector + TimescaleDB
- LangChain, LangGraph, CrewAI
- Redis, RabbitMQ, Celery

### Frontend
- Next.js 15
- React 19
- TypeScript
- shadcn/ui + TailwindCSS
- Zustand, React Query

### AI/ML
- Ollama (Local LLMs)
- Groq API
- Anthropic Claude
- XGBoost, Prophet

## 📦 Quick Start

### Prerequisites
- Docker Desktop
- Python 3.12+
- Node.js 18+
- Poetry
- pnpm

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Om7035/FinRack.git
cd FinRack/finrack
```

2. **Start Docker services**
```bash
docker-compose up -d
```

3. **Setup Backend**
```bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

4. **Setup Frontend**
```bash
cd frontend
pnpm install
pnpm dev
```

5. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

## 🔐 Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/finrack

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-secret-key

# Plaid
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox

# LLM Providers
GROQ_API_KEY=your_groq_api_key
ANTHROPIC_API_KEY=your_anthropic_key

# Notifications
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
SENDGRID_API_KEY=your_sendgrid_key
```

## 📚 Documentation

- [Build Guide](../WINDSURF_BUILD_GUIDE.md)
- [User Action Guide](../YOUR_ACTION_GUIDE.md)
- [Command Reference](../COMMAND_REFERENCE.md)
- [Windsurf Prompts](../WINDSURF_PROMPTS.md)

## 🤖 AI Agents

1. **Budget Guardian** - Autonomous budget management
2. **Fraud Sentinel** - Real-time fraud detection
3. **Investment Advisor** - Portfolio optimization
4. **Bill Optimizer** - Subscription management
5. **Tax Strategist** - Tax optimization
6. **Wealth Planner** - Goal-based planning
7. **Finance Concierge** - Natural language interface

## 🧪 Testing

```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests
cd frontend
pnpm test

# E2E tests
pnpm test:e2e
```

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📧 Contact

- GitHub: [@Om7035](https://github.com/Om7035)
- Repository: [FinRack](https://github.com/Om7035/FinRack)

---

**Built with ❤️ using Windsurf AI IDE**
