import json
import aiohttp
from fastapi import HTTPException
from api.config import settings
from api.generators.base import ScriptGenerator
from typing import Dict, Any

class OllamaScriptGenerator(ScriptGenerator):
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def _generate(self, prompt: str, system_prompt: str, json_format: bool = True) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        
        # Ollama requires a specific format for JSON mode in some versions, 
        # but generally just prompting well works. API defines "format": "json"
        
        keep_alive = 0 if settings.single_gpu_mode else -1 # 0 = unload immediately, -1 = keep loaded indefinitely (default)
        
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{prompt}",
            "stream": False,
            "format": "json" if json_format else None,
            "keep_alive": keep_alive,
            "options": {
                "temperature": 0.7
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(status_code=500, detail=f"Ollama API Error: {error_text}")
                    
                    data = await response.json()
                    response_text = data.get("response", "")
                    
                    if json_format:
                        try:
                            return json.loads(response_text)
                        except json.JSONDecodeError:
                            # Try to find JSON in the text if it's wrapped in markdown
                            start = response_text.find('{')
                            end = response_text.rfind('}') + 1
                            if start != -1 and end != -1:
                                return json.loads(response_text[start:end])
                            raise HTTPException(status_code=500, detail=f"Invalid JSON from Ollama: {response_text}")
                    return response_text

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")

    async def generate_script(self, topic: str) -> Dict[str, Any]:
        print(f"Generating script with Ollama ({self.model})...")
        system_prompt = """You are a voiceover script generator. Create short stories based on topics provided.
Reply ONLY in valid JSON format with a "title" string and "scenes" array.
Script must be readable in under 1 minute.
Each scene's voiceover must be one sentence.
Include scene_number and script for each scene."""

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
        return await self._generate(user_prompt, system_prompt)

    async def generate_scenes_and_prompts(self, topic: str, num_scenes: int) -> Dict[str, Any]:
        print(f"Generating {num_scenes} scenes and prompts with Ollama ({self.model})...")
        
        system_prompt = f"""You create scripts with image prompts. Split the topic into exactly {num_scenes} scenes with matching image prompts.
Reply ONLY in valid JSON format with "title" and "scenes" array.
Split into exactly {num_scenes} scenes.
Each scene needs "scene_number", "script", and "prompt".
Image prompts should be detailed for AI image generation.
Focus on visual elements, characters, and actions."""

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
        return await self._generate(user_prompt, system_prompt)
