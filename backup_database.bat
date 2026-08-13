@echo off
setlocal enabledelayedexpansion

REM Windows MySQL Database Backup Script for IPCMS
echo Starting IPCMS MySQL Database Backup...

set BACKUP_DIR=database\backups
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

set DB_HOST=localhost
set DB_USER=root
set DB_NAME=hospital_management_system

for /f "tokens=2 delims==" %%i in ('wmic os get localdatetime /value') do set datetime=%%i
set TIMESTAMP=%datetime:~0,4%%datetime:~4,2%%datetime:~6,2%_%datetime:~8,2%%datetime:~10,2%%datetime:~12,2%
set BACKUP_FILE=%BACKUP_DIR%\ipcms_backup_%TIMESTAMP%.sql

echo Target Backup File: %BACKUP_FILE%
echo Running mysqldump for database %DB_NAME%...

REM Executes mysqldump (Uses MYSQL_PWD env var if provided, or prompts)
mysqldump -h %DB_HOST% -u %DB_USER% %DB_NAME% > "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Database backup created: %BACKUP_FILE%
) else (
    echo [ERROR] mysqldump failed with error code %ERRORLEVEL%
)
