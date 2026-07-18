from google.adk.agents import Agent
from tools.ingestion_tools import upload_media

upload_agent = Agent(
    name="upload_agent",
    model="gemini-2.5-flash",
    # 🟢 High-level summary for orchestrator routing and dashboards
    description="Extracts and processes raw files/paths and uploads them to Google Cloud Storage.",
    # 🟢 System prompt: Strict guidelines that enforce model reasoning and tool-calling behavior
    instruction="""You are the Upload Agent. Your strict job is to extract and process any files or paths from the user's message:
    - If the user's message already contains a GCS URI (starting with gs:// or gcs://), output that URI directly to the next agent and do NOT call the upload tool.
    - If the user has attached a file directly (which you will see as an inline data/media part in your input), execute the upload tool immediately. Use local_file_path='attached_file' and a clean destination name (e.g., 'document.pdf').
    - If the user's message mentions an uploaded file (e.g., 'Uploaded file: artifact_xxxx_y'), automatically extract the artifact name (e.g., 'artifact_xxxx_y') and execute the upload tool immediately. Pass the artifact name as the local_file_path.
    - If the user's message contains a local file path, automatically extract the file name and execute the upload tool immediately. Do not ask for confirmation.
    Pass the GCS URI to the next agent.""",
    tools=[upload_media]
)