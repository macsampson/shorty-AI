import React from "react"
import { Settings } from "../types"
import SettingsPanel from "./SettingsPanel"

interface VideoFormProps {
  prompt: string
  setPrompt: (prompt: string) => void
  handleSubmit: (e: React.FormEvent) => void
  loading: boolean
  videoGenerating: boolean
  error: string | null
  settings: Settings
  voices: string[]
  ttsPresets: string[]
  captionStyles?: string[]
  captionStyleDescriptions?: Record<string, string>
  updateSetting: (name: keyof Settings, value: any) => void
}

const VideoForm: React.FC<VideoFormProps> = ({
  prompt,
  setPrompt,
  handleSubmit,
  loading,
  videoGenerating,
  error,
  settings,
  voices,
  ttsPresets,
  captionStyles,
  captionStyleDescriptions,
  updateSetting,
}) => {
  return (
    <div className="bg-white rounded-lg p-4 md:p-6 shadow-md mb-6">
      <h2 className="text-center text-xl md:text-2xl font-semibold mb-6 text-gray-800">
        Generate a Short Video
      </h2>
      <form onSubmit={handleSubmit}>
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter a topic or idea for your video..."
            disabled={loading || videoGenerating}
            className="flex-1 p-4 border border-gray-300 rounded-lg text-base transition-all focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!prompt || loading || videoGenerating}
            className="px-6 py-4 bg-primary text-white border-none rounded-lg text-base font-semibold cursor-pointer transition-all hover:bg-primary-hover hover:translate-y-[-2px] disabled:bg-secondary disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:translate-y-0 md:whitespace-nowrap"
          >
            {loading ? "Generating..." : "Generate"}
          </button>
        </div>
      </form>
      {error && (
        <div className="text-danger p-3 mt-4 bg-danger/10 rounded-lg text-sm border-l-3 border-danger">
          {error}
        </div>
      )}

      {/* Settings Panel - Always Visible */}
      <SettingsPanel
        settings={settings}
        voices={voices}
        ttsPresets={ttsPresets}
        captionStyles={captionStyles}
        captionStyleDescriptions={captionStyleDescriptions}
        updateSetting={updateSetting}
      />
    </div>
  )
}

export default VideoForm
