# Shorty AI

AI-powered video generation from text prompts using LLMs, image generation (FLUX/SDXL), and text-to-speech.

## Quick Start

```bash
docker-compose up
```

Access at http://localhost:3000

## Requirements

- Docker & Docker Compose
- CUDA-compatible GPU (recommended)

## Configuration

Change Ollama model via environment variable:
```bash
OLLAMA_MODEL=llama3
```

Or edit `api/config.py`
