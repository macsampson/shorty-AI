import os
import json
from aeneas.executetask import ExecuteTask
from aeneas.task import Task

from moviepy.editor import VideoFileClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip, TextClip

import random
from moviepy.video.compositing import transitions as transfx
import moviepy.editor as mp

# Helper function to format timecode
def format_timecode(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Aeneas

# Generates a forced alignment map for the given script and audio
def generate_forced_alignment_map(script_data, combined_audio_path, output_path):
    # Prepare text for aeneas
    print("Preparing text for aeneas...")
    # print(script_data)
    text_content = "\n".join([scene['script'] for scene in script_data['scenes']])
    # print(text_content)
    text_file_path = os.path.join(os.path.dirname(output_path), "script.txt")
    with open(text_file_path, 'w') as f:
        f.write(text_content)

    try:
        # Run aeneas
        print("Running aeneas...")
        config_string = "task_language=eng|is_text_type=mplain|os_task_file_format=json|os_task_file_levels=23"
        task = Task(config_string=config_string)
        task.audio_file_path_absolute = combined_audio_path
        task.text_file_path_absolute = text_file_path
        task.sync_map_file_path_absolute = os.path.join(os.path.dirname(output_path), "syncmap.json")

        ExecuteTask(task).execute()
        task.output_sync_map_file()

        # Format the sync map
        formatted_timestamps = format_aeneas_timestamps(task.sync_map_file_path_absolute)

        # RETURN THE SYNC MAP
        return formatted_timestamps
    finally:
        # Delete the temporary text file
        if os.path.exists(text_file_path):
            os.remove(text_file_path)
            print(f"Temporary file {text_file_path} has been deleted.")

# Create timestamp tuples at the scene level and word level 
def format_aeneas_timestamps(sync_map_path):
    with open(sync_map_path, 'r') as f:
        sync_map = json.load(f)
    
    formatted_timestamps = []
    
    for fragment in sync_map['fragments']:
        scene_start_time = float(fragment['begin'])
        scene_end_time = float(fragment['end'])
        scene_text = fragment['lines'][0]
        
        word_timestamps = []
        for word in fragment['children']:
            word_start_time = float(word['begin'])
            word_end_time = float(word['end'])
            word_text = word['lines'][0]
            word_timestamps.append(([word_start_time, word_end_time], word_text))
        
        formatted_timestamps.append({
            'scene': ([scene_start_time, scene_end_time], scene_text),
            'words': word_timestamps
        })
    
    return formatted_timestamps





# Moviepy

# Applies a random effect to the given clip
def _apply_effects(clip):
    def zoomIn(clip):
        return clip.resize(lambda t: 1 + t * 0.05)

    def fadeIn(clip):
        return clip.fx(transfx.crossfadein, duration=0.5)

    def fadeOut(clip):
        return clip.fx(transfx.crossfadeout, duration=0.2)

    def slide_in_left(clip):
        return transfx.slide_in(clip, duration=0.1, side="left")

    def slide_in_right(clip):
        return transfx.slide_in(clip, duration=0.1, side="right")

    def slide_in_top(clip):
        return transfx.slide_in(clip, duration=0.1, side="top")

    def slide_in_bottom(clip):
        return transfx.slide_in(clip, duration=0.1, side="bottom")

    inEffects = [
        fadeIn,
        slide_in_left,
        slide_in_right,
        slide_in_top,
        slide_in_bottom,
    ]

    def slide_out_left(clip):
        return transfx.slide_out(clip, duration=0.3, side="left")

    def slide_out_right(clip):
        return transfx.slide_out(clip, duration=0.3, side="right")

    def slide_out_top(clip):
        return transfx.slide_out(clip, duration=0.3, side="top")

    def slide_out_bottom(clip):
        return transfx.slide_out(clip, duration=0.3, side="bottom")

    outEffects = [
        fadeOut,
        slide_out_left,
        slide_out_right,
        slide_out_top,
        slide_out_bottom,
    ]

    inEffect = random.choice(inEffects)
    outEffect = random.choice(outEffects)

    return CompositeVideoClip([zoomIn(inEffect(clip))])

# Generates a subtitle clip for the given text
def add_word_captions(subtitles):
    def _generate_captions(text):
        text_clip = TextClip(
            text.upper(),
            color="yellow",
            font="Helvetica",
            fontsize=100,
            kerning=-8,
            interline=-2,
            method='caption',
            align="center",
        )
        stroke_clip = TextClip(
            text.upper(),
            color="yellow",
            font="Helvetica",
            fontsize=100,
            kerning=-8,
            interline=-2,
            method='caption',
            align="center",
            stroke_color="black",
            stroke_width=20,
        )
        final_text = mp.CompositeVideoClip([stroke_clip, text_clip])
        # Position the text at the center bottom with a small margin
        final_text = final_text.set_position(("center", "bottom"))
        return final_text

    return SubtitlesClip(subtitles, _generate_captions)

# Enhanced function to display multiple words with synchronized highlighting and improved visual effects
def add_phrase_captions_with_highlighting(word_subtitles, words_per_line=5, max_lines=2, style_config=None):
    """
    Creates captions that display multiple words at a time with the current word highlighted.
    Enhanced with better visual effects, transitions, and customizable styling.
    
    Args:
        word_subtitles: List of tuples with word timing and text ([start_time, end_time], word_text)
        words_per_line: Number of words to display per line
        max_lines: Maximum number of lines to display at once
        style_config: Dictionary with custom styling options
    
    Returns:
        A clip with the formatted captions
    """
    if not word_subtitles:
        # Return an empty clip if no words
        return mp.ColorClip(size=(1920, 1080), color=(0, 0, 0, 0)).set_duration(0.1)
    
    # Default style configuration
    default_style = {
        'base_fontsize': 75,
        'highlight_color': '#00FF7F',  # Spring Green - more vibrant
        'normal_color': '#FFFFFF',     # White for better contrast
        'stroke_color': '#000000',     # Black stroke
        'stroke_width': 4,
        'background_opacity': 0.8,
        'background_color': (0, 0, 0), # Black background
        'font_family': 'Helvetica-Bold',
        'glow_effect': True,
        'animate_highlight': True,
        'fade_transition': True,
        'shadow_offset': 2,
        'letter_spacing': 1.2
    }
    
    # Merge with provided style config
    if style_config:
        default_style.update(style_config)
    
    # Get the total duration from the last word's end time
    total_duration = word_subtitles[-1][0][1]
    
    # Create a clip for each word
    word_clips = []
    
    # Define video dimensions
    video_width, video_height = 1920, 1080
    
    # Calculate safe area margins (8% of height for bottom, improved positioning)
    bottom_margin = int(video_height * 0.08)
    
    for i, ((start_time, end_time), current_word) in enumerate(word_subtitles):
        duration = end_time - start_time
        
        # Skip very short words (likely noise)
        if duration < 0.05:
            continue
            
        # Determine which words to show (context around the current word)
        context_size = words_per_line * max_lines // 2
        start_idx = max(0, i - context_size)
        end_idx = min(len(word_subtitles), i + context_size + 1)
        
        # Get the words to display
        display_words = word_subtitles[start_idx:end_idx]
        
        # Organize words into lines with better word wrapping
        lines = []
        line = []
        current_line_length = 0
        max_line_length = 50  # Approximate character limit per line
        
        for j, (_, word) in enumerate(display_words):
            is_current = (start_idx + j) == i
            word_length = len(word)
            
            # Check if adding this word would exceed line length
            if (current_line_length + word_length + 1 > max_line_length and 
                len(line) >= 2 and len(line) < words_per_line):
                lines.append(line)
                line = [(word, is_current)]
                current_line_length = word_length
            else:
                line.append((word, is_current))
                current_line_length += word_length + 1
            
            # Start a new line when we reach words_per_line
            if len(line) >= words_per_line:
                lines.append(line)
                line = []
                current_line_length = 0
        
        # Add any remaining words
        if line:
            lines.append(line)
        
        # Limit to max_lines
        lines = lines[:max_lines]
        
        # Create enhanced text with better styling
        all_lines_text = []
        
        for line_words in lines:
            line_parts = []
            for word, is_current in line_words:
                if is_current:
                    # Current word - enhanced highlighting with glow effect
                    if default_style['glow_effect']:
                        line_parts.append(
                            f"<span foreground='{default_style['highlight_color']}' "
                            f"weight='bold' size='larger' "
                            f"letter_spacing='{int(default_style['letter_spacing'] * 1024)}'>"
                            f"{word}</span>"
                        )
                    else:
                        line_parts.append(
                            f"<span foreground='{default_style['highlight_color']}' weight='bold'>{word}</span>"
                        )
                else:
                    # Other words - normal styling with subtle opacity
                    line_parts.append(
                        f"<span foreground='{default_style['normal_color']}' alpha='85%'>{word}</span>"
                    )
            
            all_lines_text.append(" ".join(line_parts))
        
        # Join all lines with newlines
        full_text = "<span>" + "\n".join(all_lines_text) + "</span>"
        
        # Dynamically adjust font size based on content
        base_fontsize = default_style['base_fontsize']
        
        # Reduce font size if we have many lines or very long words
        if max_lines >= 3:
            base_fontsize = int(base_fontsize * 0.9)
        if max_lines >= 4:
            base_fontsize = int(base_fontsize * 0.8)
        if any(len(word) > 12 for line in lines for word, _ in line):
            base_fontsize = int(base_fontsize * 0.9)
        if any(len(word) > 18 for line in lines for word, _ in line):
            base_fontsize = int(base_fontsize * 0.8)
            
        # Create the main text clip with enhanced styling
        text_clip = TextClip(
            full_text,
            color=default_style['normal_color'],
            font=default_style['font_family'],
            fontsize=base_fontsize,
            method='pango',
            align="center",
            stroke_color=default_style['stroke_color'],
            stroke_width=default_style['stroke_width'],
        )
        
        # Add shadow effect for better depth
        if default_style['shadow_offset'] > 0:
            shadow_clip = TextClip(
                full_text,
                color='#333333',
                font=default_style['font_family'],
                fontsize=base_fontsize,
                method='pango',
                align="center",
            ).set_position((default_style['shadow_offset'], default_style['shadow_offset']))
            
            text_clip = mp.CompositeVideoClip([shadow_clip, text_clip])
        
        # Get dimensions after potential shadow composition
        w, h = text_clip.size
        
        # Enhanced padding calculation
        horizontal_padding = max(25, int(w * 0.05))
        vertical_padding = max(20, int(h * 0.1))
        
        # Ensure caption fits on screen by adjusting fontsize if needed
        max_height = video_height - (bottom_margin * 2)
        if h + (vertical_padding * 2) > max_height:
            # Calculate a new font size that will fit
            scale_factor = max_height / (h + (vertical_padding * 2))
            adjusted_fontsize = int(base_fontsize * scale_factor * 0.9)  # 10% buffer
            
            # Recreate the text clip with adjusted font size
            text_clip = TextClip(
                full_text,
                color=default_style['normal_color'],
                font=default_style['font_family'],
                fontsize=adjusted_fontsize,
                method='pango',
                align="center",
                stroke_color=default_style['stroke_color'],
                stroke_width=default_style['stroke_width'],
            )
            
            # Recreate shadow if enabled
            if default_style['shadow_offset'] > 0:
                shadow_clip = TextClip(
                    full_text,
                    color='#333333',
                    font=default_style['font_family'],
                    fontsize=adjusted_fontsize,
                    method='pango',
                    align="center",
                ).set_position((default_style['shadow_offset'], default_style['shadow_offset']))
                
                text_clip = mp.CompositeVideoClip([shadow_clip, text_clip])
            
            w, h = text_clip.size
        
        # Create enhanced background with rounded corners effect
        bg_width = w + horizontal_padding * 2
        bg_height = h + vertical_padding * 2
        
        # Create gradient-like background effect
        bg_clip = mp.ColorClip(
            size=(bg_width, bg_height), 
            color=(*default_style['background_color'], default_style['background_opacity'])
        ).set_opacity(default_style['background_opacity'])
        
        # Position text on background
        caption_clip = mp.CompositeVideoClip([
            bg_clip,
            text_clip.set_position((horizontal_padding, vertical_padding))
        ])
        
        # Add fade transitions if enabled
        if default_style['fade_transition'] and duration > 0.3:
            fade_duration = min(0.15, duration * 0.2)
            caption_clip = caption_clip.crossfadein(fade_duration).crossfadeout(fade_duration)
        
        # Set timing with slight overlap for smoother transitions
        caption_clip = caption_clip.set_start(start_time).set_duration(duration)
        
        # Enhanced positioning with better centering
        caption_y = video_height - bg_height - bottom_margin
        
        # Ensure caption doesn't go off screen
        if caption_y < bottom_margin // 2:
            caption_y = bottom_margin // 2
        elif caption_y + bg_height > video_height - bottom_margin // 2:
            caption_y = video_height - bg_height - bottom_margin // 2
            
        # Center horizontally and position vertically
        caption_clip = caption_clip.set_position(('center', caption_y))
        
        word_clips.append(caption_clip)
    
    # Combine all word clips with better composition
    if word_clips:
        final_clip = mp.CompositeVideoClip(word_clips, size=(video_width, video_height))
        final_clip = final_clip.set_duration(total_duration)
        return final_clip
    else:
        return mp.ColorClip(size=(video_width, video_height), color=(0, 0, 0, 0)).set_duration(total_duration)

# Enhanced function with customizable styling options
def create_advanced_captions(word_subtitles, caption_style='modern', words_per_line=5, max_lines=2):
    """
    Creates captions with predefined visual styles for different aesthetics.
    
    Args:
        word_subtitles: List of tuples with word timing and text
        caption_style: Style preset ('modern', 'classic', 'neon', 'minimal')
        words_per_line: Number of words to display per line
        max_lines: Maximum number of lines to display
    
    Returns:
        A clip with the formatted captions
    """
    
    style_presets = {
        'modern': {
            'base_fontsize': 75,
            'highlight_color': '#00FF7F',
            'normal_color': '#FFFFFF',
            'stroke_color': '#000000',
            'stroke_width': 4,
            'background_opacity': 0.8,
            'background_color': (0, 0, 0),
            'font_family': 'Helvetica-Bold',
            'glow_effect': True,
            'animate_highlight': True,
            'fade_transition': True,
            'shadow_offset': 2,
            'letter_spacing': 1.2
        },
        'classic': {
            'base_fontsize': 70,
            'highlight_color': '#FFD700',
            'normal_color': '#FFFFFF',
            'stroke_color': '#000000',
            'stroke_width': 3,
            'background_opacity': 0.7,
            'background_color': (0, 0, 0),
            'font_family': 'Times-Bold',
            'glow_effect': False,
            'animate_highlight': False,
            'fade_transition': True,
            'shadow_offset': 1,
            'letter_spacing': 1.0
        },
        'neon': {
            'base_fontsize': 80,
            'highlight_color': '#FF00FF',
            'normal_color': '#00FFFF',
            'stroke_color': '#FFFFFF',
            'stroke_width': 2,
            'background_opacity': 0.9,
            'background_color': (0, 0, 0),
            'font_family': 'Helvetica-Bold',
            'glow_effect': True,
            'animate_highlight': True,
            'fade_transition': True,
            'shadow_offset': 3,
            'letter_spacing': 1.5
        },
        'minimal': {
            'base_fontsize': 65,
            'highlight_color': '#FFFFFF',
            'normal_color': '#CCCCCC',
            'stroke_color': '#000000',
            'stroke_width': 1,
            'background_opacity': 0.6,
            'background_color': (0, 0, 0),
            'font_family': 'Helvetica',
            'glow_effect': False,
            'animate_highlight': False,
            'fade_transition': False,
            'shadow_offset': 0,
            'letter_spacing': 1.0
        }
    }
    
    style_config = style_presets.get(caption_style, style_presets['modern'])
    
    return add_phrase_captions_with_highlighting(
        word_subtitles, 
        words_per_line=words_per_line, 
        max_lines=max_lines, 
        style_config=style_config
    )

# Adds the subtitle clip to the video
def add_captions_to_video(video_path, sync_map, output_path):
    print("Video path: ", video_path)
    video = VideoFileClip(video_path)
    captions = add_word_captions(sync_map)
    
    final_video = CompositeVideoClip([video, captions])
    final_video.write_videofile(output_path, codec='libx264')
    
    video.close()
    final_video.close()


# def generate_caption_clips(sync_map, video_size):
#     clips = []
#     current_segment = []
#     segment_start_time = None
#     segment_char_count = 0
#     max_chars_per_line = 30  # Adjust this value as needed
#     font_size = 64

#     for fragment in sync_map['fragments']:
#         for word in fragment['children']:
#             start_time = float(word['begin'])
#             end_time = float(word['end'])
#             text = word['lines'][0]

#             if not current_segment:
#                 segment_start_time = start_time
#                 current_segment.append(text)
#                 segment_char_count = len(text)
#             elif segment_char_count + len(text) + 1 <= max_chars_per_line:
#                 current_segment.append(text)
#                 segment_char_count += len(text) + 1  # +1 for the space
#             else:
#                 # Create clip for the current segment
#                 segment_text = ' '.join(current_segment)
#                 segment_duration = start_time - segment_start_time
#                 txt_clip = create_growing_text_clip(segment_text, font_size, segment_duration, segment_start_time)
#                 clips.append(txt_clip)

#                 # Start a new segment
#                 segment_start_time = start_time
    #             current_segment = [text]
    #             segment_char_count = len(text)

    # # Handle the last segment
    # if current_segment:
    #     segment_text = ' '.join(current_segment)
    #     segment_duration = end_time - segment_start_time
    #     txt_clip = create_growing_text_clip(segment_text, font_size, segment_duration, segment_start_time)
    #     clips.append(txt_clip)

    # return CompositeVideoClip(clips, size=video_size)

# def create_growing_text_clip(txt, font_size, duration, t_start):
#     return TextClip(txt, fontsize=font_size, color='white', font='Helvetica', stroke_color='black', stroke_width=1.5, method='caption', size=(1080,1920)) \
#         .set_position(('center', 'bottom')) \
#         .set_duration(duration) \
#         .set_start(t_start) \
#         .margin(bottom=20, opacity=0)  # Add some bottom margin
