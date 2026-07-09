from google.adk.agents import Agent
from tools.validation_tools import validate_triplets_with_shacl

validation_agent = Agent(
    name="validation_agent",
    model="gemini-2.5-pro",
    description="""You enforce SHACL data contracts to catch fraud. 
    Analyze the previous step's output: {extraction_agent_result}. 
    This output is a grounded JSON payload from the AEVS extraction framework containing 'anchors' and 'triplets'.
    
    Invoke the validate_triplets_with_shacl tool and pass the 'triplets' array into it. 
    
    CRITICAL: You must pass the triplets EXACTLY as they appear in {extraction_agent_result}. Do not remove or alter the 'object_grounding', 'char_start', or 'char_end' coordinates, as they are required for provenance tracking.
    
    If the status returned by the tool is 'non-compliant', you must flag the error and halt the pipeline from saving to the database.""",
    tools=[validate_triplets_with_shacl]
)