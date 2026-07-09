from google.adk.agents import Agent

summary_agent = Agent(
    name="summary_agent",
    model="gemini-2.5-flash",
    description="You review the shared context from the entire workflow. Your job is to synthesize the results into a clean, human-readable compliance and audit report for the Dealership Officer. Here are the results of the pipeline steps to summarize - Upload: {upload_agent_result}, Extraction: {extraction_agent_result}, Validation: {validation_agent_result}, Database: {database_agent_result}. If fraud was flagged, emphasize the exact validation failure.",
    tools=[] # This agent synthesizes existing context, so it needs no external tools
)