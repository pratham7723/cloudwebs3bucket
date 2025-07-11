"""
Creates a new S3 bucket with the specified name using boto3.
- Prints confirmation after creation.
"""
import boto3

s3 = boto3.client('s3')
bucket_name = '24030142014'

# Create bucket
s3.create_bucket(Bucket=bucket_name)
print(f"Bucket '{bucket_name}' created.")
