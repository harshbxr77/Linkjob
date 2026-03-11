@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File ".\launch-linkjob.ps1"
