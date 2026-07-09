
# Enterprise Multi-Agent System with Google ADK, Neo4j, and CopilotKit

A production-ready architectural template for deploying collaborative AI agents. This platform leverages Google's Agent Development Kit (ADK) for orchestration, Neo4j for graph-native session memory and GraphRAG, and CopilotKit for live streaming Generative UI over the AG-UI protocol.

## Architecture Highlights
- **Structured Multi-Agent Chains:** Utilizes code-first orchestration engine definitions via Sequential and Parallel agent delegations.
- **Graph-Native Context Tracking:** Implements persistent session management using `agent-memory` to maintain human-in-the-loop state loops.
- **Bi-directional Generative UI:** Synchronizes agent states with responsive React elements natively via unified SSE streams.
- **Managed Object Storage Pipelines:** Ingests local media, text structures, and PDF analytics chunks securely via direct API wrappers.

## Project Structure
```text
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── agent.py         # Main ADK Agent and flow logic definitions
│   │   ├── main.py          # FastAPI app wrapper initialization
│   │   └── gcs_service.py   # Infrastructure service managing Google Cloud Storage bucket connections
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/      # Generative UI components mapping to agent tools
    │   └── App.tsx          # CopilotKit Provider and chat interface wrappers
    ├── package.json
    └── vite.config.ts

```

## Setup & Installation

### 1. Prerequisites

* Python 3.10+ or Node.js v18+
* Active Neo4j Instance (Local Docker or AuraDB)
* Google Cloud Account with Vertex AI and Google Cloud Storage APIs enabled

### 2. Backend Configuration

Navigate to the `backend/` directory, configure your environment, and initialize:

```bash
cd backend
cp .env.example .env

```

Populate the `.env` file with your connection strings (including the targeted GCS bucket identity):

```ini
PORT=8080
GEMINI_API_KEY="your-gemini-api-key"
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="your-strong-password"
GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
GOOGLE_CLOUD_LOCATION="global"
GCS_BUCKET_NAME="your-enterprise-agent-storage-bucket"

```

Install dependencies and start the local server:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

```

### 3. Frontend Configuration

The React single-page application has been successfully scaffolded inside the `frontend/` directory using Vite, complete with proxy configurations and CopilotKit core runtime wrappers.

To install the environment tracking layers and run the frontend server:

```bash
cd ../frontend
npm install
npm run dev

```

---

## Testing & Verification (Work In Progress)

> ⚠️ **Status:** The environment blocks are fully installed and wired, but end-to-end integration tests are currently pending. Use the steps below to validate the components as we progress.

### Local Verification Roadmap

1. **Verify Backend Availability:**
Ensure the FastAPI app is serving routes without issues by pinging the status endpoint:
```bash
curl http://localhost:8080/health

```


2. **Verify Frontend Dev Server & Proxy Connection:**
Open `http://localhost:5173` in your browser. Verify that requests sent to `/api/*` successfully pass through Vite's dev server proxy to the FastAPI backend without throwing origin or CORS blocks.
3. **Verify CopilotKit Runtime Endpoint:**
Check if the agentic streaming platform endpoint is responsive by requesting descriptions:
```bash
curl http://localhost:8080/api/copilotkit

```


4. **Verify GCS Storage Handshake:**
Verify that your local user permissions or standard Application Default Credentials (ADC) let `gcs_service.py` securely list/write objects without access errors.
5. **Verify Neo4j Connection:**
Ensure that the backend logs confirm a stable handshake with `agent-memory` over the Bolt network line, indicating persistent checkpoints are tracking properly.

---

## Deployment

### Cloud Run (Using ADK CLI)

This application is optimized for containerized cloud architecture. You can compile and ship the backend service seamlessly:

```bash
cd backend
adk deploy --project=YOUR_PROJECT_ID --region=YOUR_DEPLOY_REGION

```

*Note: For production instances, configure your runtime settings to map secrets directly from Google Secret Manager instead of tracking environment variables in plaintext.*

## License

Distributed under the MIT License. See `LICENSE` for details.

```

```
