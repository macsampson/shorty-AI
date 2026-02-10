from fastapi import HTTPException
from fastapi.responses import Response

import json
import datetime
import os
import asyncio
from openai import AsyncOpenAI

# Import the settings from config
from config import settings

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.openai_api_key)

# TMP_DURATION = 60
TMP_SCENES = 2


async def generate_script(request, output_path):
    print("Generating script...")
    system_prompt = """You are a voiceover script generator. Create short stories based on topics provided.

Rules:
1. Reply in valid JSON format with a "title" string and "scenes" array
2. Script must be readable in under 1 minute
3. Each scene's voiceover must be one sentence
4. Include scene_number and script for each scene"""

    user_prompt = f"""Create a short story for this topic: {request.prompt}

Use this JSON format:
{{
    "title": "Story Title",
    "scenes": [
        {{
            "scene_number": 1,
            "script": "First scene description as one sentence."
        }},
        {{
            "scene_number": 2,
            "script": "Second scene description as one sentence."
        }}
    ]
}}"""

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        script = response.choices[0].message.content

        # write the script to a file in the output directory
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_path, f"{now}.json")
        with open(file_path, "w") as f:
            f.write(script)

        # Validate JSON
        try:
            json.loads(script)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from OpenAI")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI: {str(e)}")

    return Response(content=script, media_type="application/json")

# Generate a script and prompts for each scene
async def generate_scenes_and_prompts(request, num_scenes, output_path):
    print("Generating script...")
    
    system_prompt = f"""You create scripts with image prompts. Split the topic into exactly {num_scenes} scenes with matching image prompts.

Rules:
1. Reply in valid JSON format with "title" and "scenes" array
2. Split into exactly {num_scenes} scenes
3. Each scene needs "scene_number", "script", and "prompt"
4. Image prompts should be detailed for AI image generation
5. Focus on visual elements, characters, and actions"""

    user_prompt = f"""Create {num_scenes} scenes with image prompts for: {request.prompt}

Use this JSON format:
{{
    "title": "Story Title",
    "scenes": [
        {{
            "scene_number": 1,
            "script": "Scene narrative here.",
            "prompt": "detailed image prompt for AI generation"
        }}
    ]
}}"""

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        script = response.choices[0].message.content

        # write the script to a file in the output directory
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_path, f"{now}.json")
        with open(file_path, "w") as f:
            f.write(script)

        try:
            json.loads(script)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from OpenAI")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI: {str(e)}")

    return Response(content=script, media_type="application/json")


# OpenAI doesn't require model unloading
async def unload_llama():
    print("OpenAI API doesn't require model unloading - operation skipped")
    pass

# Generate a script split into scenes
async def generate_scenes(request, output_path, num_scenes = 1):
    print(f"Generating scenes for {num_scenes} scenes...")
    
    system_prompt = f"""You are a script writer. Create engaging narration scripts split into exactly {num_scenes} scenes.

Rules:
1. Reply in valid JSON format with "title" string and "scenes" array
2. Split into exactly {num_scenes} scenes
3. Each scene must be a complete thought or sentence
4. Include scene_number and script for each scene
5. Script must have beginning, middle, and conclusion
6. Make it interesting and engaging"""

    user_prompt = f"""Create a narration script for this topic: {request.prompt}

Use this JSON format:
{{
    "title": "Story Title",
    "scenes": [
        {{
            "scene_number": 1,
            "script": "Scene description here."
        }}
    ]
}}"""

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        scenes = response.choices[0].message.content

        # write the scenes to a file in the output directory
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_path, f"scenes_{now}.json")
        with open(file_path, "w") as f:
            f.write(scenes)

        try:
            json.loads(scenes)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from OpenAI")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI: {str(e)}")

    return Response(content=scenes, media_type="application/json")


# Generate a prompt for each scene
async def generate_prompts(scenes_data, output_path):
    print("Generating prompts...")
    
    system_prompt = """You are an expert at creating image prompts for AI image generators. Create detailed, visual prompts for each scene.

Rules:
1. Reply in valid JSON format with "prompts" array
2. Create one image prompt per scene for AI image generation
3. Focus on characters, actions, and visual details
4. Describe characters by physical features, not names
5. Use descriptive language suitable for image generation
6. Include technical details like "8k", "cinematic lighting", "high resolution"""

    user_prompt = f"""Create image generation prompts for these scenes: {json.dumps(scenes_data)}

Use this JSON format:
{{
    "prompts": [
        {{
            "scene_number": 1,
            "prompt": "detailed visual description for image generation"
        }}
    ]
}}"""

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        prompts = response.choices[0].message.content

        # write the prompts to a file in the output directory
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_path, f"prompts_{now}.json")
        with open(file_path, "w") as f:
            f.write(prompts)

        try:
            json.loads(prompts)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from OpenAI")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI: {str(e)}")

    return Response(content=prompts, media_type="application/json")



async def split_scenes(scenes_data):
    system_prompt = """You split scenes into smaller, more visual scenes suitable for image generation.

Rules:
1. Reply in valid JSON format with "title" and "scenes" array
2. Renumber scenes sequentially starting from 1
3. Each scene should be easily visualizable
4. Split original scenes into 2-4 smaller scenes
5. Split only at natural breaks (commas, periods)
6. Each new scene must be complete and descriptive"""

    user_prompt = f"""Split these scenes into smaller, more visual scenes:

{json.dumps(scenes_data)}

Use this JSON format:
{{
    "title": "Story Title",
    "scenes": [
        {{
            "scene_number": 1,
            "script": "Scene description here."
        }}
    ]
}}"""

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result = response.choices[0].message.content

        try:
            split_scenes = json.loads(result)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from OpenAI")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI: {str(e)}")

    return split_scenes