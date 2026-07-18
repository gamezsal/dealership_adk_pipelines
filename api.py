import os
import uuid
import json
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
from ag_ui.core import (
    RunAgentInput, UserMessage, AssistantMessage, SystemMessage, ToolMessage,
    ToolCall, FunctionCall
)

# 1. Import your actual root orchestrator from your agent.py file!
from agents.agent import root_agent

# 2. Import the runner (which handles the session) from extraction_agent
from agents.extraction_agent import runner

# 3. Import the decoupled state machine from our new 7th file
from agents.state import DealPackState

load_dotenv()

# NEW: Pure ASGI Silent Slash Normalization Middleware
# Intercepts "/api/copilotkit" requests and silently normalizes
# them internally to "/api/copilotkit/" to bypass the 307 Redirect
# without interfering with StreamingResponse/SSE.
class NormalizeSlashMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] == "/api/copilotkit":
            scope["path"] = "/api/copilotkit/"
        await self.app(scope, receive, send)

app = FastAPI(title="Dealership QA & Provenance API")

app.add_middleware(NormalizeSlashMiddleware)

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
# STORY 1.2: AG-UI AGENT STREAMING ENDPOINT
# ---------------------------------------------------------
class CopilotKitADKAgent(ADKAgent):
    async def execute(
        self,
        *,
        state: dict,
        thread_id: str,
        messages: list,
        actions: list = None,
        node_name: str = None,
        config: dict = None,
        meta_events: list = None,
        **kwargs,
    ):
        ag_ui_messages = []
        for msg in messages:
            role = msg.get("role")
            msg_id = msg.get("id", str(uuid.uuid4()))
            
            if role == "user":
                ag_ui_messages.append(
                    UserMessage(
                        id=msg_id,
                        content=msg.get("content") or "",
                        role="user"
                    )
                )
            elif role == "system":
                ag_ui_messages.append(
                    SystemMessage(
                        id=msg_id,
                        content=msg.get("content") or "",
                        role="system"
                    )
                )
            elif role == "assistant":
                if "name" in msg and "arguments" in msg:
                    tool_call_id = msg.get("id")
                    tool_name = msg.get("name")
                    arguments = msg.get("arguments")
                    if isinstance(arguments, dict):
                        arguments = json.dumps(arguments)
                    
                    tool_calls = [
                        ToolCall(
                            id=tool_call_id,
                            type="function",
                            function=FunctionCall(name=tool_name, arguments=arguments)
                        )
                    ]
                    ag_ui_messages.append(
                        AssistantMessage(
                            id=msg_id,
                            content="",
                            role="assistant",
                            tool_calls=tool_calls
                        )
                    )
                else:
                    tool_calls_list = []
                    for tc in msg.get("toolCalls") or []:
                        args = tc.get("args") or tc.get("arguments")
                        if isinstance(args, dict):
                            args = json.dumps(args)
                        tool_calls_list.append(
                            ToolCall(
                                id=tc.get("id"),
                                type="function",
                                function=FunctionCall(name=tc.get("name"), arguments=args)
                            )
                        )
                    ag_ui_messages.append(
                        AssistantMessage(
                            id=msg_id,
                            content=msg.get("content") or "",
                            role="assistant",
                            tool_calls=tool_calls_list if tool_calls_list else None
                        )
                    )
            elif role == "tool" or "actionExecutionId" in msg:
                tool_call_id = msg.get("actionExecutionId") or msg.get("id")
                result = msg.get("result") or msg.get("content") or ""
                ag_ui_messages.append(
                    ToolMessage(
                        id=msg_id,
                        content=result,
                        role="tool",
                        tool_call_id=tool_call_id
                    )
                )

        run_input = RunAgentInput(
            thread_id=thread_id,
            run_id=str(uuid.uuid4()),
            state=state or {},
            messages=ag_ui_messages,
            tools=[],
            context=[],
            forwarded_props=None,
        )

        async for event in self.run(run_input):
            encoded = event.model_dump_json(by_alias=True, exclude_none=True)
            yield encoded

    async def get_state(self, *, thread_id: str):
        app_name = self._static_app_name or "default"
        user_id = self._static_user_id or "default"
        session = await self._session_manager._find_session_by_thread_id(
            app_name=app_name,
            user_id=user_id,
            thread_id=thread_id
        )
        thread_exists = session is not None
        state = {}
        if thread_exists:
            state = await self._session_manager.get_session_state(
                session_id=session.id,
                app_name=app_name,
                user_id=user_id
            ) or {}
            
        return {
            "threadId": thread_id,
            "threadExists": thread_exists,
            "state": state,
            "messages": []
        }

# 1. Create the CopilotKitADKAgent wrapper instance
adk_agent_wrapper = CopilotKitADKAgent(root_agent)

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

# Monkeypatch info to return agents as a dict (matching JS SDK expectations)
class DictWithListIter(dict):
    def __iter__(self):
        return iter(self.values())

original_info = sdk.info
def custom_info(context):
    res = original_info(context=context)
    if isinstance(res.get("agents"), list):
        res["agents"] = DictWithListIter({agent["name"]: agent for agent in res["agents"]})
    return res
sdk.info = custom_info

# Mock CopilotKit threads endpoints to satisfy frontend persistence requests
@app.get("/api/copilotkit/threads")
async def get_copilotkit_threads():
    return {"threads": []}

@app.post("/api/copilotkit/threads")
async def post_copilotkit_threads():
    return {"threadId": str(uuid.uuid4())}

@app.get("/api/copilotkit/threads/{thread_id}")
async def get_copilotkit_thread(thread_id: str):
    return {"threadId": thread_id, "messages": []}

@app.post("/api/copilotkit/threads/{thread_id}/archive")
async def archive_copilotkit_thread(thread_id: str):
    return {"success": True}

@app.delete("/api/copilotkit/threads/{thread_id}")
async def delete_copilotkit_thread(thread_id: str):
    return {"success": True}

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