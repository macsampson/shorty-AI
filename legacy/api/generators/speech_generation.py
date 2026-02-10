from fastapi import HTTPException
import aiohttp
import os
import datetime
from config import settings

async def generate_speech(request, output_dir):
    try:
        # ElevenLabs API configuration
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{request.voice}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": settings.elevenlabs_api_key
        }
        
        data = {
            "text": request.text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

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

        return [file_path]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")


# ElevenLabs doesn't require model unloading
async def unload_tortoise():
    print("ElevenLabs API doesn't require model unloading - operation skipped")
    pass