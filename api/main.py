from fastapi import FastAPI, HTTPException, Response, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

import os
import json
import datetime
import subprocess
import re
import aiohttp
import shutil

import moviepy.editor as mp

from urllib.parse import unquote
from pathlib import Path
from schemas.generate_image_request import GenerateImageRequest
from schemas.generate_text_request import GenerateTextRequest
from schemas.generate_speech_request import GenerateSpeechRequest

from generators.image_generation import generate_image, unload_image_model
from generators.script_generation import generate_script, unload_llama, generate_scenes, generate_prompts, split_scenes
from generators.speech_generation import generate_speech, unload_tortoise  
from generators.caption_overlay import generate_forced_alignment_map, add_word_captions, _apply_effects, format_aeneas_timestamps, add_phrase_captions_with_highlighting, create_advanced_captions
from generators.subtitle_creator import srt_create
from pydantic import BaseModel, Field

app = FastAPI()

# Variables that will be exposed to the frontend
SCENE_DURATION = 5 # Default duration for the video in seconds

# External API services - no local URLs needed
MAX_RETRIES = 3 # Maximum number of retries to generate a valid JSON object
VOICE = "pNInz6obpgDQGcFmaJgB"  # Default ElevenLabs voice ID
# Define the path for the generated images
# GENERATED_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generations")
GENERATED_IMAGES_DIR = "/app/generations/images"
GENERATED_SPEECH_DIR = "/app/generations/speech"
GENERATED_VIDEOS_DIR = "/app/generations/videos"
GENERATED_SCRIPTS_DIR = "/app/generations/scripts"  

# Caption settings
CAPTION_WORDS_PER_LINE = 5  # Number of words to display per line
CAPTION_MAX_LINES = 2       # Maximum number of lines to display at once
CAPTION_STYLE = "modern"  # Default caption style
CAPTION_HIGHLIGHT_COLOR = "#00FF7F"  # Default highlight color
CAPTION_NORMAL_COLOR = "#FFFFFF"  # Default normal text color

# Available caption styles
CAPTION_STYLES = ["modern", "classic", "neon", "minimal"]

# Default number of scenes
DEFAULT_NUM_SCENES = 5

# Available ElevenLabs voices (voice_id: name)
AVAILABLE_VOICES = {
    "pNInz6obpgDQGcFmaJgB": "Adam",
    "21m00Tcm4TlvDq8ikWAM": "Rachel",
    "AZnzlk1XvdvUeBnXmlld": "Domi", 
    "EXAVITQu4vr4xnSDxMaL": "Bella",
    "MF3mGyEYCl7XYWbV9V6O": "Elli",
    "TxGEqnHWrfWFTfGW9XjX": "Josh",
    "VR6AewLTigWG4xSOukaG": "Arnold",
    "pqHfZKP75CvOlQylNhV4": "Bill",
    "yoZ06aMxZJJ28mfd3POQ": "Sam",
    "29vD33N1CtxCmqQRPOHJ": "Drew"
}

# TTS generation presets (simplified for ElevenLabs)
TTS_PRESETS = [
    "standard"
]

class CaptionSettings(BaseModel):
    words_per_line: int = Field(default=5, ge=1, le=10)
    max_lines: int = Field(default=2, ge=1, le=5)
    style: str = Field(default="modern", description="Caption style preset")
    highlight_color: str = Field(default="#00FF7F", description="Color for highlighted words")
    normal_color: str = Field(default="#FFFFFF", description="Color for normal words")

class GenerationSettings(BaseModel):
    # Video structure settings
    num_scenes: int = Field(default=DEFAULT_NUM_SCENES, ge=1, le=10, description="Number of scenes in the video")
    scene_duration: int = Field(default=SCENE_DURATION, ge=3, le=15, description="Target duration for each scene in seconds")
    
    # Voice settings
    voice: str = Field(default=VOICE, description="ElevenLabs voice ID to use for text-to-speech")
    tts_preset: str = Field(default="standard", description="Quality preset for text-to-speech generation")
    
    # Caption settings
    caption_words_per_line: int = Field(default=CAPTION_WORDS_PER_LINE, ge=1, le=10, description="Number of words per line in captions")
    caption_max_lines: int = Field(default=CAPTION_MAX_LINES, ge=1, le=5, description="Maximum number of caption lines to display")
    caption_style: str = Field(default="modern", description="Caption visual style preset")
    caption_highlight_color: str = Field(default="#00FF7F", description="Color for highlighted words in captions")
    caption_normal_color: str = Field(default="#FFFFFF", description="Color for normal words in captions")
    
    # Advanced settings
    max_retries: int = Field(default=MAX_RETRIES, ge=1, le=10, description="Maximum number of retries for generation")

# Global settings object
current_settings = GenerationSettings()

@app.on_event("startup")
async def startup_event():
    directories = [GENERATED_IMAGES_DIR, GENERATED_SPEECH_DIR, GENERATED_VIDEOS_DIR, GENERATED_SCRIPTS_DIR]
    
    for folder in directories:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            print(f"Folder created: {folder}")
    return directories

# Store the created directories
created_directories = []

@app.on_event("startup")
async def store_created_directories():
    global created_directories
    created_directories = await startup_event()

