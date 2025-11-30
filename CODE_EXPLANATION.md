# Code Explanation 

This document provides a detailed, file-by-file explanation of the Stock Research Chatbot, designed to be presented to a senior manager. It highlights how different components connect, with a special focus on the backend, LangGraph orchestration, and WebSocket communication.

## 1. The Entry Point: Frontend Interaction

The user journey begins in the frontend React application.

### `frontend/stock-research-ui/src/App.jsx`

This is the main component of our user interface. When a user types a query and clicks "Analyze", the `handleAnalyze` function is triggered.

**Key Logic:**

1.  **State Management**: It manages the application\'s state, including the user\'s query, analysis results, and loading status.
2.  **Request ID Generation**: A unique `request_id` is created for each new analysis. This ID is crucial for tracking the request and linking it to the WebSocket stream.

    ```javascript
    // frontend/stock-research-ui/src/App.jsx: line 151
    const requestId = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    setCurrentRequestId(requestId)
    setEnableWebSocket(true)
    ```

3.  **API Call**: It sends the query and `request_id` to the backend\'s `/api/v1/analyze` endpoint.

    ```javascript
    // frontend/stock-research-ui/src/App.jsx: line 168
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    })
    ```

## 2. The Gateway: Backend API

The request from the frontend is received by our FastAPI backend.

### `backend/app/main.py`

This file defines the main FastAPI application, including middleware, startup/shutdown events, and our API endpoints.

-   The `@app.post("/api/v1/analyze")` endpoint is defined in `backend/app/api.py` and included here.
-   The `@app.websocket("/ws/{request_id}")` endpoint is the key to our real-time logging.

### `backend/app/api.py`

This is where the core analysis logic is initiated.

**Key Logic:**

1.  **Request Handling**: The `analyze_stock` function receives the `AnalysisRequest` from the frontend.
2.  **Orchestrator Invocation**: It creates an instance of the `Orchestrator` and invokes the LangGraph workflow.

    ```python
    # backend/app/api.py: line 101
    orchestrator = Orchestrator()
    result = await orchestrator.invoke(
        query=request.query,
        max_iterations=request.max_iterations,
        timeout_seconds=request.timeout_seconds,
        request_id=request.request_id,
        log_broadcaster=log_broadcaster,
        confirmed_tickers=confirmed_tickers
    )
    ```

## 3. The Conductor: LangGraph Orchestrator

The `Orchestrator` is the heart of our multi-agent system, managing the entire analysis process using a state machine built with LangGraph.

### `backend/agents/orchestrator.py`

**Key Logic:**

1.  **State Definition (`OrchestratorState`)**: This class defines the data that is passed between the nodes of our graph (the state).
2.  **Workflow Construction (`_build_workflow`)**: This method defines the nodes (steps) and edges (transitions) of our analysis graph.

    ```python
    # backend/agents/orchestrator.py: line 74
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

3.  **Node Execution**: Each node in the graph is a function that performs a specific task (e.g., `extract_tickers_node`, `analyze_ticker_node`).

## 4. The Announcer: WebSocket Log Broadcasting

As the `Orchestrator` works, it needs to provide real-time feedback to the user. This is where the `LogBroadcaster` and WebSocket system come into play.

### `backend/services/log_broadcaster.py`

This service provides a simple, high-level API for sending log messages. It is initialized in `api.py` and passed to the `Orchestrator`.

**Key Logic:**

-   It contains methods for specific events, like `fetching_news` or `analyzing_technicals`.
-   Each method constructs a JSON payload and calls `_broadcast`.

    ```python
    # backend/services/log_broadcaster.py: line 105
    async def fetching_news(self, ticker: str, company_name: str):
        await self._broadcast(
            type="agent_progress",
            message=f"Gathering latest news for {company_name} ({ticker})...",
            agent="news",
            details={"ticker": ticker, "progress": 25}
        )
    ```

### How it Connects to the WebSocket:

The `LogBroadcaster` uses the `ConnectionManager` to send the message to the correct user.

### `backend/app/websocket.py`

This file contains the `ConnectionManager`, a singleton class that keeps track of all active WebSocket connections.

**Key Logic:**

1.  **`connect`**: When a user connects to `/ws/{request_id}`, the `ConnectionManager` stores the WebSocket object in a dictionary, using the `request_id` as the key.

    ```python
    # backend/app/websocket.py: line 23
    async def connect(self, websocket: WebSocket, request_id: str):
        await websocket.accept()
        self.active_connections[request_id] = websocket
    ```

2.  **`broadcast_to_request`**: The `LogBroadcaster` calls this method, providing the `request_id` and the message. The `ConnectionManager` looks up the correct WebSocket and sends the data.

    ```python
    # backend/app/websocket.py: line 36
    async def broadcast_to_request(self, request_id: str, message: Dict[str, Any]):
        if request_id in self.active_connections:
            websocket = self.active_connections[request_id]
            await websocket.send_json(message)
    ```

### `frontend/stock-research-ui/src/hooks/useWebSocketLogs.js`

Back on the frontend, this custom React hook manages the WebSocket connection.

**Key Logic:**

1.  **Connection**: When `enabled` and `requestId` are set, it establishes a connection to `ws://localhost:8000/ws/{requestId}`.
2.  **Message Handling**: The `ws.onmessage` event handler parses the incoming JSON from the backend and adds it to the `logs` state array.

    ```javascript
    // frontend/stock-research-ui/src/hooks/useWebSocketLogs.js: line 42
    ws.onmessage = (event) => {
      try {
        const logEvent = JSON.parse(event.data)
        setLogs((prevLogs) => [...prevLogs, logEvent])
      } catch (err) {
        console.error('Error parsing log message:', err)
      }
    }
    ```

3.  **UI Update**: The `StreamingLogPanel.jsx` component receives the `logs` array and renders the real-time updates.

## 5. The Specialists: Tools and Services

The `Orchestrator` uses various tools and services to gather and process information.

### `backend/tools/yahoo_finance_tool.py`

-   A wrapper around the `yfinance` library.
-   Provides methods like `get_stock_info`, `get_news`, and `get_price_history`.
-   Called by the `Orchestrator` during the `analyze_ticker_node` step.

### `backend/services/gemini_service.py`

-   Interfaces with the Google Gemini API.
-   Provides methods for summarization (`summarize_news`), analysis (`analyze_support_resistance`), and synthesis (`generate_investment_analysis`).
-   These methods construct prompts and send them to the Gemini model.

## Summary of the Flow

1.  **Frontend (`App.jsx`)**: User submits a query, a `request_id` is created, and an API call is made to the backend.
2.  **Backend (`api.py`)**: The request is received, and the `Orchestrator` is invoked with the query and `request_id`.
3.  **Backend (`orchestrator.py`)**: The LangGraph workflow begins. As it executes, it calls the `LogBroadcaster`.
4.  **Backend (`log_broadcaster.py`)**: The broadcaster formats a log message and uses the `ConnectionManager` to send it.
5.  **Backend (`websocket.py`)**: The `ConnectionManager` finds the correct WebSocket connection using the `request_id` and sends the message.
6.  **Frontend (`useWebSocketLogs.js`)**: The hook receives the message and updates the UI state.
7.  **Loop**: Steps 3-6 repeat as the `Orchestrator` continues its analysis, providing a seamless, real-time experience for the user.
8.  **Completion**: The `Orchestrator` finishes, returns the final analysis to `api.py`, which sends it back to the frontend as the final HTTP response.
