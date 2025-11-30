# In-Depth Code Analysis: Stock Research Chatbot

**Author:** Manus AI
**Date:** November 19, 2025

## 1. Introduction

This document provides a comprehensive, line-by-line analysis of the Stock Research Chatbot application. It is intended for a senior manager to understand the complete workings of the system, from the user interface to the backend services and external API integrations. We will explore the architecture, data flow, and the specific code that connects each component, supported by visual diagrams.

## 2. System Architecture Overview

The application is a modern full-stack solution composed of a React frontend and a Python FastAPI backend. It leverages a multi-agent system orchestrated by LangGraph to perform detailed stock analysis, with real-time progress streaming to the user via WebSockets.

Below is the high-level architecture diagram illustrating the primary components and their interactions.
<!-- 
![System Architecture](/home/ubuntu/architecture_diagram.png) -->

### Key Components:

| Component                   | Technology      | Responsibility                                                                                             | Key Files                                                                 |
| --------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Frontend**                | React, Vite     | User interface, query submission, and real-time log display.                                               | `App.jsx`, `useWebSocketLogs.js`                                          |
| **Backend**                 | FastAPI, Python | API endpoints, WebSocket management, and orchestration of the analysis workflow.                           | `main.py`, `api.py`, `websocket.py`                                       |
| **Orchestration Engine**    | LangGraph       | Manages the sequence of analysis tasks, including data fetching and AI-powered synthesis.                  | `orchestrator.py`                                                         |
| **AI & Data Services**      | Gemini, Manus   | Provides AI-driven analysis (Google Gemini) and real-time financial data (Yahoo Finance via Manus API Hub). | `gemini_service.py`, `yahoo_finance_tool.py`                              |
| **Real-time Communication** | WebSockets      | Streams live progress and logs from the backend to the frontend for a responsive user experience.          | `websocket.py`, `useWebSocketLogs.js`, `log_broadcaster.py`               |

---

## 3. Detailed Data Flow

The following sequence diagram illustrates the entire process, from the user submitting a query to the final analysis being displayed. This shows the journey of a request through the system and how real-time feedback is provided.

<!-- ![Data Flow Diagram](/home/ubuntu/dataflow_diagram.png) -->

### The Request-Response Cycle:

1.  **Query Submission:** The user enters a query (e.g., "analyze AAPL and MSFT") in the React frontend (`App.jsx`) and clicks "Analyze".
2.  **API Request:** The frontend sends a `POST` request to the backend's `/api/v1/analyze` endpoint. Simultaneously, it establishes a WebSocket connection to `/ws/{request_id}` to listen for real-time updates.
3.  **Backend Processing:** The FastAPI backend receives the request in `api.py`. It initiates the `Orchestrator` and begins the analysis process.
4.  **Real-time Logging:** Throughout the analysis, the `Orchestrator` uses the `LogBroadcaster` to send progress updates. These messages are broadcasted through the `WebSocketManager` to the connected frontend client.
5.  **Data Fetching & AI Analysis:** The `Orchestrator` uses tools like `YahooFinanceTool` to fetch financial data and `GeminiService` to perform AI-powered analysis and synthesis.
6.  **Final Response:** Once the analysis is complete, the `Orchestrator` returns the final results to `api.py`. The backend then sends a final JSON response to the frontend's initial `POST` request.
7.  **Display Results:** The frontend (`App.jsx`) receives the final JSON response and renders the detailed stock insights for the user.

---

## 4. Backend Code Analysis

The backend is the core of the application, handling all the heavy lifting of data processing and analysis.

### `backend/app/main.py` - The Application Entry Point

This file sets up and configures the main FastAPI application.

-   **Line 57-62:** An instance of `FastAPI` is created with metadata such as the title and description.
-   **Line 65-71:** CORS (Cross-Origin Resource Sharing) middleware is configured to allow the frontend (running on a different port) to communicate with the backend.
-   **Line 74:** The API routes defined in `api.py` are included, making the `/api/v1/analyze` endpoint available.
-   **Line 77-107:** The WebSocket endpoint `/ws/{request_id}` is defined. This is where the frontend connects to receive real-time logs. It uses the `ConnectionManager` from `websocket.py` to handle the connection.

### `backend/app/api.py` - The API Router

This file defines the main `/analyze` endpoint that kicks off the stock analysis.

-   **Line 40:** The `@router.post("/analyze")` decorator defines the endpoint that listens for `POST` requests.
-   **Line 61:** A `LogBroadcaster` is created for the current request, which will be used to send real-time updates to the frontend.
-   **Line 135:** The `smart_correction_service` is used to detect and suggest corrections for any misspelled company names in the user's query.
-   **Line 226:** The `Orchestrator`'s `analyze` method is called. This is the main entry point into the LangGraph-based analysis workflow. The `await` keyword signifies that this is an asynchronous operation that will run in the background.
-   **Line 236:** Once the `Orchestrator` completes, the results are formatted into a standardized `AnalysisResponse` and sent back to the frontend.

### `backend/app/websocket.py` - The WebSocket Connection Manager

This module is responsible for managing all active WebSocket connections.

-   **`ConnectionManager` Class:** This class maintains a dictionary (`active_connections`) that maps each `request_id` to the corresponding WebSocket connection.
-   **Line 25 (`connect`):** When a new client connects, this method accepts the connection and stores it in the `active_connections` dictionary.
-   **Line 52 (`broadcast`):** This method sends a given message (a JSON payload) to all clients connected with a specific `request_id`.

### `backend/services/log_broadcaster.py` - The Real-time Log Emitter

This service provides a clean and simple interface for sending user-friendly log messages from anywhere in the backend.

