from google.adk.agents import Agent
from tools.extraction_tools import extract_triplets_aevs

# Keep the state import for decoupled typing if needed
from agents.state import DealPackState

# 🟢 REMOVED: Redundant DatabaseSessionService and Runner instances.
# These are managed globally by the root_agent in agent.py to prevent locks and share state.

extraction_agent = Agent(
    name="extraction_agent",
    model="gemini-2.5-pro",
    # 🟢 ADDED: Saves the extracted triplets JSON directly to this key in the shared state
    output_key="extraction_result", 
    description="Analyzes purchase packets in Google Cloud Storage and extracts high-fidelity semantic triplets.",
    instruction="""
    You are the Dealership QA Coordinator.
    
    # 🟢 FIXED: Appended '?' to make variables optional, preventing compilation KeyErrors
    Current Step: {current_step?}
    
    If current_step is EXTRACTING, extract knowledge graph triplets from dealership PDFs. 
    
    # 🟢 FIXED: Point to 'upload_result' (the output key of your upload_agent) safely
    Analyze the previous step's output: {upload_result?}. 
    Locate the GCS URI (starting with gs:// or gcs://) and call the extract_triplets_aevs tool with it. 
    If the GCS URI is missing or not explicitly shown in {upload_result?}, look at the tools output in the history to find the GCS URI, or use the default bucket path with the uploaded file name.
    
    CRITICAL: Once the tool returns the data, you must output the RAW, unaltered JSON dictionary directly so it can be passed to the Validation Agent. Do not summarize, format, or alter the extracted character coordinates or triplets in any way.
    
    After extraction, you MUST stop and wait. Do not proceed until current_step is READY_FOR_DB.
    """,
    tools=[extract_triplets_aevs]
)
