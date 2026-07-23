# =========================================================================
# 🟢 1. SYSTEM & ASYNC CORE IMPORTS
# =========================================================================
import os
import uuid
import sys
import asyncio
import nest_asyncio
import shutil        # 🟢 Added: For chunk-by-chunk copy of multipart file streams
import tempfile      # 🟢 Added: For buffering uploads in temporary disk space
import logging

from fastapi import FastAPI, HTTPException, UploadFile, File 
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from neo4j import GraphDatabase
from dotenv import load_dotenv

# =========================================================================
# 🟢 2. CRITICAL ABSOLUTE ENV PATH LOADER (MUST RUN IMMEDIATELY)
# Resolves the path to .env relative to where api.py sits on your disk.
# This prevents race conditions where agents import before .env loads!
# =========================================================================
_root_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_root_dir, ".env")
load_dotenv(_env_path)

# 🔬 Diagnostic Startup Prints (Monitored in your Uvicorn terminal)
print("\n" + "="*60)
print("🚀 API STARTUP DIAGNOSTIC: LOADING ENVIRONMENT")
print(f"🔗 Loaded NEO4J_URI  -> {os.getenv('NEO4J_URI')}")
print(f"👤 Loaded NEO4J_USER -> {os.getenv('NEO4J_USER') or os.getenv('NEO4J_USERNAME')}")
print("="*60 + "\n")

# =========================================================================
# 🟢 3. SYSTEM & ENVIRONMENT WORKAROUNDS
# =========================================================================
# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_gateway")

# 🟢 Apply nest_asyncio immediately to prevent Windows/Python 3.13 event loop collisions [3, 5]
nest_asyncio.apply()

# On Windows, configure the SelectorEventLoop for safe, stable async file and DB operations [3, 5]
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# =========================================================================
# 🟢 4. ADK, AG-UI, AGENT, & SERVICE IMPORTS (NOW SAFE!)
# =========================================================================
# 🟢 Import the official, built-in AG-UI routing adapters [2, 4]
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.runners import Runner

# Import your actual root orchestrator and state machine from your agent files [2, 4]
from agents.agent import root_agent
from agents.state import DealPackState

# 🟢 Import your dealership Google Cloud GCS services [6]
from services.gcs_service import GCSService

# Instantiate GCS service (it will self-configure using the now-loaded environment variables) [6]
gcs_service = GCSService()

# =========================================================================
# 🟢 5. SESSION SERVICE & PIPELINE RUNNER SETUP
# =========================================================================
# Using InMemorySessionService to run the pipeline in pure RAM, 
# completely bypassing any SQLite database locks on Windows development machines [7, 8].
session_service = InMemorySessionService()

# Initialize the global sequential pipeline runner [7, 8]
runner = Runner(
    app_name="dealership_compliance_pipeline",
    agent=root_agent,
    session_service=session_service
)

app = FastAPI(title="Dealership QA & Provenance API")

# CORS configuration to safely handle local cross-port traffic [9, 10]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================================
# 🟢 STORY 1.2: OFFICIAL AG-UI ENDPOINT MOUNT
# =========================================================================
# Create the official ADK AG-UI middleware agent [11, 12]
adk_agent = ADKAgent(
    adk_agent=root_agent,
    app_name="dealership_compliance_pipeline",
    user_id="default",
    session_service=session_service,
    use_in_memory_services=True  # ◄── Enabled for pure RAM diagnostics [11, 12]
)

# Mount the official AG-UI streaming router at /api/copilotkit [11, 12]
add_adk_fastapi_endpoint(app, adk_agent, path="/api/copilotkit")

# =========================================================================
# 🟢 STORY 1.3: HUMAN-IN-THE-LOOP (HITL) RESUME WEBHOOK
# =========================================================================
class ApprovalRequest(BaseModel):
    session_id: str

@app.post("/api/qa/approve")
async def approve_and_resume_agent(request: ApprovalRequest):
    """
    Webhook triggered by the React UI when a human approves the PDF highlights.
    Wakes the dormant ADK agent and pushes the verified payload to Neo4j.
    """
    async for event in runner.run_async(
        user_id="default",
        session_id=request.session_id,
        new_message="The QA Officer has approved the extracted coordinates. Hand off to the Database Agent.",
        state_delta={"current_step": DealPackState.READY_FOR_DB}
    ):
        pass
    return {"status": "success", "message": "Agent resumed successfully and handed off to Database Agent."}

# =========================================================================
# 🟢 STORY 1.4: NEO4J PROVENANCE REST ENDPOINTS
# =========================================================================
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

# Instantiate global read-only driver connection for the provenance REST query [13, 14]
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def fetch_provenance(tx, vin: str):
    """
    Retrieves the complete provenance verification network for a given VIN from Neo4j.
    """
    query = """
    MATCH (v:Vehicle {vin: $vin})-[r:PROV_WAS_DERIVED_FROM]->(a:Anchor)-[:PROV_WAS_DERIVED_FROM]->(d:Document)
    RETURN v.vin AS vin, a.text AS text, a.char_start AS char_start, a.char_end AS char_end, d.uri AS document_uri
    """
    result = tx.run(query, vin=vin)
    return [dict(record) for record in result]

@app.get("/api/provenance/{vin}")
async def get_provenance_data(vin: str):
    """
    REST endpoint to retrieve the full provenance network for a specific VIN.
    """
    try:
        with driver.session() as session:
            records = session.execute_read(fetch_provenance, vin)
            if not records:
                raise HTTPException(status_code=404, detail=f"Provenance data for VIN '{vin}' not found.")
            return {"status": "success", "data": records}
    except Exception as e:
        logger.error(f"❌ Provenance fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# 🟢 6. GCS FILE UPLOAD ROUTE
# =========================================================================
@app.post("/api/upload")
async def upload_dealership_pdf(file: UploadFile = File(...)):
    """
    Saves the uploaded dealership PDF stream to GCS via the self-configuring GCS service.
    Returns the public GCS URI so the agent can reference it during compliance extraction.
    """
    try:
        # Create a local temporary buffer file to write the stream chunk-by-chunk [6]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_path = tmp_file.name

        # Upload the temporary file to GCS [6]
        gcs_uri = await gcs_service.upload_file(temp_path, file.filename)
        
        # Clean up the local temporary file safely
        os.remove(temp_path)

        return {"status": "success", "gcs_uri": gcs_uri}
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file to GCS: {str(e)}")

# =========================================================================
# 🟢 7. CLEAN SERVICE SHUTDOWN
# =========================================================================
@app.on_event("shutdown")
def shutdown_event():
    """
    Closes the global Neo4j driver connection pool cleanly on server exit [15, 16].
    """
    driver.close()