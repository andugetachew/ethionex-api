import os
import subprocess
from datetime import datetime
from django.conf import settings
import boto3
from botocore.exceptions import ClientError
import gzip


class DatabaseBackup:
    """Automated database backup to AWS S3 (or local)"""

    def __init__(self):
        self.db_name = settings.DATABASES["default"]["NAME"]
        self.db_user = settings.DATABASES["default"]["USER"]
        self.db_password = settings.DATABASES["default"]["PASSWORD"]
        self.db_host = settings.DATABASES["default"].get("HOST", "localhost")
        self.backup_dir = os.path.join(settings.BASE_DIR, "backups")

        # Create backup directory if not exists
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self):
        """Create database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"ethionex_db_{timestamp}.sql")

        # PostgreSQL backup command
        command = f"PGPASSWORD={self.db_password} pg_dump -h {self.db_host} -U {self.db_user} {self.db_name} > {backup_file}"

        try:
            subprocess.run(command, shell=True, check=True)
            print(f"Backup created: {backup_file}")

            # Compress backup
            compressed_file = f"{backup_file}.gz"
            with open(backup_file, "rb") as f_in:
                with gzip.open(compressed_file, "wb") as f_out:
                    f_out.writelines(f_in)

            os.remove(backup_file)
            print(f"Backup compressed: {compressed_file}")

            return compressed_file

        except subprocess.CalledProcessError as e:
            print(f"Backup failed: {e}")
            return None

    def upload_to_s3(self, file_path, bucket_name="ethionex-backups"):
        """Upload backup to AWS S3 (optional)"""
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )

            file_name = os.path.basename(file_path)
            s3_client.upload_file(file_path, bucket_name, f"database/{file_name}")
            print(f"Uploaded to S3: {file_name}")

            # Delete old backups (keep only last 30 days)
            self.cleanup_old_backups(bucket_name, s3_client)

        except ClientError as e:
            print(f"S3 upload failed: {e}")

    def cleanup_old_backups(self, bucket_name, s3_client, days=30):
        """Delete backups older than specified days"""
        import datetime

        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)

        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="database/")

        if "Contents" in response:
            for obj in response["Contents"]:
                if obj["LastModified"] < cutoff_date:
                    s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
                    print(f"Deleted old backup: {obj['Key']}")

    def cleanup_local_backups(self, days=7):
        """Delete local backups older than specified days"""
        import datetime

        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)

        for filename in os.listdir(self.backup_dir):
            file_path = os.path.join(self.backup_dir, filename)
            if os.path.getmtime(file_path) < cutoff_date.timestamp():
                os.remove(file_path)
                print(f"Deleted local backup: {filename}")


if __name__ == "__main__":
    backup = DatabaseBackup()
    backup_file = backup.create_backup()

    if backup_file:
        # Optional: Upload to S3
        # backup.upload_to_s3(backup_file)
        backup.cleanup_local_backups(days=7)
