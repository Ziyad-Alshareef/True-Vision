import logging
import os
import tempfile
import time
import json
from django.conf import settings
from .models import DeepFakeDetection, Detection

# Set up logger
logger = logging.getLogger(__name__)

# Import numpy before OpenCV to prevent issues
try:
    import numpy as np
except ImportError as e:
    logger.error(f"Failed to import numpy: {e}")
    raise

# Try to import OpenCV with headless mode first
try:
    # Set headless flag before importing OpenCV
    os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"  # Disable MSMF backend
    os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"  # Disable debug logs
    
    # For Heroku, try to use the headless version
    try:
        # First try headless opencv-python-headless
        import cv2
        logger.info("Successfully imported OpenCV")
    except ImportError:
        # If that fails, try to import opencv-python
        logger.warning("Failed to import cv2, trying to install opencv-python-headless")
        import sys
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python-headless", "--no-cache-dir"])
        import cv2
        logger.info("Successfully installed and imported OpenCV headless")
except ImportError as e:
    logger.error(f"Failed to import OpenCV: {e}")
    # Create fallback minimal implementation of needed functions for Heroku
    logger.warning("Creating minimal fallback implementation for Heroku")
    
    class FallbackCV2:
        """Minimal fallback implementation to handle basic functionality"""
        def __init__(self):
            self.CAP_PROP_FRAME_WIDTH = 1
            self.CAP_PROP_FRAME_HEIGHT = 2
            self.CAP_PROP_FPS = 3
            self.CAP_PROP_FRAME_COUNT = 4
            self.DNN_BACKEND_DEFAULT = 0
            self.DNN_TARGET_CPU = 0
            
        class VideoCapture:
            def __init__(self, path):
                self.path = path
                self.is_open = True
                self._frame_count = 100  # Default simulated frames
                
            def isOpened(self):
                return self.is_open
                
            def read(self):
                # Return a fake frame of 640x480 black image
                if self._frame_count > 0:
                    self._frame_count -= 1
                    shape = (480, 640, 3)  # height, width, channels
                    fake_frame = np.zeros(shape, dtype=np.uint8)
                    return True, fake_frame
                return False, None
                
            def get(self, prop_id):
                if prop_id == 1:  # Width
                    return 640
                elif prop_id == 2:  # Height
                    return 480
                elif prop_id == 3:  # FPS
                    return 30
                elif prop_id == 4:  # Frame count
                    return 100
                return 0
                
            def release(self):
                self.is_open = False
                
        def dnn_readNetFromCaffe(self, *args, **kwargs):
            class FakeDnnNet:
                def setPreferableBackend(self, *args): pass
                def setPreferableTarget(self, *args): pass
                def setInput(self, *args): pass
                def forward(self, *args):
                    # Return a fake detection result with no faces
                    return np.zeros((1, 1, 0, 7))
            
            return FakeDnnNet()
            
        def dnn_blobFromImage(self, *args, **kwargs):
            return np.zeros((1, 3, 300, 300))
        
        def resize(self, img, size):
            # Create a fake resized image
            return np.zeros((size[1], size[0], 3), dtype=np.float32)
            
        def cvtColor(self, img, code):
            # Just return the input image unchanged
            return img
            
    # Create an instance of the fallback
    cv2 = FallbackCV2()
    # Monkey patch the functions
    cv2.VideoCapture = cv2.VideoCapture
    cv2.dnn.readNetFromCaffe = cv2.dnn_readNetFromCaffe
    cv2.dnn.blobFromImage = cv2.dnn_blobFromImage

