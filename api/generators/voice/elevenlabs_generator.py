import os
import aiohttp
import datetime
from fastapi import HTTPException
from api.config import settings
from api.generators.base import VoiceGenerator

class ElevenLabsVoiceGenerator(VoiceGenerator):
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key

    async def generate_speech(self, text: str, voice: str, output_dir: str) -> str:
        print(f"Generating speech with ElevenLabs: {text[:50]}...")
        
        # ElevenLabs API configuration
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers, timeout=60) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(status_code=response.status, detail=f"ElevenLabs API error: {error_text}")
                    
                    # Generate filename with timestamp
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"speech_{timestamp}.mp3"
                    file_path = os.path.join(output_dir, filename)
                    
                    # Ensure output directory exists
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Save audio file
                    with open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
            
            return file_path

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating speech with ElevenLabs: {str(e)}")
