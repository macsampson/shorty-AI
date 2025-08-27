# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

Shorty AI is a microservices-based video generation platform that creates animated videos from text prompts. The system consists of:

- **API Service (FastAPI)**: Main orchestration service handling video generation workflow
- **Frontend (React/TypeScript)**: User interface built with Tailwind CSS
- **Ollama**: LLM service for script and prompt generation
- **SDXL/Flux**: Image generation services using Stable Diffusion
- **Tortoise TTS**: Text-to-speech generation service
- **Common Base**: Shared Docker base image for GPU services

## Development Commands

### Running the Application
```bash
# Start all services
docker-compose up

# Start specific services only
docker-compose up central ollama frontend
```

### Frontend Development
```bash
cd frontend
npm start          # Development server on port 3000
npm run build      # Production build
npm test           # Run tests
```

### API Development
The FastAPI service runs on port 8000 with auto-reload in development mode.

## Key Configuration

### Environment Variables
- `OLLAMA_MODEL`: Override the default LLM model (configurable in `api/config.py`)
- GPU services require NVIDIA runtime and CUDA-compatible hardware

### Model Configuration
The Ollama model can be changed by:
1. Setting `OLLAMA_MODEL` environment variable
2. Modifying the default in `api/config.py:ollama_model`
3. Ensuring the model exists: `ollama list` and `ollama pull <model>`

## Video Generation Pipeline

The core video generation follows this sequence:
1. **Script Generation**: Uses Ollama LLM to create structured scenes from text prompt
2. **Scene Splitting**: Breaks scenes into smaller segments for better pacing
3. **Image Prompt Generation**: Creates visual descriptions for each scene
4. **Image Generation**: Produces visuals using SDXL/Flux services
5. **Speech Generation**: Converts script text to audio using Tortoise TTS
6. **Audio Alignment**: Creates forced alignment maps for precise caption timing
7. **Video Assembly**: Combines images, audio, and captions using MoviePy

## Important File Locations

- **Main API**: `api/main.py` - Core FastAPI application with all endpoints
- **Generators**: `api/generators/` - Individual generation modules
- **Schemas**: `api/schemas/` - Pydantic request/response models  
- **Frontend Components**: `frontend/src/components/` - React UI components
- **Settings Management**: Global settings stored in `current_settings` object

## Generation Settings

The system uses a global `GenerationSettings` object controlling:
- Scene count and duration
- Voice selection and TTS quality presets
- Caption styling and word highlighting
- Retry limits and advanced parameters

Access via `/update_settings` and `/get_settings` endpoints.

## Service Dependencies

Services have specific startup dependencies:
- `central` depends on `ollama` and `common-base`
- `frontend` depends on `central`
- GPU services (`sdxl`, `flux`, `tortoise`) depend on `common-base`

## Storage Structure

Generated content is organized in `/app/generations/`:
- `images/` - Generated scene images
- `speech/` - TTS audio files  
- `videos/` - Final video outputs with all assets
- `scripts/` - Scene scripts and metadata

## Testing

The system includes testing endpoints:
- `/test_create_video` - Tests the caption overlay system
- `/generate_alignment_map` - Tests forced alignment functionality
- Test assets are stored in `api/testing/`