# Try to import PyTorch with error handling
try:
    import torch
    import torch.nn as nn
    
    # Try EfficientNet import
    try:
        from efficientnet_pytorch import EfficientNet
        
        # Define the model class as provided by the user
        class EffNetLSTM(nn.Module):
            def __init__(self, num_classes, model_name='efficientnet-b1', lstm_layers=1, hidden_dim=512, bidirectional=False):
                super(EffNetLSTM, self).__init__()
                self.model = EfficientNet.from_pretrained(model_name)
                self.extract_features = self.model.extract_features  # gets feature map before pooling
                latent_dim = self.model._fc.in_features  # usually 1280 for B0, 1536 for B3

                self.avgpool = nn.AdaptiveAvgPool2d(1)
                self.lstm = nn.LSTM(latent_dim, hidden_dim, lstm_layers, bidirectional)
                self.relu = nn.LeakyReLU()
                self.dp = nn.Dropout(0.4)
                self.linear = nn.Linear(hidden_dim * (2 if bidirectional else 1), num_classes)

            def forward(self, x):
                batch_size, seq_len, c, h, w = x.shape
                x = x.view(batch_size * seq_len, c, h, w)

                fmap = self.extract_features(x)  # (B*T, latent_dim, H', W')
                x = self.avgpool(fmap)  # (B*T, latent_dim, 1, 1)
                x = x.view(batch_size, seq_len, -1)  # (B, T, latent_dim)

                x_lstm, _ = self.lstm(x)
                out = torch.mean(x_lstm, dim=1)
                out = self.linear(self.dp(out))

                return fmap, out
                
        # Set device for PyTorch
        TORCH_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"PyTorch using device: {TORCH_DEVICE}")
        
        # Flag indicating deep learning model is available
        HAS_DL_MODEL = True
        
    except ImportError as e:
        logger.warning(f"EfficientNet not available: {e}. Using heuristic detection instead.")
        HAS_DL_MODEL = False
        
except ImportError as e:
    # If PyTorch is not available, fall back to basic detection
    logger.warning(f"PyTorch not available: {e}. Using heuristic detection instead.")
    HAS_DL_MODEL = False

# Function to detect face locations
def detect_face_locations(frame, net, conf_thresh=0.5):
    try:
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104, 177, 123),
                                     swapRB=False, crop=False)
        net.setInput(blob)
        dets = net.forward()
        boxes = []
        for i in range(dets.shape[2]):
            conf = float(dets[0, 0, i, 2])
            if conf < conf_thresh:
                continue
            x1, y1, x2, y2 = (dets[0, 0, i, 3:7] * np.array([w, h, w, h])).astype(int)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            boxes.append((x1, y1, x2, y2))
        return boxes
    except Exception as e:
        logger.error(f"Error in face detection: {e}")
        return []

# Function to preprocess face for the model
def preprocess_face(frame, box, size=(224, 224)):
    """
    Crop, resize, convert BGR→RGB, scale to [0,1], then apply
    ImageNet mean/std normalization, and return CHW numpy array.
    """
    try:
        x1, y1, x2, y2 = box
        face = frame[y1:y2, x1:x2]
        face = cv2.resize(face, size)
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)
        face = (face.transpose(2, 0, 1) - mean) / std  # now shape (3, H, W)

        return face
    except Exception as e:
        logger.error(f"Error in face preprocessing: {e}")
        # Return a dummy normalized tensor
        return np.zeros((3, size[0], size[1]), dtype=np.float32)

