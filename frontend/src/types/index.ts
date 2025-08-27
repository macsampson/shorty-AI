// Define shared types for the application

export interface Scene {
  scene_number: number
  script: string
}

export interface Script {
  title: string
  scenes: Scene[]
}

export interface GeneratedContent {
  script: Script
  image_urls: string[]
  video_urls: string[]
}

// Settings interface
export interface Settings {
  num_scenes: number
  scene_duration: number
  voice: string
  tts_preset: string
  caption_words_per_line: number
  caption_max_lines: number
  caption_style: string
  caption_highlight_color: string
  caption_normal_color: string
  max_retries: number
}

export interface WindowSize {
  width: number
  height: number
}
