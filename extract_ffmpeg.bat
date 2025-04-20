@echo off
echo Current directory: %CD%
echo Creating bin directory...
mkdir ..\backend\bin 2>nul

echo Extracting FFmpeg...
powershell -command "Expand-Archive -Path '%CD%\ffmpeg.zip' -DestinationPath '..\backend\bin' -Force"

echo Showing content of bin directory...
dir ..\backend\bin

echo Done! 