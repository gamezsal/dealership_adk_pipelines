import os
import uuid
import sys
import asyncio
import nest_asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 🟢 Apply nest_asyncio immediately to prevent asynchronous loop deadlocks on Windows/Python 3.13
nest_asyncio.apply()

# On Windows, configure the SelectorEventLoop for safe, stable async file and DB operations
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 🟢 Import the official, built-in AG-UI routing adapters
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.runners import Runner

# Import your actual root orchestrator and state machine from your agent files
from agents.agent import root_agent
from agents.state import DealPackState

load_dotenv()

# =========================================================================
# 🟢 SESSION SERVICE DIAGNOSTIC SELECTOR (IN-MEMORY TEST MODE ENABLED)
# =========================================================================
# We are currently using the InMemorySessionService to run the pipeline 
# in pure RAM, bypassing any SQLite database locks on Windows.
# =========================================================================
# session_service = DatabaseSessionService(db_url="sqlite+aiosqlite:///dealership_sessions.db")
session_service = InMemorySessionService() 
# =========================================================================

# Initialize the global sequential pipeline runner
runner = Runner(
    app_name="dealership_compliance_pipeline", 
    agent=root_agent, 
    session_service=session_service
)

app = FastAPI(title="Dealership QA & Provenance API")

# CORS configuration to safely handle local cross-port traffic
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# STORY 1.2: OFFICIAL AG-UI ENDPOINT MOUNT
# ---------------------------------------------------------
# Create the official ADK AG-UI middleware agent
adk_agent = ADKAgent(
    adk_agent=root_agent,
    app_name="dealership_compliance_pipeline",
    user_id="default",
    session_service=session_service,
    use_in_memory_services=True  # ◄── Enabled for pure RAM diagnostics
)

# Mount the official AG-UI streaming router at /api/copilotkit
add_adk_fastapi_endpoint(app, adk_agent, path="/api/copilotkit")


# ---------------------------------------------------------
# STORY 1.3: HITL RESUME WEBHOOK
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# STORY 1.4: NEO4J PROVENANCE REST ENDPOINT
# ---------------------------------------------------------
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

@app.get("/api/provenance/vehicle/{vin}")
def get_vehicle_provenance(vin: str):
    query = """
    MATCH (v:Vehicle {vin: $vin})-[:PROV_WAS_DERIVED_FROM]->(a:Anchor)-[:PROV_WAS_DERIVED_FROM]->(d:Document)
    RETURN 
        v.vin AS extracted_value,
        a.form_number AS form_number,
        a.page_number AS page_number,
        a.char_start AS highlight_start, 
        a.char_end AS highlight_end, 
        d.uri AS source_pdf_uri
    """
    
    def fetch_provenance(tx, vehicle_vin):
        result = tx.run(query, vin=vehicle_vin)
        return [record.data() for record in result]
        
    with driver.session() as session:
        records = session.execute_read(fetch_provenance, vin)
        
    if not records:
        raise HTTPException(status_code=404, detail=f"Provenance data for VIN '{vin}' not found.")
    return {"status": "success", "data": records}

@app.on_event("shutdown")
def shutdown_event():
    driver.close()