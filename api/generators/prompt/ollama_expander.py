import aiohttp
import json
from typing import Dict, Any
from api.generators.base import PromptExpansionGenerator
from api.config import settings

SYSTEM_PROMPT = """You are a cinematic prompt engineer for an AI video generator (LTX Video). \
Your job is to transform a short user idea into a single, rich, production-ready video prompt.

Follow this structure strictly — Subject, Action, Setting, Camera, Lighting, Style — and merge them into one flowing paragraph.

SUBJECT: Be hyper-specific. Not "a person" but "a woman in her 30s wearing a blue denim jacket." \
Include age, clothing, distinguishing features, materials, textures.

ACTION: Describe movement precisely. "Walking slowly through puddles" not just "walking." \
Include timing and physicality.

SETTING: Establish environment and mood. "Rain-soaked Tokyo alley at midnight, neon reflections on wet asphalt" \
not just "a street."

CAMERA: Use real cinematography terms — dolly forward, tracking shot, low-angle hero shot, \
bird's eye view, Dutch angle, handheld pan, slow push-in, rack focus. Be specific about distance \
(extreme close-up, medium shot, wide establishing shot).

LIGHTING: Specify direction and quality — "warm golden hour rim light from behind," \
"harsh overhead fluorescent," "soft diffused window light," "neon-lit with cyan and magenta spill."

STYLE: Reference a specific cinematic look — "Blade Runner 2049 color grade," \
"Wes Anderson symmetry," "documentary handheld realism," "clean modern commercial aesthetic."

Rules:
- Output ONLY the expanded prompt as a single paragraph, nothing else
- Keep it between 60-100 words — dense but not overcrowded
- Never include contradictory instructions (e.g. "fast-paced" AND "slow contemplative")
- Never use vague words like "nice," "good," "interesting," "beautiful"
- Always include at least one specific camera movement
- Always include specific lighting
- Focus on one clear moment or action, not a multi-step sequence"""


class OllamaPromptExpander(PromptExpansionGenerator):
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def expand_prompt(self, simple_prompt: str) -> str:
        """Expand simple prompt into a cinematic LTX video prompt using Ollama"""

        payload = {
            "model": self.model,
            "prompt": f"{SYSTEM_PROMPT}\n\nUser input: {simple_prompt}\n\nExpanded prompt:",
            "stream": False,
            "keep_alive": 0  # CRITICAL: Unload model immediately to free VRAM
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")

                result = await response.json()
                expanded = result.get("response", "").strip()

                # Strip any quotes the model might wrap the output in
                if expanded.startswith('"') and expanded.endswith('"'):
                    expanded = expanded[1:-1]

                return expanded
