import os
from google.cloud import storage

class GCSService:
    def __init__(self):
        self.project_id = os.getenv("PROJECT_ID")
        # Remove the 'gs://' prefix if it exists in the env variable
        self.bucket_name = os.getenv("GCS_BUCKET", "dlrdata").replace("gs://", "")
        
        # Initialize the GCS client
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_file(self, local_file_path: str, destination_blob_name: str) -> str:
        """Handles the physical implementation of uploading a file to GCS."""
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_file_path)
        
        gcs_uri = f"gs://{self.bucket_name}/{destination_blob_name}"
        print(f"Service Layer: Successfully uploaded to {gcs_uri}")
        return gcs_uri

    def upload_bytes(self, file_bytes: bytes, destination_blob_name: str, content_type: str = "application/pdf") -> str:
        """Handles uploading raw bytes directly to GCS."""
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes, content_type=content_type)
        
        gcs_uri = f"gs://{self.bucket_name}/{destination_blob_name}"
        print(f"Service Layer: Successfully uploaded bytes to {gcs_uri}")
        return gcs_uri