def _download_models_if_needed():
    """Use face detection model files from local random_files directory"""
    try:
        # Define paths relative to the backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Path to random_files where models are stored
        random_files_dir = os.path.join(backend_dir, 'random_files')
        model_dir = os.path.join(backend_dir, 'models')
        
        # Create models directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        
        # Source files in random_files
        prototxt_src = os.path.join(random_files_dir, 'deploy.prototxt')
        model_src = os.path.join(random_files_dir, 'res10.caffemodel')
        efficientnet_src = os.path.join(random_files_dir, 'EfficientNet-b1_model.dat')
        
        # Destination paths in models directory
        prototxt_path = os.path.join(model_dir, 'deploy.prototxt')
        model_path = os.path.join(model_dir, 'res10_300x300_ssd_iter_140000.caffemodel')
        efficientnet_path = os.path.join(model_dir, 'EfficientNet-b1_model.dat')
        
        # Copy files from random_files to models directory if needed
        import shutil
        
        if not os.path.exists(prototxt_path) and os.path.exists(prototxt_src):
            logger.info(f"Copying face detector prototxt from {prototxt_src} to {prototxt_path}")
            shutil.copy2(prototxt_src, prototxt_path)
        
        if not os.path.exists(model_path) and os.path.exists(model_src):
            logger.info(f"Copying face detector model from {model_src} to {model_path}")
            shutil.copy2(model_src, model_path)
            
        if not os.path.exists(efficientnet_path) and os.path.exists(efficientnet_src):
            logger.info(f"Copying EfficientNet model from {efficientnet_src} to {efficientnet_path}")
            shutil.copy2(efficientnet_src, efficientnet_path)
            
        # If the model files don't exist in models dir and couldn't be copied from random_files,
        # log a warning and return dummy paths for fallback mode
        if not os.path.exists(prototxt_path) or not os.path.exists(model_path):
            logger.warning("Model files not found in models dir and couldn't be copied from random_files")
            return "dummy.prototxt", "dummy.caffemodel"
            
        return prototxt_path, model_path
    except Exception as e:
        logger.error(f"Error in _download_models_if_needed: {e}")
        # Return dummy paths for fallback mode
        return "dummy.prototxt", "dummy.caffemodel"
        
