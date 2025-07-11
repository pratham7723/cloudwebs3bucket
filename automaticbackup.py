"""
Periodically (every BACKUP_INTERVAL seconds) backs up all supported files from a local folder to S3.
- Each backup is stored in a timestamped S3 folder under 'auto-backups/'.
- Logs upload results and errors.
- Designed to run continuously as an auto-backup cronjob.
"""
import boto3
import os
import time
import logging
from datetime import datetime
from botocore.exceptions import BotoCoreError, ClientError

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='🔍 %(levelname)s: %(message)s')

# --- Config ---
s3 = boto3.client('s3')
bucket_name = '24030142014'
local_folder = '/Volumes/study/cloud web/aws 4th july/'
backup_prefix = 'auto-backups/'
allowed_extensions = ('.pdf', '.jpg', '.jpeg', '.mpeg', '.doc', '.txt')

# Backup interval (in seconds) — 3600 = every 1 hour
BACKUP_INTERVAL = 120  # Change to e.g., 600 for every 10 minutes

def run_backup():
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    s3_backup_folder = f"{backup_prefix}{timestamp}/"
    files_uploaded = 0

    try:
        s3.put_object(Bucket=bucket_name, Key=s3_backup_folder)
        logging.info(f"\n🕒 Starting backup at {timestamp}")
        logging.info(f"📁 S3 folder: {s3_backup_folder}")

        for file in os.listdir(local_folder):
            full_path = os.path.join(local_folder, file)

            if os.path.isfile(full_path) and file.lower().endswith(allowed_extensions):
                s3_key = s3_backup_folder + file
                try:
                    s3.upload_file(full_path, bucket_name, s3_key)
                    logging.info(f"✅ Uploaded: {file} → {s3_key}")
                    files_uploaded += 1
                except (ClientError, BotoCoreError) as e:
                    logging.error(f"❌ Failed to upload '{file}': {e}")

        if files_uploaded == 0:
            logging.warning("⚠️ No valid files found to upload.")
        else:
            logging.info(f"✅ Backup completed. {files_uploaded} file(s) uploaded.\n")

    except Exception as e:
        logging.critical(f"🛑 Backup failed: {e}")

# --- Run forever with interval ---
if __name__ == "__main__":
    logging.info("🔄 Auto-backup script started. Press Ctrl+C to stop.")
    try:
        while True:
            run_backup()
            time.sleep(BACKUP_INTERVAL)
    except KeyboardInterrupt:
        logging.info("🛑 Auto-backup script stopped manually.")
