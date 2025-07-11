"""
Uploads a local file to a specified S3 bucket.
- Simple example of S3 file upload using boto3.
"""
import boto3

# Step 1: Initialize the S3 client
s3 = boto3.client('s3')

# Step 2: Specify bucket name (must already exist)
bucket_name = '24030142014'  # change to your bucket name

# Step 3: File to upload
file_path = 'text.txt'  # full path to file
object_name = 'note.txt'  # what it will be called in S3

# Step 4: Upload file
s3.upload_file(file_path, bucket_name, object_name)
print(f"✅ Uploaded '{file_path}' to S3 bucket '{bucket_name}' as '{object_name}'.")
