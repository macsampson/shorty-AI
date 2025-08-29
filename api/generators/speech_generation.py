import aiohttp
from fastapi import HTTPException
import shutil
import os
import asyncio

TORTOISE_URL = "http://tortoise:8002"

async def generate_speech(request, output_dir):
    try:
        payload = {
            "text": request.text,
            "voice": request.voice,
            "preset": request.preset,
            "candidates": request.candidates,
            "cvvp_amount": request.cvvp_amount
        }

        params = {
            "output_dir": output_dir
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{TORTOISE_URL}/tts", json=payload, params=params, timeout=300) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail=await response.text())
                
                response_data = await response.json()
                audio_paths = response_data.get('audio_paths', [])
                
                if not audio_paths:
                    raise HTTPException(status_code=500, detail="No audio paths received from TTS service")

        return audio_paths

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")


async def unload_tortoise():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{TORTOISE_URL}/unload_model",
                timeout=30
            ) as response:
                if response.status != 200:
                    print(f"Warning: Failed to unload Tortoise model. Status: {response.status}")
                    try:
                        error_content = await response.text()
                        print(f"Error response: {error_content}")
                    except:
                        pass
                else:
                    print("Tortoise model unloaded successfully")
                # Make sure to read the response
                await response.read()
        except asyncio.TimeoutError:
            print("Timeout while trying to unload Tortoise model")
        except Exception as e:
            print(f"Error unloading Tortoise model: {str(e)}")
            # Continue execution even if unload fails