// Define shared types for the application

export interface GeneratedContent {
  script: Record<string, any>
  image_urls: string[]
  video_urls: string[]
}

export interface WindowSize {
  width: number
  height: number
}