# ------------ HELPER FUNCTIONS ------------
# Helper function to find the matching closing brace for the opening brace at the given index
def find_matching_brace(text, start):
    stack = []
    for i, char in enumerate(text[start:], start):
        if char == '{':
            stack.append(char)
        elif char == '}':
            if not stack:
                return -1  # Unmatched closing brace
            stack.pop()
            if not stack:
                return i  # Found matching closing brace
    return -1  # No matching closing brace found

def get_audio_duration(audio_path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # print("Audio duration: ", result.stdout)
    return float(result.stdout)


# Helper function to format timecode for SRT file
def format_timecode(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}.{milliseconds:03d}"

def sanitize_filename(filename):
    return re.sub(r'[^\w\-_\. ]', '_', filename)


# Mount the generated directories
def mount_directories():
    # Mount the parent directory that contains all generation directories
    app.mount("/generations", StaticFiles(directory="/app/generations"), name="generations")
    print("Generations directory mounted")

# Call this function after the app has been created and the startup event has run
mount_directories()


# ------------ SCRIPT GENERATION ------------
# Generate script endpoint
@app.post("/generate_script")
async def generate_script_endpoint(request: GenerateTextRequest, output_dir: str = GENERATED_SCRIPTS_DIR):
    response = await generate_scenes(request, output_dir)
    # TODO: Only do this in development
    await unload_llama()
    return response

@app.post("/generate_scenes_and_prompts")
async def generate_scenes_and_prompts_endpoint(request: GenerateTextRequest, output_dir: str = GENERATED_SCRIPTS_DIR, num_scenes: int = None):
    # Use the configured number of scenes if not explicitly provided
    if num_scenes is None:
        num_scenes = DEFAULT_NUM_SCENES
    
    # Generate scenes
    response = await generate_scenes(request, output_dir, num_scenes)
    script = response.body.decode("utf-8")
    script_data = json.loads(script)

    # Generate prompts
    prompts_response = await generate_prompts(script_data, output_dir)
    prompts_data = json.loads(prompts_response.body)

    return {
        "script": script_data,
        "prompts": prompts_data
    }

# ------------ SPEECH GENERATION ------------
@app.post("/generate_speech")
async def generate_speech_endpoint(request: GenerateSpeechRequest, output_dir: str):
    response = await generate_speech(request, output_dir)
    # TODO: Only do this in development
    await unload_tortoise()
    return response



# ------------ IMAGE GENERATION ------------
@app.post("/generate_image")
async def generate_image_endpoint(request: GenerateImageRequest, output_dir: str):
    response = await generate_image(request, output_dir)
    # TODO: Only do this in development
    await unload_image_model()
    return response



# -------- VIDEO CREATION --------

# Add this new endpoint after the existing endpoints
@app.post("/generate_video")
async def generate_video(request: GenerateTextRequest):
    start_time = datetime.datetime.now()

    # Generate script
    response = await generate_scenes(request, GENERATED_SCRIPTS_DIR, current_settings.num_scenes)
    script = response.body.decode("utf-8")
    script_data = json.loads(script)

    # Split the scenes into smaller scenes
    script_data = await split_scenes(script_data)

    print("Script data: ", script_data)

    current_datetime = datetime.datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
    prep_folder = f"{current_datetime}_{sanitize_filename(script_data['title'])}"

    # Generate image prompts
    prompts_response = await generate_prompts(script_data, GENERATED_SCRIPTS_DIR)
    prompts_data = json.loads(prompts_response.body)
    
    actual_prompts_list = prompts_data.get('prompts', [])
    num_split_scenes = len(script_data.get('scenes', [])) # Get length of scenes list safely
    num_actual_prompts = len(actual_prompts_list)

    if num_actual_prompts < num_split_scenes:
        print(f"Warning: LLM generated {num_actual_prompts} prompts for {num_split_scenes} split scenes. Adjusting prompt list.")
        if actual_prompts_list:  # If there's at least one prompt to use as a template
            last_prompt_detail = actual_prompts_list[-1]
            missing_prompt_text = last_prompt_detail.get('prompt', "A descriptive visual for this scene.")
            for i in range(num_split_scenes - num_actual_prompts):
                actual_prompts_list.append({'scene_number': num_actual_prompts + i + 1, 'prompt': missing_prompt_text})
        elif num_split_scenes > 0:  # No prompts generated, but scenes exist
            print("Error: No prompts generated by LLM. Using generic prompts for all scenes.")
            generic_prompt_text = "A general visual representation for the scene."
            actual_prompts_list = [] # Ensure it's empty before repopulating
            for i in range(num_split_scenes):
                 actual_prompts_list.append({'scene_number': i + 1, 'prompt': f"{generic_prompt_text} (Scene {i+1})"})
        # If num_split_scenes is 0, actual_prompts_list will remain empty, which is fine.
        prompts_data['prompts'] = actual_prompts_list # Update prompts_data if it's referenced later directly

    elif num_actual_prompts > num_split_scenes:
        print(f"Warning: LLM generated {num_actual_prompts} prompts, more than {num_split_scenes} split scenes. Truncating prompts list.")
        actual_prompts_list = actual_prompts_list[:num_split_scenes]
        prompts_data['prompts'] = actual_prompts_list # Update prompts_data

    # TODO: Only do this in development
    await unload_llama()

  
    # Generate image for each scene
    image_paths = []
    image_prep_folder = os.path.join(GENERATED_IMAGES_DIR, prep_folder)
    os.makedirs(image_prep_folder, exist_ok=True)

    if not actual_prompts_list and num_split_scenes > 0:
        # This case should have been handled by the padding logic above.
        # If it's reached, it implies an issue, or num_split_scenes was 0 and now actual_prompts_list is also empty.
        # If num_split_scenes > 0 and list is empty, it's an error state.
        raise HTTPException(status_code=500, detail=f"Prompt list is unexpectedly empty for {num_split_scenes} scenes after adjustment logic.")
    
    for prompt_item in actual_prompts_list: # Iterate using the adjusted list
        # Ensure prompt_item is a dict and has 'prompt' key
        if not isinstance(prompt_item, dict) or 'prompt' not in prompt_item:
            print(f"Warning: Invalid prompt item encountered: {prompt_item}. Using a default prompt.")
            prompt_text = "Default fallback image prompt due to invalid item."
        else:
            prompt_text = prompt_item['prompt']
            
        image_request = GenerateImageRequest(prompt=prompt_text)
        image_path = await generate_image(image_request, image_prep_folder)
        image_paths.append(image_path)

    # TODO: Only do this in development
    await unload_image_model()

    print("DEBUG: Image generation complete. Starting speech generation loop...") # DEBUG
  
    # Generate speech for each scene
    audio_paths = []
    # Ensure script_data['scenes'] is used here, which actual_prompts_list was aligned to
    for i, scene in enumerate(script_data.get('scenes', [])): # DEBUG: Added enumerate
        print(f"DEBUG: Processing scene {i+1}/{len(script_data.get('scenes', []))} for speech generation.") # DEBUG
        # construct a GenerateSpeechRequest object
        speech_request = GenerateSpeechRequest(
            text=scene.get('script', "Missing script."), # Safe access to script text
            voice=current_settings.voice, 
            preset=current_settings.tts_preset, 
            candidates=1, 
            cvvp_amount=0.0
        )
        print(f"DEBUG: Calling generate_speech for scene {i+1}...") # DEBUG
        audio_path = await generate_speech(speech_request, GENERATED_SPEECH_DIR)
        print(f"DEBUG: generate_speech for scene {i+1} returned: {audio_path}") # DEBUG

        audio_prep_folder = os.path.join(GENERATED_SPEECH_DIR, prep_folder)
        os.makedirs(audio_prep_folder, exist_ok=True)
        # Ensure scene_number is safely accessed
        scene_number = scene.get('scene_number', f'unknown_scene_{i+1}') # DEBUG: improved fallback
        audio_filename = f"scene_{scene_number}.wav"
        destination_audio_path = os.path.join(audio_prep_folder, audio_filename)
        
        if audio_path and isinstance(audio_path, list) and len(audio_path) > 0:
            source_audio_path = audio_path[0]
            print(f"DEBUG: Moving audio for scene {i+1} from {source_audio_path} to {destination_audio_path}") # DEBUG
            shutil.move(source_audio_path, destination_audio_path)
            audio_paths.append(destination_audio_path)
            print(f"DEBUG: Audio for scene {i+1} moved and appended.") # DEBUG
        else:
            print(f"Warning: Could not generate or find audio for scene {scene_number}.")
            # Potentially add a placeholder silent audio or handle error

    print("DEBUG: Speech generation loop complete.") # DEBUG

    # TODO: Only do this in development
    print("DEBUG: Calling unload_tortoise...") # DEBUG
    await unload_tortoise()
    print("DEBUG: unload_tortoise complete.") # DEBUG

    # Create a combined audio file
    print("DEBUG: Combining audio files...")
    combined_audio_path = os.path.join(os.path.dirname(GENERATED_SPEECH_DIR), "combined_audio.wav") # Fixed: Use parent of GENERATED_SPEECH_DIR
    
    if not audio_paths:
        print("Warning: No audio paths to combine. Skipping ffmpeg audio combination.")
        # Handle the case where no audio was generated - perhaps create a silent audio track
        # For now, we'll let it proceed, but downstream functions might fail if they expect combined_audio_path
        # Or, raise an error if audio is critical:
        # raise HTTPException(status_code=500, detail="No audio files were generated to combine.")
    else:
        combine_audio_command = ['ffmpeg', '-y']
        for ap_path in audio_paths: # DEBUG: changed variable name
            combine_audio_command.extend(['-i', ap_path])
        combine_audio_command.extend(['-filter_complex', f'concat=n={len(audio_paths)}:v=0:a=1', combined_audio_path]) # DEBUG: f-string
        print(f"DEBUG: Running ffmpeg command: {' '.join(combine_audio_command)}") # DEBUG
        try:
            subprocess.run(combine_audio_command, check=True, capture_output=True, text=True) # DEBUG: Added capture_output and text
            print("DEBUG: ffmpeg audio combination complete.") # DEBUG
        except subprocess.CalledProcessError as e:
            print(f"ERROR: ffmpeg audio combination failed. Return code: {e.returncode}")
            print(f"ffmpeg stdout: {e.stdout}")
            print(f"ffmpeg stderr: {e.stderr}")
            raise HTTPException(status_code=500, detail=f"ffmpeg audio combination failed: {e.stderr}")


    # Create video output path
    video_filename = f"{prep_folder}.mp4"
    video_path = os.path.join(GENERATED_VIDEOS_DIR, prep_folder, video_filename).replace(" ", "_")
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    
    script_folder = os.path.join(GENERATED_SCRIPTS_DIR, prep_folder)
    os.makedirs(script_folder, exist_ok=True)
    script_path = os.path.join(script_folder, "script.json")
    with open(script_path, "w") as f:
        f.write(script)

    print("DEBUG: Getting audio timestamps...") # DEBUG
    # Get audio timestamps
    timestamps = generate_forced_alignment_map(script_data, combined_audio_path, video_path)
    print("DEBUG: Audio timestamps complete.") # DEBUG

    # scene_timestamps = timestamps['scene']
    # word_timestamps = timestamps['words']

    # # Generate image list
    # input_file = os.path.join(image_prep_folder, "image_list.txt")
    # with open(input_file, 'w') as f:
    #     for image_path, ((scene_start_time, scene_end_time), text) in zip(image_paths, scene_timestamps):
    #         duration = scene_end_time - scene_start_time
    #         f.write(f"file '{image_path}'\n")
    #         f.write(f"duration {duration}\n")
    
    # audio_clip = mp.AudioFileClip(combined_audio_path)
    # subtitles_clip = add_word_captions(word_timestamps)
    # subtitles_clip = subtitles_clip.set_duration(audio_clip.duration)
    # subtitles_clip = subtitles_clip.set_position('center','center')

    # # to avoid a bug with noisy sounds
    # audio_clip = audio_clip.subclip(0, audio_clip.duration - 0.1)

    # Generate ass file
    # ass_filename = srt_create(os.path.dirname(video_path), combined_audio_path)
    # # get the path of ass_file
    # ass_path = os.path.join(os.path.dirname(video_path), ass_filename)

    # print("ASS path: ", ass_path)

    # # Read the sync map
    # print("Reading sync map...")
    # with open(subtitle_path, 'r') as f:
    #     sync_map = json.load(f)

    
    # # Generate image list
    # input_file = os.path.join(image_prep_folder, "image_list.txt")
    # with open(input_file, 'w') as f:
    #     for i, (image_path, fragment) in enumerate(zip(image_paths, sync_map['fragments'])):
    #         duration = float(fragment['end']) - float(fragment['begin'])
            
    #         f.write(f"file '{image_path}'\n")
    #         f.write(f"duration {duration}\n")

    
    # Create the video
    print("DEBUG: Creating video...") # DEBUG
    output_path = await create_video(script_path, image_paths, audio_paths, combined_audio_path, timestamps, video_path)
    print("DEBUG: Video creation complete.") # DEBUG

    end_time = datetime.datetime.now()
    execution_time = end_time - start_time
    print(f"Total execution time: {execution_time}")

    return {
        "video_path": output_path,
        "execution_time": str(execution_time)
    }

async def create_video(script_path, image_paths, audio_paths, combined_audio_path,  timestamps, output_path):

    print("DEBUG: Inside create_video function.") # DEBUG
    # Load the audio
    print("DEBUG: Loading combined audio clip...") # DEBUG
    audio_clip = mp.AudioFileClip(combined_audio_path)
    print("DEBUG: Combined audio clip loaded.") # DEBUG

    # Create subtitle clip
    word_subtitles = []
    for scene in timestamps:
        word_subtitles.extend(scene['words'])

    # Create subtitle clip at the scene level
    scene_subtitles = []
    for scene in timestamps:
        scene_subtitles.append(scene['scene'])
    
    # Use the new phrase captions with highlighting function
    # Display words according to configuration
    try:
        # Create custom style config based on current settings
        custom_style = {
            'highlight_color': current_settings.caption_highlight_color,
            'normal_color': current_settings.caption_normal_color,
        }
        
        # Use the enhanced caption function with style preset
        if hasattr(current_settings, 'caption_style'):
            subtitles_clip = create_advanced_captions(
                word_subtitles,
                caption_style=current_settings.caption_style,
                words_per_line=CAPTION_WORDS_PER_LINE,
                max_lines=CAPTION_MAX_LINES
            )
        else:
            # Fallback to enhanced version with custom styling
            subtitles_clip = add_phrase_captions_with_highlighting(
                word_subtitles, 
                words_per_line=CAPTION_WORDS_PER_LINE, 
                max_lines=CAPTION_MAX_LINES,
                style_config=custom_style
            )
        subtitles_clip = subtitles_clip.set_duration(audio_clip.duration)
    except Exception as e:
        print(f"Error creating captions: {str(e)}")
        # Fallback to no captions
        subtitles_clip = None

    # Create image clips
    image_clips = []
    total_duration = 0
    overlap_duration = 1 # Half a second overlap between clips

    print("DEBUG: Creating image clips...") # DEBUG
    if not image_paths or not timestamps:
        print("Warning: image_paths or timestamps are empty. Video may be generated without images or with incorrect timing.")
        # Handle this case, perhaps by creating a blank video or raising an error.
        # For now, this might lead to mp.concatenate_videoclips([]) which could error.
        if not image_paths: # If no images, create a blank clip matching audio duration.
            if audio_clip:
                 video_clip = mp.ColorClip(size=(1080,1920), color=(0,0,0), ismask=False, duration=audio_clip.duration)
            else: # No audio either, very problematic.
                 video_clip = mp.ColorClip(size=(1080,1920), color=(0,0,0), ismask=False, duration=1) # Default 1s black screen
            image_clips.append(video_clip) # Will be used directly instead of concatenating.
        # If timestamps are empty but images exist, this loop won't run, leading to empty image_clips if not handled.
        # The zip will handle mismatched lengths gracefully by stopping at the shorter one.

    for i, (image_path, scene_data) in enumerate(zip(image_paths, timestamps)):
        print(f"DEBUG: Processing image {i+1}/{len(image_paths)}: {image_path}") # DEBUG
        start_time, end_time = scene_data['scene'][0]
        duration = end_time - start_time

        img_clip = mp.ImageClip(image_path).set_duration(duration + overlap_duration)

        if i == 0:
            img_clip = img_clip.set_start(0)
        else:
            # img_clip = _apply_effects(img_clip)
            img_clip = img_clip.set_start(total_duration - overlap_duration)

        image_clips.append(img_clip)
        total_duration += duration

    # Adjust the last clip to remove the extra overlap duration
    if image_clips:
        last_clip = image_clips[-1]
        image_clips[-1] = last_clip.set_duration(last_clip.duration - overlap_duration)

    # Concatenate image clips
    print("DEBUG: Concatenating image clips...") # DEBUG
    if not image_clips and image_paths: # This case means zip(image_paths, timestamps) was empty, likely due to empty timestamps
        print("Warning: No image clips were created despite having image paths. Timestamps might be missing. Creating black video.")
        if audio_clip:
            video_clip = mp.ColorClip(size=(1080,1920), color=(0,0,0), ismask=False, duration=audio_clip.duration)
        else:
            video_clip = mp.ColorClip(size=(1080,1920), color=(0,0,0), ismask=False, duration=1)
    elif not image_clips and not image_paths: # No images provided initially
         pass # video_clip should already be a ColorClip from earlier handling
    elif image_clips:
        video_clip = mp.concatenate_videoclips(image_clips)
    else: # Should not happen if logic above is correct
        print("ERROR: Unhandled case for video_clip creation. Defaulting to black screen.")
        video_clip = mp.ColorClip(size=(1080,1920), color=(0,0,0), ismask=False, duration=1)
        
    print("DEBUG: Image clips concatenated.") # DEBUG

    # Combine video, audio, and subtitles
    print("Combining video, audio, and subtitles...")
    if subtitles_clip:
        final_clip = mp.CompositeVideoClip([video_clip, subtitles_clip])
    else:
        final_clip = video_clip
    final_clip = final_clip.set_audio(audio_clip)

    # Write the final video
    print("DEBUG: Writing final video file...") # DEBUG
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)
    print("DEBUG: Final video file written.") # DEBUG

    # Close clips
    audio_clip.close()
    for clip in image_clips:
        clip.close()
    final_clip.close()

    # # Get script data
    # with open(script_path, 'r') as f:
    #     script_data = json.load(f)
    
        # Create the initial video without captions
    # initial_output_path = output_path.replace('.mp4', '_no_captions.mp4')
    


    # # Generate subtitle file with precise timings
    # subtitle_path = os.path.splitext(output_path)[0] + '.srt'
    # print("Generating subtitle file...")
    # with open(subtitle_path, 'w') as srt:
    #     for i, fragment in enumerate(sync_map['fragments'], start=1):
    #         start_time = float(fragment['begin'])
    #         end_time = float(fragment['end'])
    #         text = fragment['lines'][0]
    #         srt.write(f"{i}\n")
    #         srt.write(f"{format_timecode(start_time)} --> {format_timecode(end_time)}\n")
    #         srt.write(f"{text}\n\n")

    # # Generate image list
    # input_file = os.path.join(os.path.dirname(output_path), "image_list.txt")
    # with open(input_file, 'w') as f:
    #     num_images = len(image_paths)
    #     fragments_per_image = len(sync_map['fragments']) // num_images
        
    #     for i, image_path in enumerate(image_paths):
    #         start_index = i * fragments_per_image
    #         end_index = (i + 1) * fragments_per_image if i < num_images - 1 else len(sync_map['fragments'])
            
    #         start_time = float(sync_map['fragments'][start_index]['begin'])
    #         end_time = float(sync_map['fragments'][end_index - 1]['end'])
            
    #         f.write(f"file '{image_path}'\n")
    #         f.write(f"duration {end_time - start_time}\n")

    # ffmpeg_command = [
    #     'ffmpeg',
    #     '-f', 'concat',
    #     '-safe', '0',
    #     '-i', input_file,
    #     '-i', combined_audio_path,
    #     '-filter_complex', f'[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v]',
    #     '-map', '[v]',
    #     '-map', '1:a',
    #     '-c:v', 'libx264',
    #     '-preset', 'fast',
    #     '-crf', '23',
    #     '-c:a', 'aac',
    #     '-b:a', '192k',
    #     '-r', '30',
    #     output_path
    # ]

    # print("FFmpeg command: ", ' '.join(ffmpeg_command))



    # try:
    #     result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
    # except subprocess.CalledProcessError as e:
    #     error_message = f"Error creating video: {str(e)}\n"
    #     error_message += f"FFmpeg stdout: {e.stdout}\n"
    #     error_message += f"FFmpeg stderr: {e.stderr}\n"
    #     raise HTTPException(status_code=500, detail=error_message)
    
     # Add captions to the video
    # add_captions_to_video(initial_output_path, sync_map, output_path)

    # Remove the initial video without captions
    # os.remove(initial_output_path)
    
    # get parent folder of image paths and audio paths
    if image_paths: # Ensure image_paths is not empty
        image_parent_folder = os.path.dirname(image_paths[0])
    else:
        image_parent_folder = None # No images, no folder to delete

    if audio_paths: # Ensure audio_paths is not empty
        audio_parent_folder = os.path.dirname(audio_paths[0]) # This was already guarded by if not audio_paths for ffmpeg
                                                            # but audio_paths could be manipulated by placeholder logic later
    else:
        audio_parent_folder = None

    script_parent_folder = os.path.dirname(script_path)

    # move all images and audio to the video folder, and script to the video folder
    print("DEBUG: Moving generated assets to final video folder...") # DEBUG
    for image_path in image_paths:
        shutil.move(image_path, os.path.join(os.path.dirname(output_path), os.path.basename(image_path)))

    # move image list to the video folder
    # shutil.move(input_file, os.path.join(os.path.dirname(output_path), os.path.basename(input_file)))

    for audio_path_item in audio_paths: # DEBUG: Renamed variable
        shutil.move(audio_path_item, os.path.join(os.path.dirname(output_path), os.path.basename(audio_path_item)))
    shutil.move(script_path, os.path.join(os.path.dirname(output_path), os.path.basename(script_path)))
    print("DEBUG: Assets moved.") # DEBUG

    # delete the image, audio, and script folders
    print("DEBUG: Deleting temporary generation folders...") # DEBUG
    if image_parent_folder and os.path.exists(image_parent_folder) and os.path.isdir(image_parent_folder): # Add checks
        try:
            os.rmdir(image_parent_folder)
            print(f"DEBUG: Deleted image parent folder: {image_parent_folder}") # DEBUG
        except OSError as e:
            print(f"Warning: Could not delete image parent folder {image_parent_folder}: {e}")
            
    if audio_parent_folder and os.path.exists(audio_parent_folder) and os.path.isdir(audio_parent_folder): # Add checks
        try:
            os.rmdir(audio_parent_folder)
            print(f"DEBUG: Deleted audio parent folder: {audio_parent_folder}") # DEBUG
        except OSError as e:
            print(f"Warning: Could not delete audio parent folder {audio_parent_folder}: {e}")

    if script_parent_folder and os.path.exists(script_parent_folder) and os.path.isdir(script_parent_folder): # Add checks
        try:
            os.rmdir(script_parent_folder)
            print(f"DEBUG: Deleted script parent folder: {script_parent_folder}") # DEBUG
        except OSError as e:
            print(f"Warning: Could not delete script parent folder {script_parent_folder}: {e}")
            
    print("DEBUG: Temporary folders deletion attempt complete.") # DEBUG

    return output_path

