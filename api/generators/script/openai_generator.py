import json
import datetime
import os
from openai import AsyncOpenAI
from fastapi import HTTPException
from api.config import settings
from api.generators.base import ScriptGenerator
from typing import Dict, Any

class OpenAIScriptGenerator(ScriptGenerator):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def generate_script(self, topic: str) -> Dict[str, Any]:
        print("Generating script with OpenAI...")
        system_prompt = """You are a voiceover script generator. Create short stories based on topics provided.

Rules:
1. Reply in valid JSON format with a "title" string and "scenes" array
2. Script must be readable in under 1 minute
3. Each scene's voiceover must be one sentence
4. Include scene_number and script for each scene"""

        user_prompt = f"""Create a short story for this topic: {topic}

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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            script_content = response.choices[0].message.content
            return json.loads(script_content)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI: {str(e)}")

    async def generate_scenes_and_prompts(self, topic: str, num_scenes: int) -> Dict[str, Any]:
        print(f"Generating {num_scenes} scenes and prompts with OpenAI...")
        
        system_prompt = f"""You create scripts with image prompts. Split the topic into exactly {num_scenes} scenes with matching image prompts.

Rules:
1. Reply in valid JSON format with "title" and "scenes" array
2. Split into exactly {num_scenes} scenes
3. Each scene needs "scene_number", "script", and "prompt"
4. Image prompts should be detailed for AI image generation
5. Focus on visual elements, characters, and actions"""

        user_prompt = f"""Create {num_scenes} scenes with image prompts for: {topic}

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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            script_content = response.choices[0].message.content
            return json.loads(script_content)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI: {str(e)}")
