# flux/Dockerfile

ARG BASE_IMAGE=python:3.9-slim
FROM ${BASE_IMAGE}

# Copy the application code
# COPY . .

WORKDIR /app

RUN mkdir -p /app/models
# Copy only the necessary files
COPY requirements.txt .
COPY api.py .

RUN pip install sentencepiece protobuf

# Create the directory for the SDXL model
# RUN mkdir -p /app/model/flux/

# Copy the SDXL model if it exists locally
# COPY model/sdxl/sdxl_lightning_4step_unet /app/model/sdxl/sdxl_lightning_4step_unet

EXPOSE 8008 

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8008", "--reload"]