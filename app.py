from flask import Flask, request, render_template
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
from efficientnet_pytorch import EfficientNet

import cv2, os, tempfile
from flask import render_template

# --- 1) Your model definition exactly as trained ---
class EffNetLSTM(nn.Module):
    def __init__(self, num_classes, model_name='efficientnet-b0',
                 lstm_layers=1, hidden_dim=512, bidirectional=False):
        super().__init__()
        self.model = EfficientNet.from_pretrained(model_name)
        self.extract_features = self.model.extract_features
        latent_dim = self.model._fc.in_features  # 1280 for B0

        self.avgpool = nn.AdaptiveAvgPool2d(1)
        self.lstm    = nn.LSTM(latent_dim, hidden_dim,
                               lstm_layers, bidirectional=bidirectional)
        self.relu    = nn.LeakyReLU()
        self.dp      = nn.Dropout(0.4)
        self.linear  = nn.Linear(
            hidden_dim * (2 if bidirectional else 1),
            num_classes
        )

    def forward(self, x):
        # x: [B, T, 3, H, W]
        b, t, c, h, w = x.shape
        x = x.view(b*t, c, h, w)
        fmap = self.extract_features(x)       # [B*T, feat, H', W']
        x = self.avgpool(fmap)                # [B*T, feat, 1,1]
        x = x.view(b, t, -1)                  # [B, T, feat]
        x_lstm, _ = self.lstm(x)              # [B, T, hidden*dirs]
        out = torch.mean(x_lstm, dim=1)       # temporal mean
        out = self.linear(self.dp(out))       # → [B, num_classes]
        return fmap, out

# --- 2) Flask app and model loading ---
app = Flask(__name__)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = EffNetLSTM(num_classes=2, model_name='efficientnet-b0')
model.load_state_dict(torch.load("EfficientNet-b0_model.dat",
                                 map_location=device), strict=False)
model.to(device).eval()

# human-readable labels
LABELS = {0: "Real", 1: "Fake"}

# Pre-processing: ImageNet defaults
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
      mean=[0.485, 0.456, 0.406],
      std =[0.229, 0.224, 0.225]
    )
])

# --- 3) Routes ---
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# @app.route("/predict", methods=["POST"])
# def predict():
#     files = request.files.getlist("frames")
#     # load and preprocess each frame
#     tensors = []
#     for f in files:
#         img = Image.open(f.stream).convert("RGB")
#         tensors.append(preprocess(img))
#     # stack into [1, T, 3, 224, 224]
#     seq = torch.stack(tensors, dim=0).unsqueeze(0).to(device)

#     with torch.no_grad():
#         _, logits = model(seq)
#         probs = torch.softmax(logits[0], dim=0)
#         cls_id = int(probs.argmax())
#         prob   = float(probs[cls_id])

#     return render_template("index.html",
#                            result={"label": LABELS[cls_id],
#                                    "prob": prob})

@app.route("/predict", methods=["POST"])
def predict():
    # 1) Grab the uploaded video
    video_file = request.files.get("video")
    if video_file is None:
        return render_template("index.html",
                               error="No video uploaded. Please choose a file.")

    # 2) Save to a temp file so OpenCV can read it
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.write(video_file.read())
    tmp.close()
    video_path = tmp.name

    # 3) Open with OpenCV & sample frames
    cap = cv2.VideoCapture(video_path)
    frames = []
    success, frame = cap.read()
    frame_idx = 0
    SAMPLE_RATE = 5    # take every 5th frame
    MAX_FRAMES  = 16   # up to 16 frames
    while success and len(frames) < MAX_FRAMES:
        if frame_idx % SAMPLE_RATE == 0:
            # BGR → RGB → PIL → preprocess
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil   = Image.fromarray(rgb)
            frames.append(preprocess(pil))
        success, frame = cap.read()
        frame_idx += 1
    cap.release()
    os.unlink(video_path)  # clean up

    if not frames:
        return render_template("index.html",
                               error="Couldn't extract any frames from the video.")

    # 4) Stack into [1, T, 3, 224, 224]
    seq = torch.stack(frames, dim=0).unsqueeze(0).to(device)

    # 5) Inference
    with torch.no_grad():
        _, logits = model(seq)
        probs = torch.softmax(logits[0], dim=0)
        cls_id = int(probs.argmax())
        prob   = float(probs[cls_id])

    # 6) Render result
    return render_template("index.html",
                           result={"label": LABELS[cls_id],
                                   "prob": prob})


if __name__ == "__main__":
    app.run(debug=True)
