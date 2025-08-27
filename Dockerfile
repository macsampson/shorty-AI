# common-base.Dockerfile

FROM python:3.9-slim

# Set up environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip

# Copy requirements file (this should be common dependencies)
COPY common-requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r common-requirements.txt
