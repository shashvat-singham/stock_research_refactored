# System Architecture - Stock Research Chatbot

This document provides a detailed overview of the system architecture, component interactions, and data flows for the Stock Research Chatbot. It is intended for developers, architects, and senior managers who need to understand the system\'s design and inner workings.

## 1. High-Level Architecture

The system is designed as a modern, decoupled web application with a clear separation between the frontend and backend. It follows a classic **three-tier architecture**:

1.  **Presentation Tier (Frontend)**: A React-based single-page application (SPA) that provides the user interface.
2.  **Application Tier (Backend)**: A FastAPI-based application that houses the business logic, multi-agent system, and external service integrations.
3.  **Data Tier (External Services)**: External APIs like Yahoo Finance and Google Gemini that provide the raw data and AI capabilities.

### Architecture Diagram

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

## 2. Component Breakdown

### 2.1. Frontend Components

The frontend is a React application built with Vite. It consists of the following key components:

| Component | File Path | Responsibility |
|-----------|-----------|----------------|
| **App** | `frontend/stock-research-ui/src/App.jsx` | Main application component, handles user input and displays results |
| **StreamingLogPanel** | `frontend/stock-research-ui/src/components/StreamingLogPanel.jsx` | Displays real-time log messages from the backend |
| **LogEntry** | `frontend/stock-research-ui/src/components/LogEntry.jsx` | Renders individual log entries with appropriate styling |
| **useWebSocketLogs** | `frontend/stock-research-ui/src/hooks/useWebSocketLogs.js` | Custom React hook for managing WebSocket connections |

### 2.2. Backend Components

The backend is a FastAPI application with a modular structure:

| Layer | Directory | Key Files | Responsibility |
|-------|-----------|-----------|----------------|
| **API Layer** | `backend/app/` | `main.py`, `api.py`, `websocket.py`, `models.py` | Handles HTTP requests, WebSocket connections, and data validation |
| **Service Layer** | `backend/services/` | `conversation_manager.py`, `gemini_service.py`, `log_broadcaster.py`, `smart_correction_service.py`, `ticker_mapper.py` | Contains business logic and external service integrations |
| **Agent Layer** | `backend/agents/` | `orchestrator.py`, `news_agent.py`, `price_agent.py`, `synthesis_agent.py` | Implements the multi-agent analysis workflow using LangGraph |
| **Tool Layer** | `backend/tools/` | `yahoo_finance_tool.py`, `web_search_tool.py`, `sec_edgar_tool.py` | Wraps external APIs into reusable tools |
| **Configuration** | `backend/config/` | `settings.py` | Manages environment variables and application settings |

## 3. Data Flow

### 3.1. Standard Analysis Flow

This is the typical flow when a user requests an analysis for a valid ticker:

1. **User Input**: User enters a query in the frontend (e.g., "Analyze Apple stock")
2. **Request Generation**: Frontend generates a unique `request_id` and sends it with the query to `/api/v1/analyze`
3. **WebSocket Connection**: Frontend immediately opens a WebSocket connection to `/ws/{request_id}`
4. **API Handler**: The `analyze_stock` function in `backend/app/api.py` receives the request
5. **Ticker Extraction**: The `TickerMapper` service extracts ticker symbols from the query
6. **Orchestrator Invocation**: The `Orchestrator` is invoked with the query and `request_id`
7. **LangGraph Execution**: The LangGraph workflow executes the following nodes:
   - **extract_tickers_node**: Validates and deduplicates tickers
   - **analyze_ticker_node**: Analyzes each ticker (can run in parallel)
8. **Real-Time Logging**: As the orchestrator runs, it calls methods on the `LogBroadcaster`:
   - `LogBroadcaster.fetching_news(ticker)` → `ConnectionManager.broadcast_to_request(request_id, message)` → WebSocket sends JSON to frontend
9. **Tool Invocation**: The orchestrator calls tools like `YahooFinanceTool.get_news()` and `GeminiService.summarize_news()`
10. **Result Compilation**: The orchestrator compiles the final `TickerInsight` objects
11. **Response**: The API returns the insights to the frontend
12. **Display**: Frontend displays the analysis results

