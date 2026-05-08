@echo off
rem Wrapper so save works without changing PowerShell execution policy.
rem Usage:  save              (saves with a timestamp message)
rem         save "your message"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0save.ps1" %*
