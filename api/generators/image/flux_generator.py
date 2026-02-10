import os
import aiohttp
import datetime
import base64
from fastapi import HTTPException
from api.config import settings
from api.generators.base import ImageGenerator

class FluxImageGenerator(ImageGenerator):
    def __init__(self):
        self.api_url = settings.flux_api_url

    async def generate_image(self, prompt: str, output_dir: str) -> str:
        print(f"Generating image with Flux: {prompt[:50]}...")
        url = f"{self.api_url}/generate_image"
        
        payload = {
            "prompt": prompt,
            "guidance_scale": 3.5, 
            "num_inference_steps": 4,
            "max_sequence_length": 256
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=120) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(status_code=500, detail=f"Flux API Error: {error_text}")
                    
                    data = await response.json()
                    img_str = data.get("image")
                    
                    if not img_str:
                         raise HTTPException(status_code=500, detail="No image data returned from Flux")

                    # Decode and save
                    img_data = base64.b64decode(img_str)
                    
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_path = os.path.join(output_dir, f"flux_{timestamp}.png")
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    
                    with open(image_path, "wb") as f:
                        f.write(img_data)
                        
                    return image_path

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Flux service: {str(e)}")
        finally:
            if settings.single_gpu_mode:
                await self._unload_model()

    async def _unload_model(self):
        print("Unloading Flux model due to single_gpu_mode...")
        url = f"{self.api_url}/unload_model"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, timeout=10) as response:
                    if response.status != 200:
                        print(f"Warning: Failed to unload Flux model: {response.status}")
        except Exception as e:
            print(f"Warning: Error unloading Flux model: {e}")
