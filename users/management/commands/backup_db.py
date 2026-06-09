from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import os
from datetime import datetime
import gzip
import shutil


class Command(BaseCommand):
    help = "Create database backup"

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(settings.BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        backup_file = os.path.join(backup_dir, f"ethionex_db_{timestamp}.sql")

        db_settings = settings.DATABASES["default"]
        db_name = db_settings["NAME"]
        db_user = db_settings["USER"]
        db_password = db_settings["PASSWORD"]
        db_host = db_settings.get("HOST", "localhost")

        command = f"PGPASSWORD={db_password} pg_dump -h {db_host} -U {db_user} {db_name} > {backup_file}"

        self.stdout.write(f"Creating backup: {backup_file}")

        try:
            subprocess.run(command, shell=True, check=True)

            # Compress backup
            with open(backup_file, "rb") as f_in:
                with gzip.open(f"{backup_file}.gz", "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            os.remove(backup_file)

            self.stdout.write(self.style.SUCCESS(f"Backup created: {backup_file}.gz"))

            # Clean old backups (keep only last 7)
            self.cleanup_old_backups(backup_dir)

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"Backup failed: {e}"))

    def cleanup_old_backups(self, backup_dir, keep=7):
        """Keep only last 'keep' backups"""
        import datetime

        files = [
            os.path.join(backup_dir, f)
            for f in os.listdir(backup_dir)
            if f.endswith(".gz")
        ]
        files.sort(key=os.path.getmtime)

        for file in files[:-keep]:
            os.remove(file)
            self.stdout.write(f"Deleted old backup: {os.path.basename(file)}")
