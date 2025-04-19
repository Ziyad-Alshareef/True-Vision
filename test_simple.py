import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Print environment variables (without secrets)
print(f"AWS_STORAGE_BUCKET_NAME: {os.environ.get('AWS_STORAGE_BUCKET_NAME')}")
print(f"AWS_S3_REGION_NAME: {os.environ.get('AWS_S3_REGION_NAME')}") 