-   **`LogBroadcaster` Class:** Initialized with a `request_id` and the `ConnectionManager` instance.
-   **Line 48 (`emit`):** The core method that constructs a log event dictionary and uses the `connection_manager` to broadcast it.
-   **User-Facing Methods (Lines 96-282):** A series of methods like `query_received`, `fetching_news`, and `analyzing_technicals` provide a high-level API for sending specific, pre-formatted progress updates. For example:

    ```python
    # backend/services/log_broadcaster.py: line 165
    async def fetching_news(self, ticker: str, company_name: str = None):
        display_name = company_name or ticker
        await self.emit(
            LogEventType.AGENT_START,
            f"📰 Searching for latest news about {display_name}...",
            agent="news",
            details={"ticker": ticker},
            delay=0.7
        )
    ```

### `backend/agents/orchestrator.py` - The LangGraph Orchestration Engine

This is the most critical component of the backend, where the multi-agent analysis takes place.

-   **`OrchestratorState` (Line 31):** A `TypedDict` that defines the structure of the state that is passed between the different nodes of our graph. It includes the query, tickers, results, and tracking information.
-   **`_build_workflow` (Line 74):** This method constructs the analysis workflow using `StateGraph` from LangGraph.
    -   **Nodes:** It defines the steps of the analysis, such as `extract_tickers_node` and `process_all_tickers`.
    -   **Edges:** It defines the transitions between the nodes, creating a directed graph that the analysis will follow.
-   **`analyze_ticker_node` (Line 106):** This is the core analysis function for a single stock. It simulates a sequence of agents (News, Price, Synthesis) by:
    1.  Calling the `YahooFinanceTool` to get real-time data (news, price, etc.).
    2.  Calling the `GeminiService` to summarize the data and generate insights.
    3.  Using the `LogBroadcaster` at each step to inform the user of its progress.
-   **`process_all_tickers` (Line 333):** This function takes the list of tickers and runs the `analyze_ticker_node` for each one in parallel using `asyncio.gather`, significantly speeding up the analysis of multiple stocks.
-   **`analyze` (Line 403):** The main public method that is called by `api.py`. It initializes the state and invokes the compiled LangGraph workflow with `self.workflow.ainvoke(initial_state)`.

### `backend/services/gemini_service.py` - The AI Brain

This service is responsible for all interactions with the Google Gemini AI model.

-   **Prompts:** It contains detailed, structured prompts that instruct the AI on how to perform specific tasks, such as summarizing news or generating a full investment analysis.
-   **JSON Output:** The prompts explicitly ask the AI to return its analysis in a structured JSON format, which makes it easy to parse and use in the backend.
-   **`generate_investment_analysis` (Line 106):** This method combines news, price data, and financial metrics into a single, comprehensive prompt to generate the final investment recommendation.

### `backend/tools/yahoo_finance_tool.py` - The Data Provider

This tool is the interface to real-world financial data.

-   **`ApiClient`:** It uses a generic `ApiClient` to make calls to the Manus API Hub, which provides a simplified interface to the Yahoo Finance API.
-   **Data Fetching Methods:** It provides methods like `get_stock_info`, `get_news`, and `get_price_history` that are called by the `Orchestrator`.
-   **Web Scraping Fallback (Line 24):** It includes a web scraping mechanism using `BeautifulSoup` as a fallback in case the API fails, making the system more resilient.

---

## 5. Frontend Code Analysis

The frontend is a responsive and user-friendly interface built with React.

### `frontend/stock-research-ui/src/App.jsx` - The Main UI Component

This file controls the entire user interface and application state.

-   **State Management (Lines 111-125):** It uses `useState` hooks to manage the query, analysis results, loading status, and the WebSocket connection.
-   **`handleAnalyze` (Line 133):** This function is the primary entry point for user interaction.
    -   **Line 151:** It generates a unique `request_id` for the analysis, which is essential for linking the HTTP request with the WebSocket stream.
    -   **Line 168:** It makes the `fetch` call to the backend's `/api/v1/analyze` endpoint.
    -   **Line 183:** It handles the `needs_confirmation` response from the backend, displaying a dialog to the user if a company name was misspelled.
-   **Rendering (Line 282 onwards):** The component renders the query input, the streaming log panel, and the final analysis results in a structured and readable format.

### `frontend/stock-research-ui/src/hooks/useWebSocketLogs.js` - The Real-time Connector

This custom React hook encapsulates all the logic for managing the WebSocket connection.

-   **`useWebSocketLogs` Hook (Line 9):** It takes the `requestId` and an `enabled` flag as input.
-   **`connect` (Line 22):** This function is called to establish the WebSocket connection to `ws://localhost:8000/ws/{requestId}`.
-   **`ws.onmessage` (Line 42):** This is the event handler for incoming messages. When a log event is received from the backend, it parses the JSON and updates the `logs` state array.
-   **Reconnection Logic (Line 67):** It includes a robust reconnection mechanism with exponential backoff, ensuring that the connection is restored if it drops unexpectedly.

---

## 6. Conclusion

The Stock Research Chatbot is a well-architected, full-stack application that demonstrates the power of combining a modern web framework (React/FastAPI) with an AI orchestration engine (LangGraph) and real-time communication (WebSockets). The clear separation of concerns between the frontend, backend, and AI services makes the system modular, scalable, and maintainable.

The line-by-line connections show a clear and logical flow of data, from the user's initial query to the final, AI-generated insights. The use of a dedicated `LogBroadcaster` and WebSocket manager provides a professional and engaging user experience, setting this application apart from standard request-response systems.
