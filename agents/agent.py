from google.adk.agents import SequentialAgent
from google.adk.agents.callback_context import CallbackContext

from agents.upload_agent import upload_agent
from agents.extraction_agent import extraction_agent
from agents.validation_agent import validation_agent
from agents.database_agent import database_agent
from agents.summary_agent import summary_agent

# 🟢 Import DealPackState from your separate agents/state.py file
from agents.state import DealPackState

# 🟢 Safe State Initializer: Runs before any agent processes instructions
def initialize_compliance_state(callback_context: CallbackContext):
    if "current_step" not in callback_context.state:
        # Seed the starting step using your imported constants
        callback_context.state["current_step"] = DealPackState.EXTRACTING

root_agent = SequentialAgent(
    name="default",
    sub_agents=[
        upload_agent, 
        extraction_agent, 
        validation_agent, 
        database_agent, 
        summary_agent
    ],
    before_agent_callback=initialize_compliance_state,
    description="You are the Root Agent. Execute the dealership compliance process in strict order by routing tasks to your specialized sub-agents. Pass the state and outputs seamlessly from one agent to the next."
)