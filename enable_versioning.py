"""
Enables versioning on a specified S3 bucket using boto3.
- Simple script to turn on S3 versioning for backup/version history.
"""
import boto3

s3 = boto3.client('s3')
bucket_name = '24030142014'

response = s3.put_bucket_versioning(
    Bucket=bucket_name,
    VersioningConfiguration={'Status': 'Enabled'}
)

print("✅ Versioning enabled for bucket:", bucket_name)
