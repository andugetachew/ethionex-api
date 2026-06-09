@echo off
setlocal enabledelayedexpansion

set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_FILE=C:\Users\HP\ethionex-api\backups\ethionex_db_%TIMESTAMP:.=%.sql
set DB_NAME=ethionex_db
set DB_USER=postgres
set DB_PASSWORD=perfectionist
set DB_HOST=localhost

echo Creating backup: %BACKUP_FILE%

pg_dump --dbname=postgresql://%DB_USER%:%DB_PASSWORD%@%DB_HOST%/%DB_NAME% > %BACKUP_FILE%

if %errorlevel% equ 0 (
    echo Backup completed successfully!
    echo Compressing backup...
    powershell -Command "Compress-Archive -Path %BACKUP_FILE% -DestinationPath %BACKUP_FILE%.zip"
    del %BACKUP_FILE%
    echo Backup saved to %BACKUP_FILE%.zip
) else (
    echo Backup failed!
)