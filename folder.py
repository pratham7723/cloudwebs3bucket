"""
Creates a folder (prefix) in S3 and uploads specified local files to it.
- Demonstrates how to create a folder marker in S3.
- Uploads a hardcoded list of local files to the new S3 folder.
"""
import boto3
import os

# --- Setup ---
s3 = boto3.client('s3')
bucket_name = '24030142014'
folder_name = 'folder_creation/'  # S3 folder

# Local files to upload (adjust full paths)
local_files = [
    '/Volumes/study/cloud web/aws 4th july/stockmarket.jpg',
    '/Volumes/study/cloud web/aws 4th july/shopycloud.jpg'
]

# --- 1. Create Folder ---
s3.put_object(Bucket=bucket_name, Key=folder_name)
print(f"✅ Created folder '{folder_name}' in bucket '{bucket_name}'")

# --- 2. Upload Files ---
for file_path in local_files:
    file_name = os.path.basename(file_path)
    s3_key = folder_name + file_name
    s3.upload_file(file_path, bucket_name, s3_key)
    print(f"📤 Uploaded '{file_name}' to '{s3_key}'")
