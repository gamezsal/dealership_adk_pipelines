from typing import Dict
from services.gcs_service import GCSService

def upload_media(local_file_path: str, destination_name: str, tool_context=None) -> Dict:
    """
    Tool for the Upload Agent: Takes a local PDF file, an artifact name, or an attached file
    and stages it in Google Cloud Storage for the extraction agent to read.
    """
    print(f"Tool Layer: Intent to upload '{local_file_path}' received.")
    
    try:
        # The tool acts as an interface and uses the service for execution
        gcs_service = GCSService()
        
        # 1. Check if the path refers to an uploaded artifact
        if tool_context and local_file_path.startswith("artifact_"):
            artifact = tool_context.load_artifact(local_file_path)
            if artifact and artifact.inline_data and artifact.inline_data.data:
                # Upload the bytes directly
                file_bytes = artifact.inline_data.data
                mime_type = artifact.inline_data.mime_type or "application/pdf"
                
                # Ensure destination name has appropriate suffix
                if not destination_name.endswith(".pdf") and mime_type == "application/pdf":
                    destination_name = f"{destination_name}.pdf"
                
                gcs_uri = gcs_service.upload_bytes(file_bytes, destination_name, mime_type)
                return {"status": "success", "gcs_uri": gcs_uri}

        # 2. Check if there is an attached file (inline_data) in the user's message
        if tool_context and (local_file_path == "attached_file" or local_file_path.startswith("artifact_")):
            user_content = tool_context.user_content
            if user_content and user_content.parts:
                for part in user_content.parts:
                    if part.inline_data and part.inline_data.data:
                        file_bytes = part.inline_data.data
                        mime_type = part.inline_data.mime_type or "application/pdf"
                        
                        # Ensure destination name has appropriate suffix
                        if not destination_name.endswith(".pdf") and mime_type == "application/pdf":
                            destination_name = f"{destination_name}.pdf"
                        
                        gcs_uri = gcs_service.upload_bytes(file_bytes, destination_name, mime_type)
                        return {"status": "success", "gcs_uri": gcs_uri}

        # 3. Fallback to local file upload
        gcs_uri = gcs_service.upload_file(local_file_path, destination_name)
        
        # Return a structured dictionary for the ADK Agent-to-Agent handoff
        return {"status": "success", "gcs_uri": gcs_uri}
    
    except Exception as e:
        print(f"Failed to upload media: {e}")
        return {"status": "error", "message": str(e)}