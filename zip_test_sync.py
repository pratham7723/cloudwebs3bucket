"""
Watches a local folder for file changes.
On file modification:
- Uploads the changed file to S3.
- Creates a timestamped ZIP backup and uploads it to S3.
- Logs all actions to a debug log file.
- Minimal version of the main sync script for testing ZIP backup logic.
"""
import os
import time
import boto3
import zipfile
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Setup ---
bucket_name = '24030142014'
watch_folder = '/Volumes/study/cloud web/aws 4th july/'
log_path = os.path.join(watch_folder, 'zip_debug.log')
zip_output_folder = os.path.join(watch_folder, 'zips/')
s3 = boto3.client('s3')

# --- Logging ---
logging.basicConfig(
    filename=log_path,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Event Handler ---
class ZipUploadHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        filename = os.path.basename(filepath)

        if not filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.mpeg', '.doc', '.txt')):
            logging.info(f"Skipped unsupported file: {filename}")
            return

        try:
            # Upload raw file
            s3_key_raw = f'live-sync/{filename}'
            s3.upload_file(filepath, bucket_name, s3_key_raw)
            logging.info(f"Uploaded RAW file → {s3_key_raw}")
        except Exception as e:
            logging.error(f"Failed RAW upload: {e}")
            return

        try:
            # Create ZIP
            os.makedirs(zip_output_folder, exist_ok=True)
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            zip_name = f"{os.path.splitext(filename)[0]}_{timestamp}.zip"
            zip_path = os.path.join(zip_output_folder, zip_name)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(filepath, arcname=filename)

            logging.info(f"Created ZIP: {zip_path}")
        except Exception as e:
            logging.error(f"ZIP creation failed: {e}")
            return

        try:
            # Upload ZIP
            with open(zip_path, 'rb') as f:
                s3.put_object(Bucket=bucket_name, Key=f'live-sync/backups/{zip_name}', Body=f)
            logging.info(f"Uploaded ZIP → live-sync/backups/{zip_name}")
        except Exception as e:
            logging.error(f"ZIP upload failed: {e}")

# --- Main Watcher ---
if __name__ == "__main__":
    logging.info("Started minimal ZIP sync test.")
    observer = Observer()
    observer.schedule(ZipUploadHandler(), watch_folder, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Stopped by user.")
    observer.join()
