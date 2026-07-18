import os
from fastapi import FastAPI, HTTPException, Request  # Added Request import here!
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Import the CopilotKit FastAPI adapter
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint

# NEW: Import the AG-UI ADK adapter
from ag_ui_adk import ADKAgent

# 1. Import your actual root orchestrator from your agent.py file!
from agents.agent import root_agent

# 2. Import the runner (which handles the session) from extraction_agent
from agents.extraction_agent import runner

# 3. Import the decoupled state machine from our new 7th file
from agents.state import DealPackState

load_dotenv()

app = FastAPI(title="Dealership QA & Provenance API")

# ---------------------------------------------------------
# NEW: Add CORS to safely handle cross-port browser traffic
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# NEW: Silent Slash Normalization Middleware
# Intercepts "/api/copilotkit" requests and silently normalizes
# them internally to "/api/copilotkit/" to bypass the 307 Redirect.
# ---------------------------------------------------------
@app.middleware("http")
async def normalize_copilotkit_slash(request: Request, call_next):
    if request.url.path == "/api/copilotkit":
        request.scope["path"] = "/api/copilotkit/"
    return await call_next(request)

# ---------------------------------------------------------
# STORY 1.2: AG-UI AGENT STREAMING ENDPOINT
# ---------------------------------------------------------
# 1. Create the ADKAgent wrapper instance
adk_agent_wrapper = ADKAgent(root_agent)

# 2. NEW: Explicitly set the name attribute so the SDK doesn't fall back to index "0"
adk_agent_wrapper.name = "default"

# 3. Maintain the dict_repr patch to prevent frontend mapping crashes
adk_agent_wrapper.dict_repr = lambda: {
    "name": "default",
    "description": "Agent that extracts Deal Matrix data from PDFs.",
    "type": "adk", 
    "tools": []    
}

# 4. Pass the patched wrapper into the SDK
sdk = CopilotKitRemoteEndpoint(
    agents=[adk_agent_wrapper]
)

# Adds the /api/copilotkit POST route to your FastAPI app
add_fastapi_endpoint(app, sdk, "/api/copilotkit")

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
    # Hydrates the session and uses state_delta to transition the state machine
    await runner.run_async(
        session_id=request.session_id,
        prompt="The QA Officer has approved the extracted coordinates. Hand off to the Database Agent.",
        state_delta={"current_step": DealPackState.READY_FOR_DB}
    )
    
    return {"status": "success", "message": "Agent resumed successfully."}


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
    
    # Define the explicit read transaction function
    def fetch_provenance(tx, vehicle_vin):
        result = tx.run(query, vin=vehicle_vin)
        return [record.data() for record in result]
        
    with driver.session() as session:
        # Execute the query using the optimized execute_read method
        records = session.execute_read(fetch_provenance, vin)
        
    if not records:
        raise HTTPException(status_code=404, detail="Provenance data not found.")
    return {"status": "success", "data": records}

@app.on_event("shutdown")
def shutdown_event():
    driver.close()