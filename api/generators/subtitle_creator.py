import os
from pathlib import Path
import torch
import stable_whisper


def srt_create(path: str, audio_path: str) -> bool:
    srt_path = f"{path}{os.sep}"
    # srt_filename = f"{srt_path}subtitle.srt"
    ass_filename = f"{srt_path}subtitle.ass"

    # absolute_srt_path = Path(srt_filename).absolute()
    absolute_ass_path = Path(ass_filename).absolute()
    # print("ASS path: ", absolute_ass_path)
    
    max_words = 10
    max_characters = 50
    font_color = '#FFFF00'

    word_dict = {
        'Fontname': 'Helvetica',
        'Alignment': 2,
        'BorderStyle': '1',
        'Outline': '1',
        'Shadow': '2',
        'Blur': '21',
        'Fontsize': 21,
        'MarginL': '0',
        'MarginR': '0',
        'MarginV': '30',
    }

    transcribe = stable_whisper.load_model('base').transcribe(
        audio_path, regroup=True, fp16=torch.cuda.is_available())

    transcribe.split_by_gap(0.5).split_by_length(max_characters).merge_by_gap(0.15, max_words=max_words)

    # transcribe.to_srt_vtt(str(absolute_srt_path), word_level=True)
    transcribe.to_ass(str(absolute_ass_path), word_level=True,
                      highlight_color=font_color, **word_dict)
    print(f"Subtitles created at {ass_filename}")
    return ass_filename
