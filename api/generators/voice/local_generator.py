import os
import aiohttp
import datetime
from fastapi import HTTPException
from api.config import settings
from api.generators.base import VoiceGenerator

class LocalVoiceGenerator(VoiceGenerator):
    def __init__(self):
        self.api_url = settings.local_tts_url

    async def generate_speech(self, text: str, voice: str, output_dir: str) -> str:
        print(f"Generating speech with Local TTS: {text[:50]}...")
        
        # Assuming a simple API for the local TTS service
        # Adjust URL endpoint based on the actual container used (e.g., specific to Coqui/Piper)
        url = f"{self.api_url}/tts"
        
        # Mapping 'voice' ID to something the local TTS understands if necessary
        # For now, passing it through or using a default
        
        data = {
            "text": text,
            "voice_id": voice, # or default
            "language": "en"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=60) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(status_code=response.status, detail=f"Local TTS API error: {error_text}")
                    
                    # Generate filename with timestamp
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"speech_{timestamp}.wav" # Local TTS often outputs wav
                    file_path = os.path.join(output_dir, filename)
                    
                    # Ensure output directory exists
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Save audio file
                    with open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
            
            return file_path

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating speech with Local TTS: {str(e)}")
