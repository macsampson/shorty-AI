# Shorty AI

![](https://github.com/macsampson/ai-shorts/blob/main/frontend/public/shorty_example.gif)

AI-powered video generation from text prompts using OpenAI, ElevenLabs, and DALL-E APIs.

## Quick Start

1. Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

2. Edit `.env` with your API keys:

```bash
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

3. Start the application:

```bash
docker-compose up
```

4. Access at http://localhost:3000

## Requirements

- Docker & Docker Compose
- OpenAI API key
- ElevenLabs API key

## Features

- **Script Generation**: OpenAI GPT models for creative storytelling
- **Image Generation**: DALL-E 3 for high-quality scene visuals
- **Text-to-Speech**: ElevenLabs for natural voice synthesis
- **Video Assembly**: Automated video creation with captions
