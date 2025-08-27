import { useState, useEffect } from "react"
import axios from "axios"
import { Settings } from "../types"
import { DEFAULT_SETTINGS } from "../utils/constants"

export const useSettings = () => {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS)
  const [voices, setVoices] = useState<string[]>([])
  const [ttsPresets, setTtsPresets] = useState<string[]>([])
  const [captionStyles, setCaptionStyles] = useState<string[]>([])
  const [captionStyleDescriptions, setCaptionStyleDescriptions] = useState<
    Record<string, string>
  >({})
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Fetch current settings with timeout
      const settingsResponse = await axios.get(
        "http://localhost:8000/get_settings",
        { timeout: 5000 }
      )
      setSettings(settingsResponse.data)

      // Fetch available voices with timeout
      const voicesResponse = await axios.get(
        "http://localhost:8000/get_available_voices",
        { timeout: 5000 }
      )
      setVoices(voicesResponse.data.voices)

      // Fetch TTS presets with timeout
      const presetsResponse = await axios.get(
        "http://localhost:8000/get_tts_presets",
        { timeout: 5000 }
      )
      setTtsPresets(presetsResponse.data.presets)

      // Fetch caption styles with timeout
      const captionStylesResponse = await axios.get(
        "http://localhost:8000/get_caption_styles",
        { timeout: 5000 }
      )
      setCaptionStyles(captionStylesResponse.data.caption_styles)
      setCaptionStyleDescriptions(captionStylesResponse.data.descriptions)
    } catch (error) {
      console.error("Error fetching settings:", error)
      setError("Error loading settings")

      // Don't break the UI if settings can't be fetched, use defaults
      if (!settings) {
        setSettings(DEFAULT_SETTINGS)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const updateSetting = async (name: keyof Settings, value: any) => {
    const newSettings = {
      ...settings,
      [name]: value,
    }

    setSettings(newSettings)

    try {
      // Save the settings to the server
      await axios.post("http://localhost:8000/update_settings", newSettings)
    } catch (error) {
      console.error("Error saving settings:", error)
      setError("Error saving settings")
    }
  }

  return {
    settings,
    voices,
    ttsPresets,
    captionStyles,
    captionStyleDescriptions,
    isLoading,
    error,
    updateSetting,
    fetchSettings,
  }
}
