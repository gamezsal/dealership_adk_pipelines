import json
from typing import Dict, Union
from rdflib import Graph, Literal, Namespace
from pyshacl import validate

# UPDATED: Changed parameter to accept the full AEVS dictionary (or string) payload
def validate_triplets_with_shacl(payload: Union[Dict, str, list]) -> Dict:
    """
    Tool for the Validation Agent: Runs SHACL data contracts against 
    the extracted triplets to ensure data compliance and catch fraud.
    """
    print("Starting SHACL Validation against extracted dealership data...")

    # 1. Safely parse the JSON string into a Python dictionary if passed as a string
    if isinstance(payload, str):
        # Strip out any potential markdown code blocks the LLM might have added
        clean_string = payload.strip().strip("`").removeprefix("json")
        payload = json.loads(clean_string)

    # 2. NEW: Extract the 'triplets' list from the full AEVS dictionary payload
    if isinstance(payload, dict):
        if "triplets" in payload:
            triplets = payload["triplets"]
        else:
            return {"status": "error", "report": "Failed to find 'triplets' array in payload."}
    elif isinstance(payload, list):
        triplets = payload  # Fallback just in case it was passed directly as a list
    else:
        return {"status": "error", "report": "Unexpected payload format."}

    # 3. Initialize the in-memory graph
    g = Graph()
    onto = Namespace("http://example.org/dealership#")
    g.bind("onto", onto)
    
    # 4. Load the extracted JSON triplets into the rdflib Graph dynamically
    for triplet in triplets:
        # Extract values using their dictionary keys safely. 
        # Note: This naturally ignores the 'object_grounding' key!
        subj = triplet.get("subject", "Document")
        pred = triplet.get("predicate")
        obj = triplet.get("object")
        
        if not pred or not obj:
            continue
        
        # Format the subject dynamically for rdflib Namespace lookup
        subj_clean = subj.replace(" ", "_").replace("/", "_").replace("-", "_")
        subject_uri = onto[subj_clean]
        predicate_uri = onto[pred]
        
        # Add the triplet to your RDF graph for SHACL validation
        g.add((subject_uri, predicate_uri, Literal(obj)))

    # 3. Define the SHACL validation shapes in Turtle format
    shacl_rules = r"""
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    @prefix onto: <http://example.org/dealership#> .

    # Rule 1: VINs must be exactly 17 characters AND contain no invalid letters (O, I, Q)
    onto:VIN_Validation a sh:NodeShape ;
        sh:targetSubjectsOf onto:has_VIN ;
        sh:property [
            sh:path onto:has_VIN ;
            sh:datatype xsd:string ;
            sh:minLength 17 ;
            sh:maxLength 17 ;
            sh:pattern "^[A-HJ-NPR-Z0-9]+$" ;
            sh:flags "i" ;
            sh:message "FRAUD FLAG: The extracted VIN is either not 17 characters or contains invalid letters (O, I, or Q)." ;
        ] .
        
    # Rule 2: A Buyer must have a Full Legal Name
    onto:Buyer_Validation a sh:NodeShape ;
        sh:targetSubjectsOf onto:has_Full_Legal_Name ;
        sh:property [
            sh:path onto:has_Full_Legal_Name ;
            sh:datatype xsd:string ;
            sh:minCount 1 ;
            sh:message "COMPLIANCE FLAG: Missing the buyer's Full Legal Name." ;
        ] .

    # Rule 3: Odometer Status Validation
    onto:Odometer_Status_Validation a sh:NodeShape ;
        sh:targetSubjectsOf onto:has_Odometer_Status ;
        sh:property [
            sh:path onto:has_Odometer_Status ;
            sh:datatype xsd:string ;
            sh:pattern "^(Actual|Exceeds Limits|Not Actual|Exempt)$" ;
            sh:flags "i" ;
            sh:message "COMPLIANCE FLAG: Odometer status must be Actual, Exceeds Limits, Not Actual, or Exempt." ;
        ] .

    # Rule 4: Purchase Price Validation
    onto:Purchase_Price_Validation a sh:NodeShape ;
        sh:targetSubjectsOf onto:has_Purchase_Price ;
        sh:property [
            sh:path onto:has_Purchase_Price ;
            sh:datatype xsd:string ;
            sh:pattern "^\\$?[0-9,.]+$" ;
            sh:message "COMPLIANCE FLAG: Purchase Price must be a valid numeric dollar amount." ;
        ] .

    # Rule 5: TAVT Tax Amount Validation
    onto:TAVT_Validation a sh:NodeShape ;
        sh:targetSubjectsOf onto:has_TAVT_Amount ;
        sh:property [
            sh:path onto:has_TAVT_Amount ;
            sh:datatype xsd:string ;
            sh:pattern "^\\$?[0-9,.]+$" ;
            sh:message "COMPLIANCE FLAG: TAVT Tax Amount must be a valid numeric dollar amount." ;
        ] .
    """
    
    shapes_graph = Graph().parse(data=shacl_rules, format="turtle")

    # 4. Execute the PySHACL Validation
    conforms, results_graph, results_text = validate(
        data_graph=g,
        shacl_graph=shapes_graph,
        inference='rdfs',
        abort_on_first=False,
        meta_shacl=False,
        debug=False
    )

    # 5. Return the compliance status to the Agent
    if conforms:
        return {"status": "compliant", "report": "Packet Compliant: True"}
    else:
        # If the contract is broken, pass the fraud flag back to the agent
        return {"status": "non-compliant", "report": f"FRAUD FLAG: \n{results_text}"}