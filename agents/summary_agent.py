from google.adk.agents import Agent

summary_agent = Agent(
    name="summary_agent",
    # 🟢 High-level description for parent routing and diagnostics
    description="Synthesizes the results of all compliance steps into a human-readable audit report.",
    model="gemini-2.5-flash",
    # 🟢 System prompt: Enforces strict model guidelines and template interpolation
    instruction="""You review the shared context from the entire workflow. 
    Your job is to synthesize the results into a clean, human-readable compliance and audit report for the Dealership Officer. 
    
    # 🟢 FIXED: Added '?' to make all step variables optional, preventing Turn-1 KeyError crashes
    Here are the results of the pipeline steps to summarize:
    - Upload: {upload_agent_result?}
    - Extraction: {extraction_agent_result?}
    - Validation: {validation_agent_result?}
    - Database: {database_agent_result?}
    
    If fraud was flagged, emphasize the exact validation failure.""",
    tools=[] # This agent synthesizes existing context, so it needs no external tools
)