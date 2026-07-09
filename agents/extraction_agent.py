from google.adk.agents import Agent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from tools.extraction_tools import extract_triplets_aevs

# NEW: Import the state from our decoupled file
from agents.state import DealPackState

# Configure Persistent Database Session
session_service = DatabaseSessionService(db_url="sqlite+aiosqlite:///dealership_sessions.db")

extraction_agent = Agent(
    name="extraction_agent",
    model="gemini-2.5-pro",
    instruction="""
    You are the Dealership QA Coordinator.
    Current Step: {current_step}
    
    If current_step is EXTRACTING, extract knowledge graph triplets from dealership PDFs. 
    Analyze the previous step's output: {upload_agent_result}. 
    Locate the GCS URI (starting with gs:// or gcs://) and call the extract_triplets_aevs tool with it. 
    If the GCS URI is missing or not explicitly shown in {upload_agent_result}, look at the tools output in the history to find the GCS URI, or use the default bucket path with the uploaded file name.
    
    CRITICAL: Once the tool returns the data, you must output the RAW, unaltered JSON dictionary directly so it can be passed to the Validation Agent. Do not summarize, format, or alter the extracted character coordinates or triplets in any way.
    
    After extraction, you MUST stop and wait. Do not proceed until current_step is READY_FOR_DB.
    """,
    tools=[extract_triplets_aevs]
)

# Create the Runner to bind the agent to the persistent session
runner = Runner(app_name="dealership_extraction_app", agent=extraction_agent, session_service=session_service)