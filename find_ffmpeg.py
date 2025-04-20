#!/usr/bin/env python
"""
Utility script to find ffmpeg in a Heroku environment
"""

import os
import subprocess
import platform
import glob

def run_cmd(cmd):
    """Run a command and return output"""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return proc.stdout.strip(), proc.stderr.strip(), proc.returncode
    except Exception as e:
        return "", str(e), -1

def find_executable(name):
    """Try to find an executable through various methods"""
    print(f"Looking for {name}...")
    
    # Method 1: Check common locations
    common_locations = [
        '/app/vendor/ffmpeg/bin',
        '/app/vendor/ffmpeg',
        '/usr/bin',
        '/usr/local/bin',
        '/app/bin',
        '/app/.heroku/vendor/bin',
        '/app/.apt/usr/bin'
    ]
    
    for loc in common_locations:
        path = os.path.join(loc, name)
        if os.path.exists(path):
            print(f"Found at {path}")
            
            # Check if it's executable
            if os.access(path, os.X_OK):
                print(f"{path} is executable")
            else:
                print(f"{path} exists but is not executable")
                
            # Try running it
            out, err, rc = run_cmd(f"{path} -version")
            if rc == 0:
                print(f"Successfully ran {path} -version")
                print(out.split('\n')[0] if out else "No output")
            else:
                print(f"Failed to run {path} -version: {err}")
    
    # Method 2: Use 'which'
    out, err, rc = run_cmd(f"which {name}")
    if rc == 0 and out:
        print(f"Found via 'which': {out}")
        
        # Try running it
        out, err, rc = run_cmd(f"{out} -version")
        if rc == 0:
            print(f"Successfully ran version check: {out.split('\n')[0] if out else 'No output'}")
        else:
            print(f"Failed to run version check: {err}")
    else:
        print(f"Not found via 'which': {err}")
    
    # Method 3: Use 'find'
    out, err, rc = run_cmd(f"find /app -name {name} -type f 2>/dev/null")
    if rc == 0 and out:
        print(f"Found via 'find':")
        for path in out.split('\n'):
            if path:
                print(f"  {path}")
                # Try running it
                out2, err2, rc2 = run_cmd(f"{path} -version")
                if rc2 == 0:
                    print(f"  Successfully ran version check: {out2.split('\n')[0] if out2 else 'No output'}")
                else:
                    print(f"  Failed to run version check: {err2}")
    else:
        print("Not found via 'find' or find command failed")
    
    # Method 4: Check PATH
    print("\nChecking PATH environment:")
    path_dirs = os.environ.get('PATH', '').split(':')
    for p in path_dirs:
        print(f"- {p}")
        # Check if executable exists in this path
        exe_path = os.path.join(p, name)
        if os.path.exists(exe_path):
            print(f"  Found {name} at {exe_path}")
    
    # Method 5: Check with glob for potential variation
    print("\nChecking with glob pattern:")
    patterns = [
        f"/app/**/{name}",
        f"/usr/**/{name}",
        f"**/{name}"
    ]
    for pattern in patterns:
        try:
            files = glob.glob(pattern, recursive=True)
            if files:
                print(f"Found with pattern '{pattern}':")
                for f in files:
                    print(f"  {f}")
        except Exception as e:
            print(f"Error with glob pattern '{pattern}': {e}")
    
    # Print system info
    print("\nSystem Information:")
    print(f"Platform: {platform.platform()}")
    print(f"Python version: {platform.python_version()}")
    print(f"Current directory: {os.getcwd()}")
    
    # Try direct command
    out, err, rc = run_cmd(f"{name} -version")
    if rc == 0:
        print(f"\nDirect command '{name} -version' works:")
        print(out.split('\n')[0] if out else "No output") 
    else:
        print(f"\nDirect command '{name} -version' failed: {err}")
    
    # Check other Heroku specific locations
    print("\nChecking Heroku-specific directories:")
    for root_dir in ['/app', '/usr']:
        try:
            for root, dirs, files in os.walk(root_dir, topdown=True, followlinks=False):
                # Limit depth to reduce output
                depth = root.count(os.path.sep) - root_dir.count(os.path.sep)
                if depth > 3:  # Don't go too deep
                    dirs[:] = []
                    continue
                    
                # Check if the executable is in this directory
                if name in files:
                    path = os.path.join(root, name)
                    print(f"Found at {path}")
                    
                    # Check if it's executable
                    if os.access(path, os.X_OK):
                        print(f"{path} is executable")
                    else:
                        print(f"{path} exists but is not executable")
        except Exception as e:
            print(f"Error checking {root_dir}: {e}")

if __name__ == "__main__":
    print("Starting ffmpeg search...")
    find_executable("ffmpeg")
    print("\n" + "="*50 + "\n")
    print("Starting ffprobe search...")
    find_executable("ffprobe") 