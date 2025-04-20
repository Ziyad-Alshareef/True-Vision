import os
import zipfile
import shutil
from pathlib import Path

# Get the current working directory
cwd = Path.cwd()
# Define the paths
zip_path = cwd / 'ffmpeg-download' / 'ffmpeg.zip'
bin_dir = cwd / 'backend' / 'bin'

print(f"Current directory: {cwd}")
print(f"ZIP path: {zip_path}")
print(f"Bin directory: {bin_dir}")

# Create bin directory if it doesn't exist
os.makedirs(bin_dir, exist_ok=True)
print(f"Created bin directory: {bin_dir}")

# Extract the ZIP file
try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Get the top-level directory in the zip file (if any)
        top_dirs = {item.split('/')[0] for item in zip_ref.namelist() if '/' in item}
        print(f"Top-level directories in zip: {top_dirs}")
        
        # Extract all files
        print("Extracting files...")
        zip_ref.extractall(bin_dir)
        print("Extraction complete")
        
        # If there's a single top directory, move its contents up
        if len(top_dirs) == 1:
            top_dir = bin_dir / list(top_dirs)[0]
            print(f"Moving contents from {top_dir} to {bin_dir}")
            for item in os.listdir(top_dir):
                source = top_dir / item
                dest = bin_dir / item
                if os.path.isdir(source):
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, dest)
            print(f"Removing top directory: {top_dir}")
            shutil.rmtree(top_dir)
    
    print("Files in bin directory after extraction:")
    for item in os.listdir(bin_dir):
        print(f"  {item}")
    
    print("FFmpeg extraction completed successfully")
except Exception as e:
    print(f"Error extracting FFmpeg: {str(e)}") 