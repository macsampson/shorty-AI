import os
import asyncio
from api.config import settings
from api.generators.factory import GeneratorFactory

async def test_providers():
    print(f"Current Config:")
    print(f"Script Provider: {settings.ai_provider_script}")
    print(f"Image Provider: {settings.ai_provider_image}")
    print(f"Voice Provider: {settings.ai_provider_voice}")

    try:
        script_gen = GeneratorFactory.get_script_generator()
        print(f"✅ Script Generator Instantiated: {type(script_gen).__name__}")
    except Exception as e:
        print(f"❌ Script Generator Failed: {e}")

    try:
        image_gen = GeneratorFactory.get_image_generator()
        print(f"✅ Image Generator Instantiated: {type(image_gen).__name__}")
    except Exception as e:
        print(f"❌ Image Generator Failed: {e}")

    try:
        voice_gen = GeneratorFactory.get_voice_generator()
        print(f"✅ Voice Generator Instantiated: {type(voice_gen).__name__}")
    except Exception as e:
        print(f"❌ Voice Generator Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_providers())
