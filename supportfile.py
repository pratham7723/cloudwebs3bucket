"""
Uploads all supported files from a local directory to a specified S3 folder (prefix).
- Creates the S3 folder if missing.
- Filters files by allowed extensions.
- Uploads valid files, logs results, and lists unsupported files.
- Handles AWS and local errors gracefully.
"""
import boto3
import os
import logging
from botocore.exceptions import BotoCoreError, ClientError

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='🔍 %(levelname)s: %(message)s')

# --- Config ---
s3 = boto3.client('s3')
bucket_name = '24030142014'
folder_name = 'documents/'  # S3 folder (prefix)
local_folder = '/Volumes/study/cloud web/aws 4th july/'  # Local directory
allowed_extensions = ('.pdf', '.jpg', '.jpeg', '.mpeg', '.doc', '.txt', '.py')

unsupported_files = []

try:
    # --- 1. Create Folder in S3 ---
    s3.put_object(Bucket=bucket_name, Key=folder_name)
    logging.info(f"Created folder '{folder_name}' in bucket '{bucket_name}'")

    # --- 2. Check Local Folder Exists ---
    if not os.path.exists(local_folder):
        logging.error(f"Local folder does not exist: {local_folder}")
        exit(1)

    # --- 3. Gather & Sort Valid Files ---
    all_files = os.listdir(local_folder)
    valid_files = []
    
    for f in all_files:
        full_path = os.path.join(local_folder, f)
        if os.path.isfile(full_path):
            if f.lower().endswith(allowed_extensions):
                valid_files.append(full_path)
            else:
                unsupported_files.append(f)

    if not valid_files:
        logging.warning("No matching files to upload.")
        exit(0)

    valid_files.sort(key=os.path.getmtime, reverse=True)

    # --- 4. Upload Valid Files to S3 ---
    files_uploaded = 0
    for full_path in valid_files:
        file_name = os.path.basename(full_path)
        s3_key = folder_name + file_name
        try:
            s3.upload_file(full_path, bucket_name, s3_key)
            mod_time = os.path.getmtime(full_path)
            logging.info(f"Uploaded '{file_name}' → S3:{s3_key} [Modified: {mod_time}]")
            files_uploaded += 1
        except (ClientError, BotoCoreError) as upload_err:
            logging.error(f"Failed to upload '{file_name}': {upload_err}")

    # --- 5. Summary ---
    if files_uploaded == 0:
        logging.warning("No files were uploaded.")
    else:
        logging.info(f"✅ Successfully uploaded {files_uploaded} file(s) to folder '{folder_name}'")

    # --- 6. Show Unsupported Files ---
    if unsupported_files:
        logging.info("📛 Unsupported files skipped:")
        for fname in unsupported_files:
            logging.info(f" - {fname}")

except (ClientError, BotoCoreError) as e:
    logging.critical(f"🛑 AWS Error: {e}")
except Exception as ex:
    logging.critical(f"🛑 Unexpected Error: {ex}")
