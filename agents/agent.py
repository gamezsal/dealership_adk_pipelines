from google.adk.agents import SequentialAgent
from google.adk.agents.callback_context import CallbackContext # 🟢 Import CallbackContext

from agents.upload_agent import upload_agent
from agents.extraction_agent import extraction_agent
from agents.validation_agent import validation_agent
from agents.database_agent import database_agent
from agents.summary_agent import summary_agent

# 🟢 FIXED: Function signature must accept exactly 'callback_context'
def initialize_compliance_state(callback_context: CallbackContext):
    if "current_step" not in callback_context.state:
        callback_context.state["current_step"] = "UPLOAD_INGESTION"

# Make sure all brackets, quotes, and parentheses are properly closed below
root_agent = SequentialAgent(
    name="default",
    sub_agents=[
        upload_agent, 
        extraction_agent, 
        validation_agent, 
        database_agent, 
        summary_agent
    ],
    # 🟢 Bind the corrected callback
    before_agent_callback=initialize_compliance_state,
    description="You are the Root Agent. Execute the dealership compliance process in strict order by routing tasks to your specialized sub-agents. Pass the state and outputs seamlessly from one agent to the next."
)