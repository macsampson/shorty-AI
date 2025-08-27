import { useState, useRef, useEffect } from "react"
import axios from "axios"
import { GeneratedContent } from "../types"

export const useVideoGeneration = (
  selectedFolder: string,
  setGeneratedContent: (content: GeneratedContent) => void
) => {
  const [loading, setLoading] = useState<boolean>(false)
  const [videoGenerating, setVideoGenerating] = useState<boolean>(false)
  const [prompt, setPrompt] = useState<string>("")
  const [error, setError] = useState<string | null>(null)

  // Ref to store the interval ID
  const videoCheckIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Clean up the interval on component unmount
  useEffect(() => {
    return () => {
      if (videoCheckIntervalRef.current) {
        clearInterval(videoCheckIntervalRef.current)
        videoCheckIntervalRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    // If video is generating, start checking for it
    if (videoGenerating && selectedFolder) {
      startVideoCheckInterval()
    } else if (!videoGenerating && videoCheckIntervalRef.current) {
      // If video is no longer generating, clear the interval
      clearInterval(videoCheckIntervalRef.current)
      videoCheckIntervalRef.current = null
    }
  }, [videoGenerating, selectedFolder])

  // Function to start checking for video generation
  const startVideoCheckInterval = () => {
    // Clear any existing interval
    if (videoCheckIntervalRef.current) {
      clearInterval(videoCheckIntervalRef.current)
      videoCheckIntervalRef.current = null
    }

    // Set up a new interval to check for the video
    videoCheckIntervalRef.current = setInterval(async () => {
      try {
        // Fetch the latest folders
        const response = await axios.get(
          "http://localhost:8000/list_generated_content"
        )
        const latestFolders = response.data.folders

        // If we have a selected folder, check if it has a video
        if (selectedFolder && latestFolders.includes(selectedFolder)) {
          const contentResponse = await axios.get(
            `http://localhost:8000/get_generated_content/${selectedFolder}`
          )

          // If the folder has a video, update the content and stop checking
          if (
            contentResponse.data.video_urls &&
            contentResponse.data.video_urls.length > 0
          ) {
            setGeneratedContent(contentResponse.data)
            setVideoGenerating(false)

            // Clear the interval
            if (videoCheckIntervalRef.current) {
              clearInterval(videoCheckIntervalRef.current)
              videoCheckIntervalRef.current = null
            }
          }
        }
      } catch (error) {
        console.error("Error checking for video:", error)
        // Don't keep polling on repeated errors
        if (videoCheckIntervalRef.current) {
          clearInterval(videoCheckIntervalRef.current)
          videoCheckIntervalRef.current = null
        }
      }
    }, 5000) // Check every 5 seconds
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Call the generate_video endpoint
      await axios.post("http://localhost:8000/generate_video", {
        prompt: prompt,
      })

      // Start checking for the video
      setVideoGenerating(true)

      // Clear the prompt
      setPrompt("")

      // Return success
      return true
    } catch (error) {
      console.error("Error generating content:", error)
      setError("Failed to generate content. Please try again.")
      return false
    } finally {
      setLoading(false)
    }
  }

  return {
    loading,
    videoGenerating,
    prompt,
    error,
    setPrompt,
    setVideoGenerating,
    handleSubmit,
  }
}
