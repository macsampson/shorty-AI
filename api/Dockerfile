ARG BASE_IMAGE=python:3.9-slim
FROM ${BASE_IMAGE}

WORKDIR /app

# Install system dependencies including FFmpeg and necessary codecs
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libx264-dev \
    libavcodec-extra \
    build-essential \
    espeak \
    libespeak-dev \
    imagemagick \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Install Pillow
RUN pip install Pillow moviepy opencv-python whisper numpy Wand

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
pip install --no-cache-dir -r requirements.txt

# Output directory for generated images
RUN mkdir -p /app/generations

# Verify ImageMagick policy.xml exists, then modify it and check if successful
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then \
        sed -i 's|<policy domain="path" rights="none" pattern="@\*"/>|<policy domain="path" rights="read,write" pattern="@*"/>|g' /etc/ImageMagick-6/policy.xml && \
        if grep -q '<policy domain="path" rights="read,write" pattern="@\*"/>' /etc/ImageMagick-6/policy.xml; then \
            echo "ImageMagick policy.xml successfully modified"; \
        else \
            echo "Failed to modify ImageMagick policy.xml" && exit 1; \
        fi; \
    else \
        echo "ImageMagick policy.xml not found" && exit 1; \
    fi


COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]