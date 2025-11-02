# 🏦 FinRack - AI-Powered Financial Platform

Enterprise-grade financial management platform with 7 autonomous AI agents.

## 🚀 Features

- **Multi-Agent AI System**: 7 specialized AI agents for comprehensive financial management
- **Bank Integration**: Connect 11,000+ banks via Plaid
- **Smart Budgeting**: AI-powered budget creation and monitoring
- **Fraud Detection**: Real-time anomaly detection
- **Investment Tracking**: Portfolio analysis and recommendations
- **Goal Planning**: Intelligent financial goal tracking
- **Receipt OCR**: Automatic receipt scanning and categorization

## 🏗️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL 16 + TimescaleDB + pgvector
- **AI/ML**: LangChain, LangGraph, CrewAI
- **LLMs**: Ollama (local), Groq, Claude
- **Cache**: Redis 7.2
- **Queue**: RabbitMQ + Celery

### Frontend
- **Framework**: Next.js 15 (React 19)
- **Language**: TypeScript
- **UI**: shadcn/ui + TailwindCSS
- **State**: Zustand
- **Data**: React Query

## 📦 Installation

### Prerequisites
- Docker Desktop
- Python 3.12+
- Node.js 18+
- Poetry
- pnpm

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/Om7035/FinRack.git
cd FinRack/finrack
```

2. **Setup environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Setup backend**
```bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

5. **Setup frontend**
```bash
cd frontend
pnpm install
pnpm dev
```

6. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🤖 AI Agents

1. **Budget Guardian** - Autonomous budget management
2. **Fraud Sentinel** - Real-time fraud detection
3. **Investment Advisor** - Portfolio optimization
4. **Bill Optimizer** - Subscription tracking
5. **Tax Strategist** - Tax optimization
6. **Wealth Planner** - Goal-based planning
7. **Finance Concierge** - Natural language interface

## 📝 Environment Variables

See `.env.example` for required configuration.

## 🧪 Testing

```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests
cd frontend
pnpm test
```

## 📖 Documentation

- [Build Guide](../WINDSURF_BUILD_GUIDE.md)
- [API Documentation](http://localhost:8000/docs)
- [User Guide](../YOUR_ACTION_GUIDE.md)

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines.

## 📄 License

MIT License

## 🔗 Links

- [GitHub](https://github.com/Om7035/FinRack)
- [Documentation](../WINDSURF_BUILD_GUIDE.md)

---

Built with ❤️ using Windsurf AI
