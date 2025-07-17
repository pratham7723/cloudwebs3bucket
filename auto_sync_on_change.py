"""
Watches a local folder for file changes using watchdog.
On file modification:
- Uploads the changed file to S3 (main sync).
- Creates a ZIP backup of the file and uploads it to S3, using S3 versioning for backup history.
- Maintains logs locally and uploads logs to S3.
- Handles file deletions by removing them from S3.
"""
import os
import time
import boto3
import zipfile
import logging
from datetime import datetime
from collections import defaultdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from botocore.exceptions import ClientError, BotoCoreError

# --- Config ---
bucket_name = '24030142014'
watch_folder = '/Volumes/study/cloud web/aws 4th july/'
log_file_path = os.path.join(watch_folder, 's3_sync.log')
zip_output_folder = os.path.join(watch_folder, 'zips/')
s3_base_folder = 'live-sync/'
backup_folder = s3_base_folder + 'backups/'
log_s3_key = s3_base_folder + "logs/s3_sync.log"
allowed_extensions = ('.pdf', '.jpg', '.jpeg', '.mpeg', '.doc', '.txt', '.py')

s3 = boto3.client('s3')

# --- Logging ---
logger = logging.getLogger("S3Sync")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("🔍 %(asctime)s - %(levelname)s: %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler(log_file_path)
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# --- Upload Log to S3 ---
def upload_log_to_s3():
    try:
        s3.upload_file(log_file_path, bucket_name, log_s3_key)
        logger.info(f"📝 Log uploaded to S3: {log_s3_key}")
    except Exception as e:
        logger.error(f"❌ Failed to upload log to S3: {e}")

# --- Ensure S3 folders exist ---
def ensure_s3_folder(key):
    try:
        s3.put_object(Bucket=bucket_name, Key=key)
        logger.info(f"📁 Ensured S3 folder: {key}")
    except Exception as e:
        logger.error(f"❌ Couldn't create S3 folder {key}: {e}")

ensure_s3_folder(s3_base_folder + 'logs/')
ensure_s3_folder(s3_base_folder + 'backups/')

def ensure_bucket_versioning(bucket_name):
    s3_resource = boto3.resource('s3')
    bucket_versioning = s3_resource.BucketVersioning(bucket_name)
    if bucket_versioning.status != 'Enabled':
        bucket_versioning.enable()
        logger.info(f"✅ Enabled versioning on bucket: {bucket_name}")
    else:
        logger.info(f"ℹ️ Versioning already enabled on bucket: {bucket_name}")

ensure_bucket_versioning(bucket_name)

# --- Handler ---
class S3SyncHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_event_time = defaultdict(float)

    def on_modified(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        filename = os.path.basename(filepath)
        s3_key = s3_base_folder + filename
        now = time.time()

        if now - self.last_event_time[s3_key] < 5:
            return  # debounce

        self.last_event_time[s3_key] = now
        self.upload_main_and_backup(filepath)

    def upload_main_and_backup(self, filepath):
        filename = os.path.basename(filepath)
        name_part, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in allowed_extensions:
            logger.info(f"⏭️ Skipped unsupported file: {filename}")
            return

        if not os.path.exists(filepath):
            logger.error(f"❌ File not found: {filepath}")
            return

        logger.info(f"➡️ Triggered sync for: {filepath}")

        # --- Upload main file ---
        try:
            s3.upload_file(filepath, bucket_name, s3_base_folder + filename)
            logger.info(f"✅ Uploaded main file → {s3_base_folder + filename}")
        except Exception as e:
            logger.error(f"❌ Main file upload failed: {e}")

        # --- Create ZIP ---
        try:
            os.makedirs(zip_output_folder, exist_ok=True)
            zip_name = f"{name_part}.zip"
            zip_path = os.path.join(zip_output_folder, zip_name)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(filepath, arcname=filename)

            logger.info(f"📦 Created ZIP: {zip_path}")
        except Exception as e:
            logger.error(f"❌ ZIP creation failed: {e}")
            return

        # --- Upload ZIP to S3 ---
        try:
            with open(zip_path, 'rb') as f:
                s3.put_object(Bucket=bucket_name, Key=backup_folder + zip_name, Body=f)
            logger.info(f"📤 Uploaded ZIP → S3: {backup_folder + zip_name}")
        except Exception as e:
            logger.error(f"❌ ZIP upload failed: {e}")

        upload_log_to_s3()

    def on_deleted(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)
        s3_key = s3_base_folder + filename
        try:
            s3.delete_object(Bucket=bucket_name, Key=s3_key)
            logger.info(f"🗑️ Deleted main file from S3: {s3_key}")
        except Exception as e:
            logger.error(f"❌ Failed to delete from S3: {e}")
        upload_log_to_s3()

# --- Run Watcher ---
if __name__ == "__main__":
    logger.info(f"🔄 Watching folder: {watch_folder}")
    event_handler = S3SyncHandler()
    observer = Observer()
    observer.schedule(event_handler, watch_folder, recursive=False)
    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("🛑 Sync stopped.")
    observer.join()
