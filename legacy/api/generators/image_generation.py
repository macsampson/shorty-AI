from fastapi import HTTPException
import aiohttp
import os
import datetime
from openai import AsyncOpenAI
from config import settings

# Initialize OpenAI client for DALL-E
client = AsyncOpenAI(api_key=settings.openai_api_key)

async def generate_image(request, output_dir):
    try:
        # Generate image using DALL-E
        response = await client.images.generate(
            model="dall-e-3",
            prompt=request.prompt,
            size="1024x1792",  # Portrait orientation for vertical videos
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

# DALL-E doesn't require model unloading
async def unload_image_model():
    print("DALL-E API doesn't require model unloading - operation skipped")
    pass

# async def generate_scene_image(scene, script_folder, output_dir):
#     prompt = scene['prompt']
#     async with aiohttp.ClientSession() as session:
#         try:
#             async with session.post(
#                 f"{SDXL_URL}/generate_image",
#                 json={
#                     "prompt": prompt,
#                     "num_inference_steps": 4,
#                     "guidance_scale": 1.0,
#                 },
#                 timeout=30,
#             ) as response:
#                 response_data = await response.json()

#             img_str = response_data.get("image")
#             if img_str:
#                 img_data = base64.b64decode(img_str)
#                 image = Image.open(BytesIO(img_data))
#                 image_filename = f"scene_{scene['scene_number']}.png"
#                 image_path = os.path.join(output_dir, image_filename)
#                 image.save(image_path)

#                 return image_path
#             else:
#                 raise HTTPException(status_code=500, detail="Error generating image.")

#         except asyncio.TimeoutError:
#             raise HTTPException(status_code=500, detail="Request to SDXL timed out.")
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=str(e))

# async def generate_images_from_script(script_data, script_folder, output_dir):
#     image_paths = []
#     print("Generating images from script...")
#     async with aiohttp.ClientSession() as session:
#         for scene in script_data['scenes']:
#             image_path = await generate_scene_image(scene, script_folder, output_dir)
#             image_paths.append(image_path)
        
#         for image_path in image_paths:
#             if not os.path.exists(image_path):
#                 raise HTTPException(status_code=500, detail=f"Image not found: {image_path}")

#         print("Sending unload request to SDXL")
#         await unload_sdxl()
#     return image_paths