"""
Lists all folders and their contents in a specified S3 bucket.
- Shows top-level folders and their files.
- Also lists files directly under the bucket root.
- Logs all output and handles AWS errors.
"""
import boto3
import logging
from botocore.exceptions import ClientError, BotoCoreError

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='🔍 %(levelname)s: %(message)s')

# --- Config ---
s3 = boto3.client('s3')
bucket_name = '24030142014'

try:
    logging.info(f"📂 Listing folders and contents in bucket: {bucket_name}")

    # --- 1. Get all top-level folders (prefixes)
    top_level = s3.list_objects_v2(Bucket=bucket_name, Delimiter='/')
    prefixes = top_level.get('CommonPrefixes', [])

    if not prefixes:
        logging.info("No folders found at root level.")
    else:
        for prefix in prefixes:
            folder = prefix['Prefix']
            logging.info(f"\n📁 Folder: {folder}")

            # --- 2. List contents inside each folder
            contents = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder)
            for obj in contents.get('Contents', []):
                if obj['Key'] != folder:  # Skip the folder marker itself
                    size = obj['Size']
                    modified = obj['LastModified']
                    logging.info(f"   └── 🗂️ {obj['Key']} | {size} bytes | Modified: {modified}")

    # --- 3. List files directly under root (not in folders)
    root_files = [
        obj for obj in top_level.get('Contents', [])
        if '/' not in obj['Key']
    ]
    if root_files:
        logging.info("\n📄 Files directly under root:")
        for obj in root_files:
            logging.info(f" - {obj['Key']} | {obj['Size']} bytes | Modified: {obj['LastModified']}")
    else:
        logging.info("\nNo files found in bucket root.")

except (ClientError, BotoCoreError) as e:
    logging.critical(f"🛑 AWS Error: {e}")
except Exception as ex:
    logging.critical(f"🛑 Unexpected Error: {ex}")
