"""
Demonstrates basic CRUD operations with AWS S3:
- Lists all buckets and objects in a specified bucket.
- Creates a local file if missing.
- Uploads (creates) the file to S3.
- Downloads (reads) the file from S3.
- Updates the file locally and re-uploads to S3.
- (Optional) Deletes the file from S3.
"""
import boto3
import os

# --- Setup ---
s3 = boto3.client('s3')
bucket_name = '24030142014'
file_path = '/Volumes/study/cloud web/aws 4th july/text/note.txt'
s3_key = 'note.txt'

# --- 1. LIST Buckets and Objects ---
print("📦 Your Buckets:")
buckets = s3.list_buckets()
for b in buckets['Buckets']:
    print(f" - {b['Name']}")

print(f"\n📂 Objects in '{bucket_name}':")
objects = s3.list_objects_v2(Bucket=bucket_name)
if 'Contents' in objects:
    for obj in objects['Contents']:
        print(f" - {obj['Key']}")
else:
    print(" (Empty)")

# --- 2. CREATE note.txt if missing ---
if not os.path.exists(file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        f.write("This is an auto-generated file.\n")
    print(f"📝 File created: {file_path}")

# --- 3. UPLOAD (CREATE in S3) ---
s3.upload_file(file_path, bucket_name, s3_key)
print(f"✅ Uploaded: {file_path} to S3 as '{s3_key}'")

# --- 4. DOWNLOAD (READ from S3) ---
download_path = f"/tmp/{s3_key}"
s3.download_file(bucket_name, s3_key, download_path)
print(f"📥 Downloaded from S3 to: {download_path}")

# --- 5. UPDATE (Modify local and re-upload) ---
with open(file_path, 'a') as f:
    f.write("\n[Updated via script]")
s3.upload_file(file_path, bucket_name, s3_key)
print("🔁 File updated locally and re-uploaded to S3.")

# --- 6. DELETE (Optional - Uncomment to use) ---
# s3.delete_object(Bucket=bucket_name, Key=s3_key)
# print("🗑️ File deleted from S3.")
