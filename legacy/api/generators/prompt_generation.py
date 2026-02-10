from fastapi import HTTPException
from fastapi.responses import Response

import aiohttp
import json
import datetime
import os
import asyncio

# Import the settings from config
from config import settings

OLLAMA_URL = "http://ollama:11434"

async def generate_prompts(input_file_path, output_path):
    print("Generating prompts...")
    
    # Read the input text file
    with open(input_file_path, 'r') as file:
        script = file.read()

    template = f"""Given a script, you are to split it into scenes and provide an image prompt for each scene.

Here are some rules to follow at all costs:
1. You must reply in valid JSON format with a "scenes" array and a "title" string.
2. For each scene, you must provide an image prompt to be used with an image generation model.
3. Each image prompt should focus on characters and their actions using descriptive and detailed language.
4. Characters should not be referred to by name, but instead described by their physical features, clothing, gender, and actions.

Here is an example of the expected response format:
{{
    "title": "The Enchanted Forest Adventure",
    "scenes": [
        {{
            "scene_number": 1,
            "prompt": "close-up of young female explorer with auburn hair and green eyes, looking amazed, surrounded by glowing fairies with shimmering wings, in a magical forest glade with mystical mushrooms, intricate details, 8k, cinematic lighting"
        }},
        {{
            "scene_number": 2,
            "prompt": "close-up, human girl shrinking to fairy size, surrounded by glowing magical beings, iridescent wings, sparkles in the air, cinematic, 8k, natural lighting, HDR, high resolution"
        }}
    ]
}}

The script is: {script}
"""
    print("Template prepared, sending request to Ollama...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "prompt": template,
                    "model": settings.ollama_model,
                    "stream": False,
                    "format": "json",
                    "keep_alive": 0
                },
                timeout=60
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Ollama API request failed")
                
                response_data = await response.json()
                prompts = response_data.get("response", "{}")

                # write the prompts to a file in the output directory
                # name the file with the current timestamp
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(output_path, f"prompt_{now}.json")
                with open(file_path, "w") as f:
                    f.write(prompts)

                try:
                    json.loads(prompts)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail="Invalid JSON response from Ollama")

        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")

    # TODO: Only do this in development
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{OLLAMA_URL}/api/unload", json={"model": settings.ollama_model}):
            pass

    return Response(content=prompts, media_type="application/json")

# unload the llama model
async def unload_llama():
    async with aiohttp.ClientSession() as session:
        try:
            # Use the correct API endpoint format with proper JSON payload
            async with session.post(
                f"{OLLAMA_URL}/api/unload", 
                json={"model": settings.ollama_model},
                timeout=30
            ) as response:
                if response.status != 200:
                    print(f"Warning: Failed to unload {settings.ollama_model} model. Status: {response.status}")
                    try:
                        error_content = await response.text()
                        print(f"Error response: {error_content}")
                    except:
                        pass
                else:
                    print(f"{settings.ollama_model} model unloaded successfully")
                # Make sure to read the response
                await response.read()
        except asyncio.TimeoutError:
            print(f"Timeout while trying to unload {settings.ollama_model} model")
        except Exception as e:
            print(f"Error unloading {settings.ollama_model} model: {str(e)}")
            # Continue execution even if unload fails