### 3.2. Smart Correction Flow

When the user provides an ambiguous or misspelled company name:

1. **Ticker Extraction Fails**: The `TickerMapper` cannot resolve the company name
2. **Smart Correction**: The `SmartCorrectionService` uses Gemini to suggest a correction
3. **Conversation Creation**: A `ConversationManager` creates a new conversation with a unique ID
4. **Confirmation Prompt**: The API returns `needs_confirmation: true` with the suggestion
5. **User Confirmation**: Frontend displays a confirmation dialog
6. **Confirmation Response**: User clicks "Yes" or "No", frontend sends the response with the `conversation_id`
7. **Conversation Retrieval**: The API retrieves the conversation and extracts the confirmed ticker
8. **Standard Flow**: The analysis proceeds with the confirmed ticker

## 4. WebSocket Communication

Real-time logging is a critical feature of the system. It is handled by the `LogBroadcaster` service and the `ConnectionManager`.

### 4.1. Connection Management

The `ConnectionManager` (in `backend/app/websocket.py`) is a singleton that maintains a dictionary of active WebSocket connections:

```python
# backend/app/websocket.py: lines 15-17
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
```

When a client connects to `/ws/{request_id}`, the connection is stored:

```python
# backend/app/websocket.py: lines 23-25
async def connect(self, websocket: WebSocket, request_id: str):
    await websocket.accept()
    self.active_connections[request_id] = websocket
```

### 4.2. Log Broadcasting

The `LogBroadcaster` (in `backend/services/log_broadcaster.py`) provides a high-level API for sending log messages. It is initialized with a `request_id` and uses the `ConnectionManager` to send messages:

```python
# backend/services/log_broadcaster.py: lines 30-38
async def _broadcast(self, type: str, message: str, agent: str = None, details: dict = None):
    log_event = {
        "type": type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": message,
        "agent": agent,
        "details": details or {}
    }
    connection_manager = get_connection_manager()
    await connection_manager.broadcast_to_request(self.request_id, log_event)
```

### 4.3. Frontend WebSocket Hook

The `useWebSocketLogs` hook (in `frontend/stock-research-ui/src/hooks/useWebSocketLogs.js`) manages the WebSocket connection on the frontend:

```javascript
// frontend/stock-research-ui/src/hooks/useWebSocketLogs.js: lines 32-33
const wsUrl = `ws://localhost:8000/ws/${requestId}`
const ws = new WebSocket(wsUrl)
```

When a message is received, it is parsed and added to the state:

```javascript
// frontend/stock-research-ui/src/hooks/useWebSocketLogs.js: lines 42-52
ws.onmessage = (event) => {
  try {
    const logEvent = JSON.parse(event.data)
    const logWithId = {
      ...logEvent,
      id: `${Date.now()}-${Math.random()}`
    }
    setLogs((prevLogs) => [...prevLogs, logWithId])
  } catch (err) {
    console.error('Error parsing log message:', err)
  }
}
```

## 5. LangGraph Workflow

The `Orchestrator` uses LangGraph to define a state machine for the analysis workflow. This provides several benefits:

- **Modularity**: Each step is a separate node, making the code easier to understand and maintain
- **Flexibility**: Edges can be conditional, allowing for dynamic workflows
- **Observability**: The state is explicitly defined and can be logged or inspected at any point

### 5.1. State Definition

The `OrchestratorState` is a TypedDict that defines all the data that flows through the workflow:

```python
# backend/agents/orchestrator.py: lines 31-50
class OrchestratorState(TypedDict):
    query: str
    tickers: List[str]
    unresolved_names: List[str]
    confirmed_tickers: Optional[List[str]]
    max_iterations: int
    timeout_seconds: int
    request_id: str
    log_broadcaster: Any
    insights: List[TickerInsight]
    errors: List[str]
    start_time: float
    current_ticker: str
    current_ticker_data: Dict[str, Any]
