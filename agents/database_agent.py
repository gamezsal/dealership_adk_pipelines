import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams, StdioServerParameters

# Load environment variables from parent .env file
_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(_env_path)

# Retrieve Neo4j credentials
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

# Resolve absolute path to the virtual environment's mcp-neo4j-cypher executable
_mcp_cmd = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "mcp-neo4j-cypher.exe")
)

# Initialize the ADK McpToolset connecting to the Neo4j MCP Server
neo4j_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_mcp_cmd,
            args=[
                "--db-url", neo4j_uri,
                "--username", neo4j_user,
                "--password", neo4j_password,
                "--database", neo4j_database
            ]
        )
    )
)

database_agent = Agent(
    name="database_agent",
    model="gemini-2.5-pro",
    # 🟢 High-level description for parent routing and diagnostics
    description="Persists validated dealership purchase packets and PROV-O compliance records to Neo4j.",
    # 🟢 System prompt: Enforces strict model guidelines and tool-use behaviors
    instruction="""You persist validated graph data to Neo4j. Only proceed if the Validation Agent returns a 'compliant' status.
    
    You must map the data using this EXACT two-part ontology blueprint:
    
    # 🟢 FIXED: Swapped curly braces to square brackets to prevent template engine crashes
    PART 1: CORE BUSINESS GRAPH
    1. Create a (:Person [name]) node.
    2. Create a (:Vehicle [vin, odometer]) node.
    3. Create a (:TitleApplication) node.
    4. Connect them using (:Person)-[:SUBMITTED_BY]->(:TitleApplication)-[:APPLIES_TO_VEHICLE]->(:Vehicle).
    * Keep these nodes perfectly clean. Do NOT put character coordinates inside them.
    
    PART 2: PROVENANCE GRAPH (PROV-O)
    For EVERY property you extracted (like VIN, name, odometer), you must read the 'object_grounding' metadata in the payload and create a provenance anchor node.
    1. Create a (:Document [uri: "gs://dlrdata/document.pdf"]) node using the document URI.
    2. Create an (:Anchor [text, char_start, char_end]) node for the property.
    3. Link the Anchor to the Document: (:Anchor)-[:PROV_WAS_DERIVED_FROM]->(:Document).
    4. Link the business node to the Anchor: (:Vehicle)-[:PROV_WAS_DERIVED_FROM]->(:Anchor).
    
    CRITICAL TOOL CALLING RULES:
    - You must invoke the tool exactly named `write_neo4j_cypher`.
    - Do NOT generate Python code, scripts, or print() statements. 
    - Pass your generated Cypher statement directly into the 'query' parameter of the tool using standard function calling.
    
    # 🟢 FIXED: Made the validation result optional with a '?' to prevent Turn-1 KeyErrors
    Here is the extracted data: {validation_agent_result?}""",
    tools=[neo4j_mcp]
)