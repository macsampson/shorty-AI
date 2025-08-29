import aiohttp
import base64
from fastapi import HTTPException
from PIL import Image
from io import BytesIO
import os
import datetime
import asyncio

# IMAGE_GEN_URL, MODEL_NAME = "http://sdxl:8001", "sdxl"
IMAGE_GEN_URL, MODEL_NAME = "http://flux:8008", "flux"

async def generate_image(request, output_dir):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{IMAGE_GEN_URL}/generate_image",
                json={
                    "prompt": request.prompt,
                    "num_inference_steps": request.num_inference_steps,
                    "guidance_scale": request.guidance_scale,
                    "max_sequence_length": request.max_sequence_length,
                },
                timeout=300
            ) as response:
                response_data = await response.json()

            img_str = response_data.get("image")
            if img_str:
                img_data = base64.b64decode(img_str)
                image = Image.open(BytesIO(img_data))
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = os.path.join(output_dir, f"{MODEL_NAME}_{now}.png")
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image.save(image_path)
                
                return image_path
            else:
                raise HTTPException(status_code=500, detail=f"Error generating {MODEL_NAME} image.")

        except asyncio.TimeoutError:
            raise HTTPException(status_code=500, detail=f"Request to {MODEL_NAME} model timed out.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

async def unload_image_model():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{IMAGE_GEN_URL}/unload_model", 
                timeout=30
            ) as response:
                if response.status != 200:
                    print(f"Warning: Failed to unload {MODEL_NAME} model. Status: {response.status}")
                    try:
                        error_content = await response.text()
                        print(f"Error response: {error_content}")
                    except:
                        pass
                else:
                    print(f"{MODEL_NAME} model unloaded successfully")
                await response.read()
        except asyncio.TimeoutError:
            print(f"Timeout while trying to unload {MODEL_NAME} model")
        except Exception as e:
            print(f"Error unloading {MODEL_NAME} model: {str(e)}")

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