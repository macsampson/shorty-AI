import os
import aiohttp
import datetime
from fastapi import HTTPException
from openai import AsyncOpenAI
from api.config import settings
from api.generators.base import ImageGenerator

class OpenAIImageGenerator(ImageGenerator):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_image(self, prompt: str, output_dir: str) -> str:
        print(f"Generating image with DALL-E: {prompt[:50]}...")
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1792",  # Portrait
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as img_response:
                    if img_response.status != 200:
                        raise HTTPException(status_code=500, detail="Failed to download generated image")
                    
                    # Generate filename and save
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_path = os.path.join(output_dir, f"dalle_{timestamp}.png")
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    
                    with open(image_path, "wb") as f:
                        async for chunk in img_response.content.iter_chunked(8192):
                            f.write(chunk)
            
            return image_path

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating image with DALL-E: {str(e)}")
