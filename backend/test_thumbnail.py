#!/usr/bin/env python
"""
Test script for debugging thumbnail generation in True Vision.
This script simulates the thumbnail generation process from a local video file.
"""

import os
import sys
import django
import subprocess
import tempfile
from PIL import Image, ImageEnhance, ImageDraw
import io
from django.core.files.base import ContentFile

# Define ffmpeg path functions
def get_ffmpeg_path():
    """Get the path to the ffmpeg executable based on the project structure."""
    # Check multiple possible locations for ffmpeg
    possible_paths = [
        # Local development paths
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffmpeg.exe'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffmpeg'),
        # Standard Heroku paths
        '/app/vendor/ffmpeg/ffmpeg',
        '/usr/bin/ffmpeg',
        # Heroku buildpack location - most reliable for Heroku
        '/app/vendor/ffmpeg/bin/ffmpeg',
    ]
    
    # Check if any of the paths exist
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found ffmpeg at: {path}")
            return path
    
    # Fallback to system PATH
    print("Using ffmpeg from system PATH")
    return 'ffmpeg'

def get_ffprobe_path():
    """Get the path to the ffprobe executable based on the project structure."""
    # Check multiple possible locations for ffprobe
    possible_paths = [
        # Local development paths
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffprobe.exe'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', 'ffmpeg-6.1.1-essentials_build', 'bin', 'ffprobe'),
        # Standard Heroku paths
        '/app/vendor/ffmpeg/ffprobe',
        '/usr/bin/ffprobe',
        # Heroku buildpack location - most reliable for Heroku
        '/app/vendor/ffmpeg/bin/ffprobe',
    ]
    
    # Check if any of the paths exist
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found ffprobe at: {path}")
            return path
    
    # Fallback to system PATH
    print("Using ffprobe from system PATH")
    return 'ffprobe'

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from api.models import Video, CustomUser

def test_thumbnail_generation(video_path):
    """Test thumbnail generation from a local video file"""
    print(f"Testing thumbnail generation with video: {video_path}")
    
    # Check if the video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file {video_path} does not exist")
        return False
    
    print(f"Video file exists: {os.path.getsize(video_path)} bytes")
    
    # Create a temporary file for the thumbnail
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_thumb:
        temp_thumb_path = temp_thumb.name
    print(f"Created temporary thumbnail file: {temp_thumb_path}")
    
    # Try different timestamps
    timestamps = ['00:00:01', '00:00:03', '00:00:05', '00:00:10', '00:00:15', '00:00:20']
    success = False
    
    for timestamp in timestamps:
        try:
            print(f"Attempting thumbnail extraction at timestamp {timestamp}")
            # Try this timestamp
            cmd = [
                get_ffmpeg_path(),
                '-i', video_path,
                '-ss', timestamp,  # timestamp into the video
                '-vframes', '1',
                '-q:v', '2',  # Higher quality
                '-f', 'image2',
                '-y',  # Force overwrite if file exists
                temp_thumb_path
            ]
            print(f"Running FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Check if the file was created and has content
            if os.path.exists(temp_thumb_path) and os.path.getsize(temp_thumb_path) > 100:
                print(f"Thumbnail file created successfully: {os.path.getsize(temp_thumb_path)} bytes")
                
                # Check if the image is not just black
                img = Image.open(temp_thumb_path)
                extrema = img.convert("L").getextrema()
                print(f"Image extrema (min/max): {extrema}")
                
                # If min and max are too similar, the image is likely just one color (black)
                if extrema[1] - extrema[0] > 30:
                    success = True
                    print(f"Generated valid thumbnail at timestamp {timestamp}")
                    # Save the thumbnail for inspection
                    output_path = f"test_thumbnail_{timestamp.replace(':', '_')}.jpg"
                    img.save(output_path)
                    print(f"Saved test thumbnail to {output_path}")
                    break
                else:
                    print(f"Thumbnail at {timestamp} is too dark/uniform, trying next timestamp...")
            else:
                print(f"Thumbnail file is missing or too small: {os.path.exists(temp_thumb_path)}, {os.path.getsize(temp_thumb_path) if os.path.exists(temp_thumb_path) else 0}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating thumbnail at {timestamp}: {e}")
            print(f"FFMPEG stderr: {e.stderr}")
            print(f"FFMPEG stdout: {e.stdout}")
            continue
        except Exception as e:
            print(f"Unexpected error during thumbnail generation at {timestamp}: {str(e)}")
            continue
    
    # Clean up
    try:
        os.unlink(temp_thumb_path)
        print("Cleaned up temporary thumbnail file")
    except Exception as e:
        print(f"Error cleaning up temporary thumbnail file: {str(e)}")
    
    if success:
        print("Thumbnail generation test successful!")
    else:
        print("All thumbnail generation attempts failed")
    
    return success

def check_ffmpeg():
    """Check if FFmpeg is installed and working properly"""
    try:
        result = subprocess.run([get_ffmpeg_path(), '-version'], capture_output=True, text=True)
        print("FFmpeg version information:")
        print(result.stdout.split('\n')[0])
        return True
    except Exception as e:
        print(f"Error checking FFmpeg: {str(e)}")
        print("Please ensure FFmpeg is installed and available in your PATH")
        return False

if __name__ == "__main__":
    # Check if FFmpeg is available
    if not check_ffmpeg():
        sys.exit(1)
    
    # Get video path from command line argument or use a default
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        print("Usage: python test_thumbnail.py <path_to_video_file>")
        print("No video file specified, looking for test videos...")
        
        # Try to find sample videos in the media directory
        sample_paths = [
            'media/videos',
            '../media/videos',
            './media/videos',
            '/tmp'
        ]
        
        found = False
        for path in sample_paths:
            if os.path.exists(path):
                videos = [os.path.join(path, f) for f in os.listdir(path) 
                         if f.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.mkv'))]
                if videos:
                    video_path = videos[0]
                    print(f"Found video: {video_path}")
                    found = True
                    break
        
        if not found:
            print("No test videos found. Please specify a video file path.")
            sys.exit(1)
    
    # Test thumbnail generation
    test_thumbnail_generation(video_path) 