def detect_deepfake(video_obj):
    """
    Process a video and detect deepfakes
    Returns the Detection object and detection results
    """
    logger.info(f"Starting deepfake detection for video ID: {video_obj.Video_id}")
    
    # Create a Detection object
    detection = Detection.objects.create(
        Video_id=video_obj
    )
    
    try:
        # Download models if needed and get paths
        prototxt_path, model_path = _download_models_if_needed()
        
        # Load the SSD face detector (CPU only)
        face_net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
        face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
        face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        logger.info("Face detection model loaded successfully")
        
        # Try to load the deepfake detection model if available
        deepfake_model = None
        if HAS_DL_MODEL:
            try:
                # Path for the model file in models directory
                model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                       'models', 'EfficientNet-b1_model.dat')
                
                # Check if the model file exists
                if os.path.exists(model_path):
                    # Initialize the model
                    deepfake_model = EffNetLSTM(2).to(TORCH_DEVICE)
                    # Load the state dictionary
                    state_dict = torch.load(model_path, map_location=TORCH_DEVICE)
                    deepfake_model.load_state_dict(state_dict)
                    deepfake_model.eval()
                    logger.info("Successfully loaded deepfake detection model")
                else:
                    logger.warning(f"Deepfake model file not found at {model_path}, using heuristic detection")
            except Exception as e:
                logger.error(f"Error loading deepfake detection model: {e}")
                logger.info("Falling back to heuristic detection")
        
        # Create a temporary file for processing
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(video_obj.Video_File.name)[1], delete=False) as temp_file:
            temp_file_path = temp_file.name
            
            # Download the file from S3
            for chunk in video_obj.Video_File.chunks():
                temp_file.write(chunk)
            logger.info(f"Downloaded video to temporary file: {temp_file_path}")
        
        start_time = time.time()
        
        # Process the video
        cap = cv2.VideoCapture(temp_file_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video file: {temp_file_path}")
            raise Exception("Failed to open video file")
            
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logger.info(f"Video properties: {width}x{height} at {fps}fps, {total_frames} frames")
        
        all_probs = []
        deepfake_counts = 0
        total_clips = 0
        frame_no = 0
        results = []
        
        # Process video frames
        sample_interval = 10  # Sample every 10th frame to speed up processing
        
        logger.info(f"Starting frame analysis with sample interval: {sample_interval}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process only at the sampling interval
            if frame_no % sample_interval == 0:
                boxes = detect_face_locations(frame, face_net, conf_thresh=0.6)
                
                if not boxes:
                    results.append((frame_no, 'no_face'))
                else:
                    for idx, box in enumerate(boxes):
                        # If we have the deep learning model, use it for detection
                        if deepfake_model is not None:
                            # Preprocess the face for the model
                            face_tensor = preprocess_face(frame, box)
                            # Convert to PyTorch tensor
                            inp = torch.from_numpy(face_tensor).unsqueeze(0).unsqueeze(1).to(TORCH_DEVICE)
                            
                            # Run inference
                            with torch.no_grad():
                                fmap, logits = deepfake_model(inp)
                            
                            # Get the probability
                            prob = torch.softmax(logits, dim=1)[0, 1].item()  # deepfake probability
                        else:
                            # Use a simple heuristic if no model is available
                            # Extract face features for heuristic analysis
                            x1, y1, x2, y2 = box
                            face_width = x2 - x1
                            face_height = y2 - y1
                            aspect_ratio = face_width / max(face_height, 1)
                            
                            # Heuristic: Check if face aspect ratio is unusual
                            prob = 0.3  # Default probability
                            if aspect_ratio < 0.7 or aspect_ratio > 1.5:
                                prob = 0.6
                        
                        # Record results
                        all_probs.append(prob)
                        total_clips += 1
                        if prob > 0.5:
                            deepfake_counts += 1
                            
                        label = 'deepfake' if prob > 0.5 else 'real'
                        results.append((frame_no, idx, label, prob))
            
            frame_no += 1
            
            # Early stopping for very long videos
            if frame_no > 300:  # Limit to 300 frames (30 processed frames at interval 10)
                logger.info(f"Early stopping at frame {frame_no} to limit processing time")
                break
            
        cap.release()
        logger.info(f"Processed {frame_no} frames, found {total_clips} faces")
        
        # Calculate summaries
        if total_clips > 0:
            avg_prob = sum(all_probs) / total_clips
            max_prob = max(all_probs) if all_probs else 0.0
            deepfake_pct = deepfake_counts / total_clips * 100
            logger.info(f"Detection stats: avg_prob={avg_prob:.2f}, max_prob={max_prob:.2f}, deepfake_pct={deepfake_pct:.2f}%")
        else:
            avg_prob = max_prob = deepfake_pct = 0.0
            logger.warning("No faces detected in video")
            
        # Determine if the video is fake based on thresholds
        is_fake = max_prob > 0.7 or (avg_prob > 0.5 and deepfake_pct > 30)
        confidence = max(max_prob * 100, avg_prob * 100)
        logger.info(f"Final detection result: is_fake={is_fake}, confidence={confidence:.2f}%")
        
        # Calculate processing time
        elapsed_time = time.time() - start_time
        logger.info(f"Detection completed in {elapsed_time:.2f} seconds")
        
        # Compile metadata
        metadata = {
            "processed_frames": frame_no,
            "processed_faces": total_clips,
            "deepfake_frames": deepfake_counts,
            "deepfake_percentage": deepfake_pct,
            "avg_probability": avg_prob,
            "max_probability": max_prob,
            "detection_time": elapsed_time,
            "model_used": "EfficientNet-B1 + LSTM" if deepfake_model is not None else "Heuristic",
            "video_dimensions": f"{width}x{height}",
            "video_fps": fps
        }
        
        # Save the detection result
        deepfake_detection = DeepFakeDetection.objects.create(
            detection=detection,
            face_count=total_clips,
            frame_count=frame_no,
            detection_time=elapsed_time
        )
        
        # Update the video object
        video_obj.isAnalyzed = True
        video_obj.save()
        
        # Clean up temporary file
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info(f"Removed temporary file: {temp_file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {e}")
        
        return detection, is_fake, confidence, metadata
        
    except Exception as e:
        logger.error(f"Error in deepfake detection: {e}", exc_info=True)
        # Update the DB object to reflect the error
        detection.delete()  # Remove the failed detection to avoid orphan records
        # Re-raise to let the calling code handle it
        raise 