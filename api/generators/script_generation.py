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

# TMP_DURATION = 60
TMP_SCENES = 2


async def generate_script(request, output_path):
    print("Generating script...")
    template = f"""You are a voiceover script generator.

Given a topic, you are to create a short story based on the topic.

Here are some rules to follow at all costs:
1. You must reply in valid JSON format with a "title" string, and a "scenes" array that contains the scene number and the voiceover script for that scene.
2. The script must be able to be read in under 1 minute.
3. Each scenes voiceover must be one sentence.

Here is an example of the expected response format:
{{
    "title": "The Enchanted Forest Adventure",
    "scenes": [
        {{
            "scene_number": 1,
            "script": "Deep in the heart of an ancient forest, a young explorer named Lily, with her backpack full of adventure gear, stumbled upon a hidden glade."
        }},
        {{
            "scene_number": 2,
            "script": "Curiosity overtook caution as Lily stepped into the fairy ring. In an instant, she shrunk to the size of a pixie."
        }}
    ]
}}

Your topic is: {request.prompt}
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
                script = response_data.get("response", "{}")

                # write the script to a file in the output directory
                # name the file with the current timestamp
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(output_path, f"{now}.json")
                with open(file_path, "w") as f:
                    f.write(script)

                try:
                    json.loads(script)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail="Invalid JSON response from Ollama")

        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")

    return Response(content=script, media_type="application/json")

# Generate a script and prompts for each scene
async def generate_scenes_and_prompts(request, num_scenes, output_path):
    print("Generating script...")
    template = f"""Given a script, you are to split it into {num_scenes} scenes, and provide an image prompt for each scene.

Here are some rules to follow at all costs:
1. You must reply in valid JSON format with a "scenes" array and a "title" string.
2. You must split the script into exactly {num_scenes} parts that can be used to generate images for each scene.
3. For each part, you must provide an image prompt to be used with stable diffusion XL to generate an image that portrays the scene.
4. Each image prompt should focus on characters and their actions using descriptive and detailed language.

Here is an example of the expected response format:
{{
    "title": "The Enchanted Forest Adventure",
    "scenes": [
        {{
            "scene_number": 1,
            "script": "Deep in the heart of an ancient forest, a young explorer named Lily, with her wide-eyed curiosity and backpack full of adventure gear, stumbled upon a hidden glade. Her auburn hair caught the sunlight filtering through the canopy as she gazed in wonder at a circle of mystical mushrooms. Lily's green eyes sparkled with excitement as she noticed tiny, glowing fairies, their delicate wings shimmering, flitting playfully between the toadstools.",
            "prompt": "close-up of young female explorer with auburn hair and green eyes, looking amazed, surrounded by glowing fairies with shimmering wings, in a magical forest glade with mystical mushrooms, intricate details, 8k, cinematic lighting"
        }},
        {{
            "scene_number": 2,
            "script": "Curiosity overtook caution as Lily stepped into the fairy ring. In an instant, she shrunk to the size of a pixie. The once-tiny creatures now appeared as radiant, winged beings, welcoming her with tinkling laughter and shimmering dust.",
            "prompt": "close-up, human girl shrinking to fairy size, surrounded by glowing magical beings, iridescent wings, sparkles in the air, cinematic, 8k, natural lighting, HDR, high resolution"
        }}
    ]
}}

The script is: {request.prompt}
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
                script = response_data.get("response", "{}")

                # write the script to a file in the output directory
                # name the file with the current timestamp
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(output_path, f"{now}.json")
                with open(file_path, "w") as f:
                    f.write(script)

                try:
                    json.loads(script)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail="Invalid JSON response from Ollama")

        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")

    # TODO: Only do this in development
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{OLLAMA_URL}/api/unload", json={"model": settings.ollama_model}):
            pass

    return Response(content=script, media_type="application/json")


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