```

### 5.2. Workflow Graph

The workflow is built in the `_build_workflow` method:

```python
# backend/agents/orchestrator.py: lines 74-104
def _build_workflow(self) -> CompiledStateGraph:
    workflow = StateGraph(OrchestratorState)
    
    # Define nodes
    workflow.add_node("extract_tickers", extract_tickers_node)
    workflow.add_node("analyze_ticker", analyze_ticker_node)
    
    # Define edges
    workflow.set_entry_point("extract_tickers")
    workflow.add_conditional_edges(
        "extract_tickers",
        should_continue_analysis,
        {"continue": "analyze_ticker", "end": END}
    )
    workflow.add_edge("analyze_ticker", END)
    
    return workflow.compile()
```

This creates a simple linear workflow with a conditional branch:

```
[START] → extract_tickers → [should_continue_analysis?]
                                  ↓ (continue)    ↓ (end)
                            analyze_ticker      [END]
                                  ↓
                                [END]
```

### 5.3. Node Execution

Each node is an async function that receives the current state and returns the updated state:

```python
# backend/agents/orchestrator.py: lines 106-143
async def analyze_ticker_node(state: OrchestratorState) -> OrchestratorState:
    ticker = state["current_ticker"]
    
    # Step 1: Fetch stock info
    if state.get("log_broadcaster"):
        await state["log_broadcaster"].fetching_company_info(ticker)
    
    stock_info = self.yahoo_tool.get_stock_info(ticker)
    
    # Step 2: Fetch news
    if state.get("log_broadcaster"):
        await state["log_broadcaster"].fetching_news(ticker, company_name)
    
    news_articles = self.yahoo_tool.get_news(ticker, limit=10)
    
    # ... more steps ...
    
    return state
```

## 6. Key Design Decisions

### 6.1. Why LangGraph?

LangGraph provides a declarative way to define complex, multi-step workflows. It is particularly well-suited for agent-based systems where the flow can be dynamic and conditional. The explicit state management makes it easy to debug and extend the system.

### 6.2. Why WebSocket for Logging?

WebSocket provides a persistent, bidirectional connection that is ideal for real-time updates. Unlike HTTP polling, WebSocket is efficient and provides instant feedback to the user. The `request_id` based routing ensures that each user only receives logs for their own analysis.

### 6.3. Why Separate Services?

The service layer decouples the business logic from the API and agent layers. This makes the code more testable, reusable, and maintainable. For example, the `GeminiService` can be used by any agent without needing to know the details of the API.

### 6.4. Why Smart Correction?

The smart correction feature improves the user experience by handling common typos and ambiguous company names. It uses Gemini\'s language understanding capabilities to provide intelligent suggestions, reducing user frustration and improving the accuracy of the analysis.

## 7. Scalability Considerations

While the current implementation is designed for a single-server deployment, the architecture can be scaled horizontally with some modifications:

- **Stateless API**: The API layer is already stateless, making it easy to run multiple instances behind a load balancer
- **WebSocket Scaling**: For WebSocket scaling, a message broker (like Redis Pub/Sub) can be used to broadcast messages across multiple server instances
- **Database**: Currently, conversations are stored in-memory. For production, a database (like PostgreSQL or MongoDB) should be used
- **Caching**: Ticker mappings and other frequently accessed data can be cached in Redis to reduce latency

## 8. Security Considerations

- **API Key Management**: The Gemini API key is stored in environment variables and never exposed to the frontend
- **CORS**: CORS is configured to allow requests only from specific origins (configurable via environment variables)
- **Input Validation**: All user inputs are validated using Pydantic models
- **Rate Limiting**: For production, rate limiting should be implemented to prevent abuse
- **WebSocket Authentication**: Currently, WebSocket connections are not authenticated. For production, a token-based authentication system should be implemented

## Conclusion

The Stock Research Chatbot is a well-architected, modular system that leverages modern technologies like LangGraph, FastAPI, and React to provide a seamless, real-time stock analysis experience. The clear separation of concerns, explicit state management, and real-time logging make it easy to understand, maintain, and extend.
