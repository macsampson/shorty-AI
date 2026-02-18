# Apparition.io

**Apparition.io** is an automated short-form video generator that transforms text prompts into complete video productions. It orchestrates a suite of AI models for scriptwriting, image generation, voice synthesis, and video assembly, making it easy to create content for platforms like YouTube Shorts, TikTok, and Instagram Reels.

![Demo](https://github.com/macsampson/ai-shorts/blob/main/frontend/public/shorty_example.gif)

## Features

- **Script Generation**: Uses LLMs (OpenAI GPT-4, Llama 3 via Ollama) to craft engaging video scripts.
- **Image Generation**: Creates scene-specific visuals using DALL-E 3 or Flux (local/remote).
- **Voiceover**: Synthesizes natural-sounding narration with ElevenLabs or local Coqui TTS.
- **Video Assembly**: Automatically stitches images, audio, and subtitles into a polished video using FFmpeg and MoviePy.
- **Modern UI**: A responsive React frontend for managing generations and previewing results.

## Authorization

Apparition.io is built with a modular architecture:

- **Frontend**: React (TypeScript, TailwindCSS) - User interface for prompts and previews.
- **Backend**: FastAPI (Python) - Orchestrator for AI services and video processing.
- **AI Services**:
  - **Script**: OpenAI, Ollama (Local LLM)
  - **Image**: OpenAI (DALL-E), Flux (Local Diffusion)
  - **Voice**: ElevenLabs, Local TTS (Coqui)
- **Infrastructure**: Docker Compose manages all services including the API, Frontend, local LLM runners (Ollama), and image generators (Flux).

## Prerequisites

Before you begin, ensure you have the following installed:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Recommended)
- **NVIDIA GPU** (Recommended for local model inference)
- [Git](https://git-scm.com/)

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/macsampson/ai-shorts.git
    cd ai-shorts
    ```

2.  **Configure Environment Variables:**
    Copy the example environment file and update it with your API keys.

    ```bash
    cp .env.example .env
    ```

    Open `.env` and fill in your keys:

    ```env
    OPENAI_API_KEY=your_openai_key
    ELEVENLABS_API_KEY=your_elevenlabs_key
    ```

3.  **Start with Docker Compose:**
    ```bash
    docker-compose up --build
    ```
    _Note: This may take a while initially as it builds the containers and downloads necessary models (Ollama, Flux)._

## Local Models Setup

To use local AI providers, you need to place your model files in the `models/` directory:

- **Flux (Image)**: Place your Flux model files (e.g., `flux1-schnell.sft`, `ae.sft`) in `models/flux/`.
- **Ollama (Script)**: Ollama will automatically pull models to `models/ollama/` when the container starts for the first time.
- **Coqui TTS (Voice)**: Place your TTS model files (e.g., `tts_models/en/ljspeech/glow-tts`) in `models/tts/`.

## Configuration

The application is configured via environment variables in `.env` and `api/config.py`.

### AI Providers

You can switch between providers by modifying `api/config.py` or setting environment variables (if supported by `api/config.py` logic, currently hardcoded in `factory.py` based on `config.py` settings).

- **Script**: OpenAI / Ollama
- **Image**: OpenAI / Flux
- **Voice**: ElevenLabs / Local TTS

### Local Models (Ollama & Flux)

To use local models, ensure the `ollama` and `flux` services are running in Docker. The API is pre-configured to communicate with them via the internal Docker network.

## Usage

1.  Open your browser and navigate to `http://localhost:3000`.
2.  Enter a prompt for your video (e.g., "A history of the Roman Empire in 30 seconds").
3.  Click **Generate**.
4.  The system will:
    - Generate a script.
    - Create images for each scene.
    - Synthesize voiceovers.
    - Assemble the final video.
5.  View and download your video from the dashboard or the `generations/` folder.

## License

MIT License