# # Generate script and images endpoint
# @app.post("/generate_script_and_images")
# async def generate_script_and_images(request: GenerateTextRequest):
#     script_response = await generate_script_endpoint(request)
#     script_data = json.loads(script_response.body)
    
#     # Get date and time
#     now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
#     # Create a unique folder for this script
#     script_title = script_data.get("title", "untitled").replace(" ", "_")
#     script_folder = os.path.join(GENERATED_VIDEOS_DIR, f"{script_title}_{now}"  )

#     os.makedirs(script_folder, exist_ok=True)
    
#     image_paths = await generate_images_from_script(script_data, script_folder)
    
#     # Save the script JSON in the same folder
#     script_json_path = os.path.join(script_folder, "script.json")
#     with open(script_json_path, "w") as f:
#         json.dump(script_data, f, indent=2)
    
#     return {
#         "script": script_data,
#         "image_paths": image_paths,
#         "script_folder": script_folder,
#         "script_json_path": script_json_path,
#     }


# Endpoint to get generated content
@app.get("/get_generated_content/{folder_name:path}")
async def get_generated_content(folder_name: str):
    # Decode the URL-encoded folder name
    decoded_folder_name = unquote(folder_name)
    # print(f"Decoded folder name: {decoded_folder_name}")
    
    folder_path = os.path.join(GENERATED_VIDEOS_DIR, decoded_folder_name)
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path}")
    
    script_json_path = os.path.join(folder_path, "script.json")
    if not os.path.exists(script_json_path):
        raise HTTPException(status_code=404, detail=f"Script file not found: {script_json_path}")
    
    with open(script_json_path, "r") as f:
        script_data = json.load(f)
    
    # Check for images in the main folder and in the 'images' subfolder
    image_files = []
    image_urls = []
    
    # Check main folder for images
    main_folder_images = [f for f in os.listdir(folder_path) if f.endswith('.png')]
    for img in main_folder_images:
        image_files.append(img)
        image_urls.append(f"/generations/videos/{folder_name}/{img}")
    
    # Check 'images' subfolder if it exists
    images_subfolder = os.path.join(folder_path, "images")
    if os.path.exists(images_subfolder) and os.path.isdir(images_subfolder):
        subfolder_images = [f for f in os.listdir(images_subfolder) if f.endswith('.png')]
        for img in subfolder_images:
            image_files.append(os.path.join("images", img))
            image_urls.append(f"/generations/videos/{folder_name}/images/{img}")
    
    # Check for videos in the main folder and in the 'videos' subfolder
    video_files = []
    video_urls = []
    
    # Check main folder for videos
    main_folder_videos = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]
    for video in main_folder_videos:
        video_files.append(video)
        video_urls.append(f"/generations/videos/{folder_name}/{video}")
    
    # Check 'videos' subfolder if it exists
    videos_subfolder = os.path.join(folder_path, "videos")
    if os.path.exists(videos_subfolder) and os.path.isdir(videos_subfolder):
        subfolder_videos = [f for f in os.listdir(videos_subfolder) if f.endswith('.mp4')]
        for video in subfolder_videos:
            video_files.append(os.path.join("videos", video))
            video_urls.append(f"/generations/videos/{folder_name}/videos/{video}")

    # If no video files are found, raise a 404 error
    if not video_files:
        raise HTTPException(status_code=404, detail=f"No video files found in folder: {folder_path}")

    return {
        "script": script_data,
        "image_urls": image_urls,
        "video_urls": video_urls,
        "image_files": image_files,
        "video_files": video_files
    }

