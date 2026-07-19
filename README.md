# Dealership QA & Provenance Compliance Pipeline

An enterprise-grade, multi-agent AI system designed to ingest automotive dealership deal matrix files, extract critical purchase packets with precise character coordinates, validate compliance constraints, and store audit-ready provenance records inside a Neo4j Graph Database.

The system utilizes Google's **Agent Development Kit (ADK)** for agent orchestration, **Neo4j AuraDB** as a graph-native memory and data layer, and **CopilotKit** combined with the **AG-UI Protocol** to deliver real-time streaming state and interactive highlights directly to a React frontend.

---

## 🏗️ System Architecture

```
                                    ┌──────────────────────┐
                                    │    React Frontend    │
                                    │     (Vite Client)    │
                                    └──────────┬───────────┘
                                               │ (AG-UI Events / SSE)
                                               ▼
                                    ┌──────────────────────┐
                                    │ CopilotKit Runtime   │
                                    │     (Node Server)    │
                                    └──────────┬───────────┘
                                               │ (Proxy HTTP)
                                               ▼
                                    ┌──────────────────────┐
                                    │   FastAPI Backend    │
                                    │     (ADK Engine)     │
                                    └────┬─────────────┬───┘
                                         │             │
                                         ▼             ▼
                                   ┌───────────┐ ┌───────────┐
                                   │  Google   │ │   Neo4j   │
                                   │   Cloud   │ │  AuraDB   │
                                   │  Storage  │ │  (Graph)  │
                                   └───────────┘ └───────────┘
```

The system is built on a **3-Tier Agentic Architecture**:
1. **The Interactive Layer (Frontend):** A React Single-Page Application utilizing CopilotKit components and headless state hooks. It captures user inputs and file uploads and displays the interactive compliance approval interface.
2. **The Orchestration Bridge (Middleware/Runtime):** A Node.js runtime proxying client requests, normalizing Server-Sent Events (SSE), and coordinating the conversation threads.
3. **The Multi-Agent Engine (Backend):** A FastAPI server hosting a Google ADK `SequentialAgent` workflow. It splits cognitive tasks among four specialized, domain-specific sub-agents:
   * **Upload Agent:** Stages and persists incoming file payloads to Google Cloud Storage.
   * **Extraction Agent:** Multimodal parsing of dealer matrices using Gemini 2.5 Pro to extract key properties and character offsets.
   * **Validation Agent:** Audits data fields against strict compliance metrics and manages the human-in-the-loop (HITL) checkpoint.
   * **Database Agent:** Uses a Neo4j Model Context Protocol (MCP) toolset to persist core purchase and PROV-O compliance records.

---

## 💻 Tech Stack

### Frontend Client
* **Framework:** React 18+ with TypeScript [144]
* **Build System:** Vite (providing ESM-based instant hot module replacement) [144, 511]
* **Copilot Layer:** `@copilotkit/react-core` (v2) and `@copilotkit/react-ui` [59, 410]
* **Styling & Components:** Tailwind CSS & shadcn/ui primitives [61, 366]
* **Communication Wire:** AG-UI Protocol over Server-Sent Events (SSE) [362, 584]

### Backend Services
* **Language:** Python 3.10+ (Optimized for 3.13) [138, 413]
* **API Framework:** FastAPI served by high-speed Uvicorn ASGI workers [143]
* **Orchestration:** Google Agent Development Kit (ADK) [143, 403]
* **Database Driver:** Official `neo4j` Python driver with native `neo4j-rust-ext` [143]
* **Persistent Checkpointer:** Google ADK `DatabaseSessionService` (backed by SQLite/PostgreSQL) [80, USAGE.md]
* **Subprocess Tools:** Model Context Protocol (MCP) using the `mcp-neo4j-cypher` server [182, 398]

---

## 🔑 Environment Configuration

Create a `.env` file in your **`backend/`** directory. Populate it with your active credentials:

```env
# Google Gemini API
GEMINI_API_KEY="AIzaSy..."

# Neo4j AuraDB Database Connection
NEO4J_URI="neo4j+s://xxxxxxxx.databases.neo4j.io"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="your-secure-auradb-password"
NEO4J_DATABASE="neo4j"

# Google Cloud Storage (PDF Staging)
GCS_BUCKET_NAME="Bucket_Name"
GOOGLE_APPLICATION_CREDENTIALS="path/to/your/gcp-service-account.json"
```

---

## 🚀 Local Startup Sequence

To launch the entire stack on Windows, you must spin up your development processes in a **coordinated 3-terminal sequence**. 

> ⚠️ **CRITICAL WINDOWS SUBPROCESS NOTE:** When running Uvicorn on Windows, do **NOT** use the `--reload` flag in your active backend terminal. On Windows, hot-reloading breaks standard input/output (`stdio`) pipes bound to the background MCP database processes, resulting in silent stream crashes.

### Step 1: Start the Python Backend (Terminal 1)
Initialize your Python environment, verify environment variables, and launch the ASGI server in a stable, single-process container:
```powershell
cd backend
.venv\Scripts\activate
uvicorn api:app --host 127.0.0.1 --port 8000
```
*Wait until you see `INFO: Application startup complete` in your console logs.*

### Step 2: Start the Copilot Runtime Node Proxy (Terminal 2)
Boot the server-side middleware to act as the communication bridge between Vite and FastAPI:
```powershell
cd runtime
npm install
npm start
```
*Look for `[CopilotKit Runtime] anonymous telemetry enabled` to confirm the gateway is listening.*

### Step 3: Start the React Frontend (Terminal 3)
Compile your TypeScript resources and launch the local browser development server:
```powershell
cd frontend
npm install
npm run dev
```
*Navigate your browser to `http://localhost:5173/` to view the live dashboard.*

---

## 🧪 Verification & Inspection Roadmap

1. **API Handshake (CORS Check):** Verify that the Vite development server proxy is successfully routing client requests to FastAPI. Run a GET request to `http://localhost:5173/api/copilotkit` or test via the browser.
2. **MCP Process Safety:** Ensure that no `BrokenPipeError` or `TaskGroup` exceptions appear in the backend terminal when starting your first turn. If errors occur, verify that you started Uvicorn without `--reload`.
3. **Database Checkpoint Verification:** Verify that persistent state checkpoints are functioning. On initial prompt, verify that the backend creates a `dealership_sessions.db` SQLite file locally or writes cleanly to your persistent schema.
4. **multimodal Attachment Support:** Ensure the upload button is visible in the chat composer interface. Drag and drop a Deal Matrix PDF to kick off the Upload Agent ingestion loop.
