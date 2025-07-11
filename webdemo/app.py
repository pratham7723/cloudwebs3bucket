import os
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
import boto3
from botocore.exceptions import ClientError

app = Flask(__name__, static_folder='static', template_folder='templates')

# --- AWS S3 Config ---
BUCKET_NAME = os.environ.get('S3_BUCKET', '24030142014')
s3 = boto3.client('s3')

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/list-files')
def list_files():
    try:
        objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
        files = [obj['Key'] for obj in objects.get('Contents', [])]
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    folder = request.form.get('folder', '').strip()
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    # Clean up folder input
    if folder and not folder.endswith('/'):
        folder += '/'
    s3_key = f"{folder}{file.filename}" if folder else file.filename
    try:
        s3.upload_fileobj(file, BUCKET_NAME, s3_key)
        return jsonify({'success': True, 'filename': s3_key})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-file')
def get_file():
    key = request.args.get('key')
    if not key:
        return jsonify({'error': 'No key provided'}), 400
    try:
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        content = obj['Body'].read().decode('utf-8')
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/edit-file', methods=['POST'])
def edit_file():
    data = request.json
    key = data.get('key')
    content = data.get('content')
    if not key or content is None:
        return jsonify({'error': 'Missing key or content'}), 400
    try:
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=content.encode('utf-8'))
        return jsonify({'success': True, 'key': key})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download')
def download_file():
    key = request.args.get('key')
    if not key:
        return jsonify({'error': 'No key provided'}), 400
    try:
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        data = obj['Body'].read()
        content_type = obj.get('ContentType', 'application/octet-stream')
        # If ?download=1 is present, force download, else preview
        if request.args.get('download') == '1':
            return Response(data, headers={
                'Content-Type': content_type,
                'Content-Disposition': f'attachment; filename="{os.path.basename(key)}"'
            })
        else:
            return Response(data, headers={
                'Content-Type': content_type
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-file', methods=['POST'])
def delete_file():
    data = request.json
    key = data.get('key')
    if not key:
        return jsonify({'error': 'No key provided'}), 400
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=key)
        return jsonify({'success': True, 'key': key})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-versions')
def list_versions():
    key = request.args.get('key')
    if not key:
        return jsonify({'error': 'No key provided'}), 400
    try:
        versions = s3.list_object_versions(Bucket=BUCKET_NAME, Prefix=key)
        version_list = []
        for v in versions.get('Versions', []):
            if v['Key'] == key:
                version_list.append({
                    'VersionId': v['VersionId'],
                    'IsLatest': v['IsLatest'],
                    'LastModified': v['LastModified'].isoformat(),
                    'Size': v['Size']
                })
        return jsonify({'versions': version_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    log_path = os.path.join(os.path.dirname(__file__), '..', 's3_sync.log')
    try:
        with open(log_path, 'r') as f:
            log_content = f.read()
        return jsonify({'log': log_content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/versioning')
def versioning_status():
    try:
        response = s3.get_bucket_versioning(Bucket=BUCKET_NAME)
        status = response.get('Status', 'Disabled')
        return jsonify({'versioning': status})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-version')
def download_version():
    key = request.args.get('key')
    version_id = request.args.get('version_id')
    if not key or not version_id:
        return jsonify({'error': 'No key or version_id provided'}), 400
    try:
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=key, VersionId=version_id)
        data = obj['Body'].read()
        return Response(data, headers={
            'Content-Disposition': f'attachment; filename="{os.path.basename(key)}"'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-folders')
def list_folders():
    try:
        resp = s3.list_objects_v2(Bucket=BUCKET_NAME, Delimiter='/')
        prefixes = [p['Prefix'] for p in resp.get('CommonPrefixes', [])]
        return jsonify({'folders': prefixes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-folder', methods=['POST'])
def create_folder():
    data = request.json
    folder = data.get('folder', '').strip()
    if not folder:
        return jsonify({'error': 'No folder provided'}), 400
    if not folder.endswith('/'):
        folder += '/'
    try:
        # Check if folder exists
        resp = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=folder, Delimiter='/')
        if 'CommonPrefixes' in resp and any(p['Prefix'] == folder for p in resp['CommonPrefixes']):
            return jsonify({'error': 'Folder already exists'}), 400
        # Create folder marker
        s3.put_object(Bucket=BUCKET_NAME, Key=folder)
        return jsonify({'success': True, 'folder': folder})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True) 