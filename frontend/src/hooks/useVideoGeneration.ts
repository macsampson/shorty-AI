import { useState, useRef, useEffect } from "react"
import axios from "axios"
import { GeneratedContent } from "../types"

interface ProgressUpdate {
  progress: number
  stage: string
  message: string
}

export const useVideoGeneration = (
  selectedFolder: string,
  setGeneratedContent: (content: GeneratedContent) => void
) => {
  const [loading, setLoading] = useState<boolean>(false)
  const [videoGenerating, setVideoGenerating] = useState<boolean>(false)
  const [prompt, setPrompt] = useState<string>("")
  const [error, setError] = useState<string | null>(null)
  const [expandedPrompt, setExpandedPrompt] = useState<string>("")
  const [expanding, setExpanding] = useState<boolean>(false)
  const [durationSeconds, setDurationSeconds] = useState<number>(5)

  // WebSocket progress tracking
  const [progress, setProgress] = useState<number>(0)
  const [currentStage, setCurrentStage] = useState<string>("")
  const [statusMessage, setStatusMessage] = useState<string>("")

  // Ref to store WebSocket connection
  const wsRef = useRef<WebSocket | null>(null)

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [])

  // WebSocket connection for VidiGen pipeline
  const connectWebSocket = (jobId: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/video_generation/${jobId}`)

    ws.onopen = () => {
      console.log("WebSocket connected")
    }

    ws.onmessage = (event) => {
      const data: ProgressUpdate = JSON.parse(event.data)

      setProgress(data.progress)
      setCurrentStage(data.stage)
      setStatusMessage(data.message)

      if (data.stage === "complete") {
        setLoading(false)
        setVideoGenerating(false)
        ws.close()
        // Refresh video library
        window.location.reload()
      } else if (data.stage === "error") {
        setError(data.message)
        setLoading(false)
        setVideoGenerating(false)
        ws.close()
      }
    }

    ws.onerror = (error) => {
      console.error("WebSocket error:", error)
      setError("Real-time connection failed")
      setLoading(false)
      setVideoGenerating(false)
    }

    ws.onclose = () => {
      console.log("WebSocket closed")
    }

    wsRef.current = ws
  }

  const handleExpand = async () => {
    if (!prompt) return
    setExpanding(true)
    setExpandedPrompt("")
    setError(null)
    try {
      const response = await axios.post("http://localhost:8000/expand_prompt", { prompt })
      setExpandedPrompt(response.data.expanded)
    } catch (err) {
      console.error("Error expanding prompt:", err)
      setError("Failed to expand prompt.")
    } finally {
      setExpanding(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setProgress(0)
    setCurrentStage("")
    setStatusMessage("")

    try {
      // Use expanded prompt if available, otherwise use raw prompt
      const finalPrompt = expandedPrompt || prompt
      const response = await axios.post(
        "http://localhost:8000/generate_video_vidigen",
        { prompt: finalPrompt, duration_seconds: durationSeconds }
      )

      const { job_id } = response.data
      connectWebSocket(job_id)
      setVideoGenerating(true)

      // Clear the prompt and expanded prompt
      setPrompt("")
      setExpandedPrompt("")

      return true
    } catch (error) {
      console.error("Error generating content:", error)
      setError("Failed to generate content. Please try again.")
      return false
    }
    // Loading stays true until WebSocket reports completion
  }

  return {
    loading,
    videoGenerating,
    prompt,
    error,
    progress,
    currentStage,
    statusMessage,
    expandedPrompt,
    expanding,
    durationSeconds,
    setPrompt,
    setVideoGenerating,
    setDurationSeconds,
    handleSubmit,
    handleExpand,
  }
}
