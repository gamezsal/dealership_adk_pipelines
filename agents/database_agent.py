import os
import sys
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams, StdioServerParameters

# =========================================================================
# 🟢 CRITICAL AG-UI / COPILOTKIT STREAMING PATCH
# Monkey-patches McpToolset to make it completely deepcopy-safe.
# This prevents ag_ui_adk from crashing when duplicating system pipe handles.
# =========================================================================
McpToolset.__deepcopy__ = lambda self, memo: self
# =========================================================================

# 🟢 ROBUST ABSOLUTE ROOT RESOLUTION
# Using nested dirnames ensures .env is loaded cleanly regardless of Windows slash notation
_agents_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_agents_dir)
_env_path = os.path.join(_root_dir, ".env")
load_dotenv(_env_path)

# Retrieve Neo4j credentials
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or "neo4j"
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

# 🟢 Establish environmental variables globally in Python's os.environ dictionary.
os.environ["NEO4J_URI"] = neo4j_uri
os.environ["NEO4J_USERNAME"] = neo4j_user
os.environ["NEO4J_PASSWORD"] = neo4j_password
os.environ["NEO4J_DATABASE"] = neo4j_database

# 🔬 Diagnostic Startup Prints (Monitored in your Uvicorn terminal)
print("\n" + "="*60)
print("🤖 ADK DATABASE AGENT: BOOTSTRAP ENVIRONMENT VERIFICATION")
print(f"🔗 Target AuraDB URI -> {neo4j_uri}")
print(f"👤 Administrative User -> {neo4j_user}")
print(f"🔑 Password Configured -> {len(neo4j_password) if neo4j_password else 0} characters")
print("="*60 + "\n")

# Resolve absolute path to the virtual environment's mcp-neo4j-cypher executable
_mcp_cmd = os.path.abspath(
    os.path.join(_root_dir, ".venv", "Scripts", "mcp-neo4j-cypher.exe")
)

# Initialize the ADK McpToolset connecting to the Neo4j MCP Server
# 🟢 CRITICAL WINDOWS SUBPROCESS PATCH:
# We explicitly inject the 'env' dictionary here to guarantee these variables
# are handed directly to mcp-neo4j-cypher.exe upon execution.
neo4j_mcp = McpToolset(
    errlog=None, 
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_mcp_cmd,
            args=[],  
            env={
                "NEO4J_URI": neo4j_uri,
                "NEO4J_USERNAME": neo4j_user,
                "NEO4J_PASSWORD": neo4j_password,
                "NEO4J_DATABASE": neo4j_database
            }
        ),
        timeout=60.0  # ◄── Extends request execution timeouts up to 60 seconds
    )
)

database_agent = Agent(
    name="database_agent",
    model="gemini-2.5-pro",
    output_key="database_agent_result",
    description="Persists validated dealership purchase packets and PROV-O compliance records to Neo4j.",
    instruction="""You persist validated graph data to Neo4j. Only proceed if the Validation Agent returns a 'compliant' status.
    
    You must map the data using this EXACT two-part ontology blueprint:
    
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
    
    Here is the extracted data: {validation_agent_result?}""",
    tools=[neo4j_mcp]
)