# List generated content endpoint
@app.get("/list_generated_content")
async def list_generated_content():
    folders = [f for f in os.listdir(GENERATED_VIDEOS_DIR) if os.path.isdir(os.path.join(GENERATED_VIDEOS_DIR, f))]
    return {"folders": folders}


app.add_middleware(
    CORSMiddleware, 
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Add any other potential frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------ TESTING ENDPOINTS ------------

# Helper function to generate speech for a scene
async def generate_speech_for_scene(session, scene, output_dir):
    """
    Generate speech for a single scene using the current voice and TTS settings.
    
    Args:
        session: aiohttp ClientSession to use for the request
        scene: Scene data containing the script
        output_dir: Directory to save the generated audio
        
    Returns:
        Path to the generated audio file
    """
    speech_request = GenerateSpeechRequest(
        text=scene['script'],
        voice=current_settings.voice,
        preset=current_settings.tts_preset,
        candidates=1,
        cvvp_amount=0.0
    )
    
    # Call the speech generation function
    audio_path = await generate_speech(speech_request, output_dir)
    return audio_path[0]  # Return the first audio path

# for testing purposes
@app.post("/generate_script_and_audio")
async def generate_script_and_audio(request: GenerateTextRequest):
    # Generate script
    script_response = await generate_script(request)
    script_data = json.loads(script_response.body)

    # Get date and time
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a unique folder for this script
    script_title = script_data.get("title", "untitled").replace(" ", "_")
    script_folder = os.path.join(GENERATED_IMAGES_DIR, f"{script_title}_{now}")

    os.makedirs(script_folder, exist_ok=True)
    
    # Generate speech for each scene
    async with aiohttp.ClientSession() as session:
        audio_paths = []
        for scene in script_data['scenes']:
            audio_path = await generate_speech_for_scene(session, scene, script_folder)
            audio_paths.append(audio_path)

    print("Audio paths: ", audio_paths)
    # Save the script JSON in the same folder
    script_json_path = os.path.join(script_folder, "script.json")
    with open(script_json_path, "w") as f:
        json.dump(script_data, f, indent=2)
    
    return {
        "script": script_data,
        "audio_paths": audio_paths,
        "script_folder": script_folder,
        "script_json_path": script_json_path,
    }


TESTING_FOLDER = "/app/api/testing"  # Adjust this path as needed

@app.post("/generate_alignment_map")
async def generate_alignment_map(request: dict):
    try:
        script_path = os.path.join("/app/api/testing", request.get("script_path", ""))
        audio_path = os.path.join("/app/api/testing", request.get("audio_path", ""))
        
        if not script_path or not audio_path:
            raise HTTPException(status_code=400, detail="Missing required data")

        # Read the script data from the file
        with open(script_path, 'r') as script_file:
            script_data = json.load(script_file)

        # Generate a unique output path for the alignment map
        output_filename = f"alignment_map_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = os.path.join("/app/api/testing", output_filename)

        # Call the generate_forced_alignment_map function
        generate_forced_alignment_map(script_data, audio_path, output_path)

        # Format the timestamps
        formatted_timestamps = format_aeneas_timestamps(output_path)

        return {
            "message": "Alignment map generated successfully",
            "alignment_map_path": output_path,
            "formatted_timestamps": formatted_timestamps
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating alignment map: {str(e)}")


@app.get("/test_create_video")
async def test_caption_overlay():
    try:
        # Load the script
        full_script_path = os.path.join(TESTING_FOLDER, "script.json")
        with open(full_script_path, "r") as f:
            script_data = json.load(f)

        video_clips = []

        for i, scene in enumerate(script_data['scenes'], start=1):
            # Load image
            image_path = os.path.join(TESTING_FOLDER, f"scene_{i}.png")
            img_clip = mp.ImageClip(image_path)

            # Load audio
            audio_path = os.path.join(TESTING_FOLDER, f"scene_{i}.wav")
            audio_clip = mp.AudioFileClip(audio_path)

            # Set image duration to match audio
            img_clip = img_clip.set_duration(audio_clip.duration)

            # Apply effects
            effected_clip = _apply_effects(img_clip)

            # Load syncmap
            syncmap_path = os.path.join(TESTING_FOLDER, f"syncmap_{i}.json")
            with open(syncmap_path, "r") as f:
                syncmap_data = json.load(f)

            # Create word subtitles
            word_subtitles = []
            for fragment in syncmap_data['fragments']:
                for word in fragment['children']:
                    word_subtitles.append(([float(word['begin']), float(word['end'])], word['lines'][0]))

            # Add captions with the new phrase highlighting function
            try:
                captioned_clip = add_phrase_captions_with_highlighting(
                    word_subtitles,
                    words_per_line=CAPTION_WORDS_PER_LINE,
                    max_lines=CAPTION_MAX_LINES
                ).set_duration(audio_clip.duration)
                
                # Combine image, captions, and audio
                final_clip = mp.CompositeVideoClip([effected_clip, captioned_clip]).set_audio(audio_clip)
            except Exception as e:
                print(f"Error creating captions for scene {i}: {str(e)}")
                # Fallback to no captions
                final_clip = effected_clip.set_audio(audio_clip)

            video_clips.append(final_clip)

        # Concatenate all scenes
        final_video = mp.concatenate_videoclips(video_clips)

        # Write the final video
        output_path = os.path.join(TESTING_FOLDER, "final_video.mp4")
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')

        return FileResponse(output_path, media_type="video/mp4", filename="final_video.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_settings")
async def update_settings(settings: GenerationSettings):
    """
    Update the generation settings for videos.
    
    These settings control various aspects of video generation including:
    - Number of scenes and scene duration
    - Voice selection and TTS quality
    - Caption display options
    - Advanced generation parameters
    """
    global current_settings, SCENE_DURATION, VOICE, MAX_RETRIES, CAPTION_WORDS_PER_LINE, CAPTION_MAX_LINES, DEFAULT_NUM_SCENES, CAPTION_STYLE, CAPTION_HIGHLIGHT_COLOR, CAPTION_NORMAL_COLOR
    
    # Update the global settings object
    current_settings = settings
    
    # Update individual global variables used by various functions
    SCENE_DURATION = settings.scene_duration
    VOICE = settings.voice
    MAX_RETRIES = settings.max_retries
    CAPTION_WORDS_PER_LINE = settings.caption_words_per_line
    CAPTION_MAX_LINES = settings.caption_max_lines
    DEFAULT_NUM_SCENES = settings.num_scenes
    CAPTION_STYLE = settings.caption_style
    CAPTION_HIGHLIGHT_COLOR = settings.caption_highlight_color
    CAPTION_NORMAL_COLOR = settings.caption_normal_color
    
    return {
        "message": "Settings updated successfully",
        "settings": current_settings
    }

@app.get("/get_settings")
async def get_settings():
    """
    Get the current generation settings for videos.
    """
    return current_settings

@app.get("/get_available_voices")
async def get_available_voices():
    """
    Get the list of available ElevenLabs voices for text-to-speech.
    """
    return {
        "voices": AVAILABLE_VOICES
    }

@app.get("/get_tts_presets")
async def get_tts_presets():
    """
    Get the list of available TTS quality presets.
    """
    return {
        "presets": TTS_PRESETS
    }

# Keep the existing caption settings endpoints for backward compatibility
@app.post("/update_caption_settings")
async def update_caption_settings(settings: CaptionSettings):
    """
    Update the caption settings for word highlighting in videos.
    
    Args:
        words_per_line: Number of words to display per line (1-10)
        max_lines: Maximum number of lines to display at once (1-5)
    """
    global CAPTION_WORDS_PER_LINE, CAPTION_MAX_LINES, current_settings
    
    CAPTION_WORDS_PER_LINE = settings.words_per_line
    CAPTION_MAX_LINES = settings.max_lines
    
    # Also update the main settings object
    current_settings.caption_words_per_line = settings.words_per_line
    current_settings.caption_max_lines = settings.max_lines
    
    return {
        "message": "Caption settings updated successfully",
        "settings": {
            "words_per_line": CAPTION_WORDS_PER_LINE,
            "max_lines": CAPTION_MAX_LINES
        }
    }

@app.get("/get_caption_settings")
async def get_caption_settings():
    """
    Get the current caption settings for word highlighting in videos.
    """
    return {
        "words_per_line": CAPTION_WORDS_PER_LINE,
        "max_lines": CAPTION_MAX_LINES
    }

@app.get("/get_caption_styles")
async def get_caption_styles():
    """
    Get the list of available caption styles.
    """
    return {
        "caption_styles": CAPTION_STYLES,
        "descriptions": {
            "modern": "Clean and vibrant with green highlights and smooth transitions",
            "classic": "Traditional yellow-on-black styling with elegant fonts",
            "neon": "Cyberpunk-inspired with bright magenta and cyan colors",
            "minimal": "Simple and understated with clean white text"
        }
    }