# Generate a script split into scenes
async def generate_scenes(request, output_path, num_scenes = 1):
    print(f"Generating scenes for {num_scenes} scenes...")
    template = f"""Given a topic, you are to create a narration script based on the topic, split into {num_scenes} scenes.

Here are some rules to follow at all costs:
1. You must reply in valid JSON format with a "scenes" array and a "title" string.
2. You split the script into exactly {num_scenes} scenes.
3. Each scene's script must be a short sentence or a partial sentence split by a comma.
4. Each scene must contain a "script" string.
5. The script must have a beginning, middle, and conclusion.
6. The script must be interesting and engaging.

Here is an example of the expected response format for 2 scenes:
{{
    "title": "The Enchanted Forest Adventure",
    "scenes": [
        {{
            "scene_number": 1,
            "script": "Deep in the heart of an ancient forest, a young explorer named Lily, with her backpack full of adventure gear, stumbled upon a hidden glade."
        }},
        {{
            "scene_number": 2,
            "script": "Curiosity overtook caution as Lily stepped into the fairy ring. In an instant, she shrunk to the size of a pixie."
        }}
    ]
}}

Your topic is: {request.prompt}
"""
    print("Template prepared, sending scenes generation request to Ollama...")
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
                scenes = response_data.get("response", "{}")

                # write the scenes to a file in the output directory
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(output_path, f"scenes_{now}.json")
                with open(file_path, "w") as f:
                    f.write(scenes)

                try:
                    json.loads(scenes)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail="Invalid JSON response from Ollama")

        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")

    return Response(content=scenes, media_type="application/json")


# Generate a prompt for each scene
async def generate_prompts(scenes_data, output_path):
    print("Generating prompts...")
    template = f"""Given a script split into scenes, you are to provide an image prompt for each scene.

Here are some rules to follow at all costs:
1. You must reply in valid JSON format with a "title" string and a "prompts" array.
2. For each scene, you must provide an image prompt to be used with stable diffusion XL to generate an image that portrays the scene.
3. Each image prompt should focus on characters and their actions using descriptive and detailed language.
4. Characters should not be referred to by name, but rather described by their physical features, clothing, gender, and actions.
5. Do not use flowery language, and do not repeat the same word over and over again.

Here is an example of the expected response format:
{{
    "prompts": [
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

The scenes are: {json.dumps(scenes_data)}
"""
    print("Template prepared, sending prompt generation request to Ollama...")
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
                now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(output_path, f"prompts_{now}.json")
                with open(file_path, "w") as f:
                    f.write(prompts)

                try:
                    json.loads(prompts)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail="Invalid JSON response from Ollama")

        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")

    return Response(content=prompts, media_type="application/json")



async def split_scenes(scenes_data):
    # Prepare the prompt for Ollama
    prompt = f"""Given the following scenes, split them into smaller scenes where you think a new image could be used to represent that scene. Each scene should be a complete thought or action.

Rules:
1. Respond in valid JSON format with a "title" string and a "scenes" array.
2. Renumber all scenes sequentially starting from 1.
3. Ensure each scene is descriptive and can be visualized.
4. Split each original scene into 2-4 new scenes.
5. Only split scenes at commas or periods. Do not introduce new punctuation.
6. Each new scene must be a complete sentence or clause.

Example output format:
{{
    "title": "Dragon's Desperate Pursuit",
    "scenes": [
        {{
            "scene_number": 1,
            "script": "In the rolling hills of the countryside, a majestic dragon named Tharros appeared."
        }},
        {{
            "scene_number": 2,
            "script": "Tharros's scales shimmered like polished gold in the sunlight."
        }},
        {{
            "scene_number": 3,
            "script": "The dragon spotted its arch-nemesis, a cunning sheep named Winston."
        }}
    ]
}}

Input scenes:
{json.dumps(scenes_data)}
"""

    # Send request to Ollama
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "prompt": prompt,
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
                result = response_data.get("response", "{}")

                try:
                    split_scenes = json.loads(result)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=500, detail="Invalid JSON response from Ollama")

        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")

    return split_scenes