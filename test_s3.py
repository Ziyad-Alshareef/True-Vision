import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_s3_connection():
    """Test S3 connection with credentials from environment variables"""
    print("Testing S3 connection...")
    
    # Print environment variables (without secrets)
    print(f"AWS_STORAGE_BUCKET_NAME: {os.environ.get('AWS_STORAGE_BUCKET_NAME')}")
    print(f"AWS_S3_REGION_NAME: {os.environ.get('AWS_S3_REGION_NAME')}")
    
    # Create a boto3 session
    session = boto3.session.Session(
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_S3_REGION_NAME')
    )
    
    # Create S3 client
    s3 = session.client('s3')
    
    # Get bucket details
    bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    print(f"Using bucket name: {bucket_name}")
    
    try:
        # Try to access the bucket
        s3.head_bucket(Bucket=bucket_name)
        print(f"Successfully connected to bucket: {bucket_name}")
        
        # List some objects in the bucket
        print("\nListing up to 5 objects in the bucket:")
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"- {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("Bucket is empty")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error accessing bucket: {error_code} - {error_message}")
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_s3_connection() 