import os
import json
from typing import Dict
import vertexai
from vertexai.generative_models import GenerativeModel, Part

# Import ADK context and the NEW decoupled State Machine schema
from google.adk.tools import ToolContext
from agents.state import DealPackState  # <--- THIS IS THE CRITICAL CHANGE

def extract_triplets_aevs(ctx: ToolContext, gcs_uri: str) -> Dict:
    """
    Tool for the Extraction Agent to read an uploaded PDF from Google Cloud Storage 
    and extract knowledge graph triplets using the AEVS framework.
    """
    print(f"Starting AEVS Extraction for document: {gcs_uri}")

    project_id = os.getenv("PROJECT_ID")
    # us-central1 is the primary hub for Gemini 2.5 Pro
    location = os.getenv("LOCATION", "us-central1") 
    vertexai.init(project=project_id, location=location)
    
    if gcs_uri.startswith("gcs://"):
        gcs_uri = gcs_uri.replace("gcs://", "gs://", 1)

    document_part = Part.from_uri(uri=gcs_uri, mime_type="application/pdf")
    model = GenerativeModel("gemini-2.5-pro")

    # ---------------------------------------------------------
    # STAGE 1 & 2: ANCHOR DISCOVERY & GROUNDED EXTRACTION
    # ---------------------------------------------------------
    aevs_prompt = """
    You are a strict data extraction agent. Analyze the attached document and extract knowledge using the Anchor-Constrained (AEVS) framework.
    
    You must output a strictly formatted JSON object containing two stages.

    STAGE 1: ANCHOR DISCOVERY
    Identify the exact text snippets and their PRECISE character positions (char_start, char_end) for the following entities:
    - Form Name / Form Number (e.g., "Form MV-1", "MV-7DW", "Title Back")
    - 17-character VIN (Vehicle Identification Number)
    - Sale Date / Date purchased
    - Buyer's / Seller's Full Legal Name / Dealership Name
    - Odometer Reading / Odometer Status
    - Purchase Price / TAVT Amount
    - Lienholder Name
    
    Classify them as "entity", "attribute", or "relation".
    
    STAGE 2: GROUNDED EXTRACTION
    Using ONLY the anchors from Stage 1, generate knowledge graph triplets.
    - Identify the short Form Number to construct a clean subject identifier (e.g., "Form_MV-1"). If none, use "Form_Unknown".
    - Use ONLY these specific predicates: has_Form_Name, has_Form_Number, has_VIN, has_Sale_Date, has_Full_Legal_Name, has_Odometer_Reading, has_Odometer_Status, has_Seller_Name, has_Purchase_Price, has_TAVT_Amount, has_Lienholder_Name.
    
    CRITICAL RULES:
    1. NO HALLUCINATION: Every triplet element MUST correspond exactly to a discovered anchor. Do not invent or auto-correct.
    2. PROVENANCE GROUNDING: For each object in the triplet, provide the "object_grounding" with the exact anchor_text, char_start, and char_end.
    
    EXPECTED JSON FORMAT:
    {
      "anchors": [
        {"text": "3VWDB7AJ8HM266903", "type": "attribute", "char_start": 150, "char_end": 167}
      ],
      "triplets": [
        {
          "subject": "Form_MV-1",
          "predicate": "has_VIN",
          "object": "3VWDB7AJ8HM266903",
          "object_grounding": {"anchor_text": "3VWDB7AJ8HM266903", "char_start": 150, "char_end": 167}
        }
      ]
    }
    """
    print("Executing AEVS Extraction via Gemini JSON Mode...")
    
    response = model.generate_content(
        [document_part, aevs_prompt],
        # Forces Gemini to return strict, parseable JSON
        generation_config={"response_mime_type": "application/json"}
    )

    print("Parsing Grounded JSON output and beginning verification...")
    try:
        # 1. Parse the strict JSON output returned by Gemini
        raw_json = response.text.strip("```json").strip("```")
        extracted_data = json.loads(raw_json)
        
        # ---------------------------------------------------------
        # 2. THE HITL DORMANCY GATE (STORY 1.3)
        # ---------------------------------------------------------
        # Atomically update the persistent session state to put the agent to sleep
        # while we wait for the human QA officer to verify the data in the React UI!
        ctx.state["current_step"] = DealPackState.AWAITING_QA_APPROVAL
        
        print("Extraction complete. Agent entering AWAITING_QA_APPROVAL state.")
        
        # 3. Return the payload to the frontend over the AG-UI stream
        return {
            "status": "paused_for_qa", 
            "data": extracted_data
        }
        
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Failed to parse LLM JSON: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}