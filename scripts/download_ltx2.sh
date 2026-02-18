#!/bin/bash
# Download LTX-2 19B Distilled FP8 model

MODEL_DIR="./models/ltx2"
mkdir -p "$MODEL_DIR"

echo "Downloading LTX-2 19B Distilled FP8 model..."
wget -O "$MODEL_DIR/ltx-2-19b-distilled-fp8.safetensors" \
  https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.safetensors

echo "Model download complete!"
echo "Location: $MODEL_DIR/ltx-2-19b-distilled-fp8.safetensors"
