# Stock Research Chatbot - Multi-Agent AI System

A professional-grade, real-time stock analysis platform powered by **LangGraph**, **Gemini 2.5 Flash**, and **Yahoo Finance**. This system employs a multi-agent architecture with intelligent ticker resolution, WebSocket-based streaming logs, and comprehensive investment analysis.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [WebSocket Streaming](#websocket-streaming)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The **Stock Research Chatbot** is an enterprise-ready AI system that performs comprehensive stock analysis by orchestrating multiple specialized agents. It combines real-time market data from Yahoo Finance with advanced AI reasoning from Google's Gemini 2.5 Flash to deliver actionable investment insights.

### What Makes This System Unique?

1. **Multi-Agent Architecture**: Specialized agents (News, Price, Synthesis) work collaboratively using LangGraph workflows
2. **Smart Ticker Resolution**: Gemini-powered intelligent company name correction and ticker mapping
3. **Real-Time Streaming**: WebSocket-based live progress updates with professional user-facing logs
4. **Confirmation Flow**: Interactive user confirmation for ambiguous ticker inputs
5. **Production-Ready**: Structured logging, error handling, CORS support, health checks, and Docker deployment

---

## Key Features

### 🤖 Multi-Agent System
- **News Agent**: Fetches and analyzes recent news articles for sentiment and market impact
- **Price Agent**: Analyzes technical indicators, support/resistance levels, and price trends
- **Synthesis Agent**: Combines insights to generate comprehensive investment recommendations

### 🧠 Intelligent Ticker Resolution
- Automatic company name to ticker symbol mapping
- Gemini-powered smart correction for misspelled company names
- Interactive confirmation flow for ambiguous inputs
- Confidence scoring (high/medium/low) for suggestions

### 📡 Real-Time Streaming Logs
- WebSocket-based live progress updates
- Professional user-facing log messages
- Agent activity tracking with timestamps
- Auto-reconnection with exponential backoff

### 📊 Comprehensive Analysis
- **Stance**: Buy, Sell, or Hold recommendation
- **Confidence Level**: High, Medium, or Low
- **Summary**: Executive summary of the investment thesis
- **Rationale**: Detailed reasoning behind the recommendation
- **Key Drivers**: Primary factors influencing the stock
- **Risks**: Potential downside factors
- **Catalysts**: Upcoming events or triggers
- **Sources**: News articles with URLs and timestamps

### 🔧 Production Features
- Structured JSON logging with `structlog`
- CORS middleware for cross-origin requests
- Health check endpoints
- Environment-based configuration
- Docker containerization
- Comprehensive error handling
- Request ID tracking

---

## System Architecture

The system follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   UI Layer   │  │  WebSocket   │  │  HTTP Client │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────┴────────────────────────────────────┐
│                  Backend (FastAPI + LangGraph)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Layer (FastAPI)                     │  │
│  │  • /api/v1/analyze  • /health  • /ws/{request_id}   │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────┴─────────────────────────────────┐  │
│  │          Service Layer                               │  │
│  │  • ConversationManager  • SmartCorrectionService     │  │
│  │  • LogBroadcaster       • TickerMapper               │  │
│  │  • GeminiService                                     │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────┴─────────────────────────────────┐  │
│  │          Agent Layer (LangGraph)                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │  │
│  │  │ Orchestrator │→ │  News Agent  │  │Price Agent│  │  │
│  │  └──────────────┘  └──────────────┘  └───────────┘  │  │
│  │         │                                             │  │
│  │         └──────────→ Synthesis Agent                 │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────┴─────────────────────────────────┐  │
│  │          Tool Layer                                  │  │
│  │  • YahooFinanceTool  • WebSearchTool                │  │
│  │  • SECEdgarTool                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│              External Services                              │
│  • Yahoo Finance API  • Google Gemini 2.5 Flash            │
│  • SEC EDGAR API                                            │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Frontend sends query to `/api/v1/analyze`
2. **Ticker Extraction** → TickerMapper resolves company names to ticker symbols
3. **Smart Correction** → If ambiguous, SmartCorrectionService suggests corrections
4. **Confirmation Flow** → User confirms or rejects suggestions
5. **LangGraph Workflow** → Orchestrator executes multi-agent analysis
6. **Real-Time Logs** → LogBroadcaster streams progress via WebSocket
7. **Analysis Result** → Comprehensive insights returned to frontend

For detailed architecture diagrams and component interactions, see [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.115.12
- **Workflow Engine**: LangGraph 0.2.65
- **AI Model**: Google Gemini 2.5 Flash (via `google-generativeai`)
- **Data Source**: Yahoo Finance (via `yfinance`)
- **Logging**: `structlog` for structured JSON logging
- **WebSocket**: FastAPI WebSocket support
- **Validation**: Pydantic models

### Frontend
- **Framework**: React 18.3.1
- **Build Tool**: Vite 6.0.11
- **UI Library**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS 3.4.17
- **Icons**: Lucide React
- **HTTP Client**: Fetch API
- **WebSocket**: Native WebSocket API

### DevOps
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest
- **Environment Management**: python-dotenv
- **API Testing**: Postman collections included

---

## Project Structure

```
stock-research-chatbot/
├── backend/                      # Backend application
│   ├── agents/                   # Agent implementations
│   │   ├── base_agent.py         # Base agent class
│   │   ├── orchestrator.py       # Main LangGraph orchestrator
│   │   ├── news_agent.py         # News analysis agent
│   │   ├── price_agent.py        # Price analysis agent
│   │   ├── synthesis_agent.py    # Synthesis agent
│   │   ├── earnings_agent.py     # Earnings analysis agent
│   │   ├── filings_agent.py      # SEC filings agent
│   │   ├── insider_agent.py      # Insider trading agent
│   │   └── patents_agent.py      # Patent analysis agent
│   ├── app/                      # FastAPI application
│   │   ├── main.py               # Application entry point
│   │   ├── api.py                # API route handlers
│   │   ├── models.py             # Pydantic models
│   │   └── websocket.py          # WebSocket connection manager
│   ├── config/                   # Configuration
│   │   └── settings.py           # Settings and environment variables
│   ├── services/                 # Business logic services
│   │   ├── conversation_manager.py    # Manages conversation state
│   │   ├── gemini_service.py          # Gemini API integration
│   │   ├── log_broadcaster.py         # WebSocket log streaming
│   │   ├── smart_correction_service.py # Ticker correction
│   │   └── ticker_mapper.py           # Company name to ticker mapping
│   ├── tools/                    # External API tools
│   │   ├── base_tool.py          # Base tool class
│   │   ├── yahoo_finance_tool.py # Yahoo Finance integration
│   │   ├── web_search_tool.py    # Web search tool
│   │   └── sec_edgar_tool.py     # SEC EDGAR integration
│   ├── utils/                    # Utility functions
│   │   ├── api_client.py         # HTTP client utilities
│   │   └── formatters.py         # Data formatting utilities
│   ├── tests/                    # Test suite
│   │   ├── test_agents.py        # Agent tests
│   │   ├── test_api.py           # API tests
│   │   └── test_smart_correction.py # Smart correction tests
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # Backend Docker configuration
├── frontend/                     # Frontend application
│   └── stock-research-ui/        # React application
│       ├── src/
│       │   ├── components/       # React components
│       │   │   ├── ui/           # shadcn/ui components
│       │   │   ├── LogEntry.jsx  # Log entry component
│       │   │   └── StreamingLogPanel.jsx # Log panel component
│       │   ├── hooks/            # Custom React hooks
│       │   │   └── useWebSocketLogs.js # WebSocket hook
│       │   ├── lib/              # Utility libraries
│       │   ├── App.jsx           # Main application component
│       │   └── main.jsx          # Application entry point
│       ├── package.json          # Node dependencies
│       └── vite.config.js        # Vite configuration
├── scripts/                      # Utility scripts
├── postman/                      # Postman API collections
├── .env.template                 # Environment variable template
├── docker-compose.yml            # Docker Compose configuration
├── pytest.ini                    # pytest configuration
├── README.md                     # This file
├── ARCHITECTURE.md               # Detailed architecture documentation
```

---

## Installation & Setup

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **npm** or **pnpm**: Latest version
- **Docker** (optional): For containerized deployment
- **Google Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd stock-research-chatbot
```

### Step 2: Configure Environment Variables

```bash
# Copy the template
cp .env.template .env

# Edit .env and add your Gemini API key
nano .env
```

**Required Environment Variables:**

```env
# Application Settings
APP_ENV=development
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# CORS Settings
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Step 3: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
python -m backend.app.main
```

The backend will start on `http://localhost:8000`.

### Step 4: Frontend Setup

```bash
# Navigate to frontend directory
cd frontend/stock-research-ui

# Install dependencies
npm install
# or
pnpm install

# Start the development server
npm run dev
# or
pnpm dev
```

The frontend will start on `http://localhost:5173`.

### Step 5: Verify Installation

1. Open `http://localhost:5173` in your browser
2. Enter a query like "Analyze Apple stock"
3. Verify that the analysis completes successfully

---

## Usage Guide

### Basic Query

```
Analyze Apple stock
```

### Multiple Tickers

```
Compare MSFT and GOOGL
```

### Company Names

```
What's the outlook for Tesla and Nvidia?
```

### Smart Correction Flow

If you enter a misspelled company name:

```
Analyze Microsft
```

The system will:
1. Detect the misspelling
2. Suggest "Microsoft (MSFT)" with confidence level
3. Ask for confirmation
4. Proceed with analysis upon confirmation

### Understanding Results

Each analysis includes:

- **Stance**: Buy/Sell/Hold recommendation
- **Confidence**: High/Medium/Low confidence level
- **Summary**: One-paragraph executive summary
- **Rationale**: Detailed reasoning
- **Key Drivers**: 3-5 primary factors
- **Risks**: Potential downside factors
- **Catalysts**: Upcoming events or triggers
- **Sources**: News articles with links
- **Agent Traces**: Detailed agent execution logs

---

## API Documentation

### Endpoints

#### `POST /api/v1/analyze`

Analyze one or more stocks.

**Request Body:**

```json
{
  "query": "Analyze Apple stock",
  "max_iterations": 3,
  "timeout_seconds": 60,
  "request_id": "req-1234567890-abcdef",
  "conversation_id": null,
  "confirmation_response": null
}
```

**Response (Success):**

```json
{
  "insights": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "stance": "buy",
      "confidence": "high",
      "summary": "Apple shows strong fundamentals...",
      "rationale": "Based on recent earnings...",
      "key_drivers": ["iPhone 15 sales", "Services growth"],
      "risks": ["Regulatory pressure", "Supply chain"],
      "catalysts": ["Q1 earnings", "Vision Pro launch"],
      "sources": [...],
      "agent_traces": [...]
    }
  ],
  "request_id": "req-1234567890-abcdef",
  "needs_confirmation": false
}
```

**Response (Needs Confirmation):**

```json
{
  "needs_confirmation": true,
  "confirmation_prompt": {
    "conversation_id": "conv-123",
    "message": "Did you mean Microsoft (MSFT)?",
    "suggestion": {
      "original_input": "Microsft",
      "corrected_name": "Microsoft Corporation",
      "ticker": "MSFT",
      "confidence": "high",
      "explanation": "Detected likely typo..."
    }
  }
}
```

#### `GET /health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": 1699564800.123,
  "service": "stock-research-chatbot"
}
```

#### `WebSocket /ws/{request_id}`

Real-time log streaming.

**Connection:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/req-1234567890-abcdef');
```

**Message Format:**

```json
{
  "type": "agent_start",
  "timestamp": "2024-11-16T10:30:00.123Z",
  "message": "Starting analysis for AAPL",
  "agent": "news",
  "details": {
    "ticker": "AAPL",
    "progress": 25
  }
}
```

---

## WebSocket Streaming

The system provides real-time progress updates via WebSocket. The frontend automatically connects when an analysis starts.

### Log Event Types

- `agent_start`: Agent begins execution
- `agent_complete`: Agent finishes execution
- `agent_progress`: Agent progress update
- `tool_call`: External API call
- `search_query`: Search operation
- `data_fetch`: Data retrieval
- `analysis`: Analysis in progress
- `thinking`: AI reasoning
- `error`: Error occurred
- `info`: General information

### Frontend Integration

```javascript
import { useWebSocketLogs } from './hooks/useWebSocketLogs';

const { logs, isConnected, error, clearLogs } = useWebSocketLogs(
  requestId,
  enabled
);
```

---

## Configuration

### Backend Configuration

Edit `backend/config/settings.py` or set environment variables:

```python
class Settings(BaseSettings):
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-exp"
    cors_origins: str = "http://localhost:5173"
```

### Frontend Configuration

Edit `frontend/stock-research-ui/src/App.jsx`:

```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Test Coverage

```bash
pytest tests/ --cov=backend --cov-report=html
```

### API Testing with Postman

Import the collection from `postman/` directory.

---

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Deployment

#### Backend

```bash
cd backend
gunicorn backend.app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### Frontend

```bash
cd frontend/stock-research-ui
npm run build
# Serve the dist/ folder with nginx or any static server
```

---

## Troubleshooting

### Common Issues

**Issue**: "No valid stock tickers found"
- **Solution**: Ensure you're using valid ticker symbols (e.g., AAPL, MSFT) or full company names

**Issue**: WebSocket connection fails
- **Solution**: Check that the backend is running and CORS is configured correctly

**Issue**: Gemini API errors
- **Solution**: Verify your API key is valid and has sufficient quota

**Issue**: Yahoo Finance data unavailable
- **Solution**: Some tickers may have limited data; try a different ticker

### Logs

Backend logs are in JSON format:

```bash
tail -f backend.log | jq
```

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) file for details.

---

## Support

For questions or issues:
- Open an issue on GitHub
- Contact: [your-email@example.com]

---

**Built with ❤️ using LangGraph, Gemini, and FastAPI**
