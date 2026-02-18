import React from "react"
import { ProgressBar } from "./ProgressBar"

interface VideoFormProps {
  prompt: string
  setPrompt: (prompt: string) => void
  handleSubmit: (e: React.FormEvent) => void
  handleExpand: () => void
  loading: boolean
  videoGenerating: boolean
  expanding: boolean
  expandedPrompt: string
  error: string | null
  progress?: number
  currentStage?: string
  statusMessage?: string
  durationSeconds: number
  setDurationSeconds: (value: number) => void
}

const VideoForm: React.FC<VideoFormProps> = ({
  prompt,
  setPrompt,
  handleSubmit,
  handleExpand,
  loading,
  videoGenerating,
  expanding,
  expandedPrompt,
  error,
  progress = 0,
  currentStage = "",
  statusMessage = "",
  durationSeconds,
  setDurationSeconds,
}) => {
  return (
    <div className="bg-white rounded-lg p-4 md:p-6 shadow-md mb-6">
      <h2 className="text-center text-xl md:text-2xl font-semibold mb-6 text-gray-800">
        apparition.io
      </h2>

      <form onSubmit={handleSubmit}>
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter a simple video idea (e.g., 'a cat walking on the street')..."
            disabled={loading || videoGenerating}
            className="flex-1 p-4 border border-gray-300 rounded-lg text-base transition-all focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="button"
            onClick={handleExpand}
            disabled={!prompt || loading || videoGenerating || expanding}
            className="px-6 py-4 bg-amber-600 text-white border-none rounded-lg text-base font-semibold cursor-pointer transition-all hover:bg-amber-700 hover:translate-y-[-2px] disabled:bg-secondary disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:translate-y-0 md:whitespace-nowrap"
          >
            {expanding ? "Expanding..." : "Expand"}
          </button>
          <button
            type="submit"
            disabled={!prompt || loading || videoGenerating}
            className="px-6 py-4 bg-primary text-white border-none rounded-lg text-base font-semibold cursor-pointer transition-all hover:bg-primary-hover hover:translate-y-[-2px] disabled:bg-secondary disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:translate-y-0 md:whitespace-nowrap"
          >
            {loading ? "Generating..." : "Generate"}
          </button>
        </div>
      </form>

      <div className="mb-4 max-w-xs">
        <label className="flex items-center justify-between text-sm font-medium text-gray-700 mb-2">
          <span>Duration</span>
          <span className="text-primary font-semibold">{durationSeconds}s</span>
        </label>
        <input
          type="range"
          min={5}
          max={30}
          step={5}
          value={durationSeconds}
          onChange={(e) => setDurationSeconds(Number(e.target.value))}
          disabled={loading || videoGenerating}
          className="w-full h-2 rounded-lg appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow-md [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-primary [&::-moz-range-thumb]:border-none [&::-moz-range-thumb]:shadow-md"
          style={{
            background: `linear-gradient(to right, var(--color-primary) 0%, var(--color-primary) ${((durationSeconds - 5) / 25) * 100}%, #e5e7eb ${((durationSeconds - 5) / 25) * 100}%, #e5e7eb 100%)`,
          }}
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>5s</span>
          <span>30s</span>
        </div>
      </div>

      {error && (
        <div className="text-danger p-3 mt-4 bg-danger/10 rounded-lg text-sm border-l-3 border-danger">
          {error}
        </div>
      )}

      {/* Expanded Prompt */}
      {expandedPrompt && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-500 mb-2">Expanded Prompt</h3>
          <p className="text-gray-800 text-sm leading-relaxed">{expandedPrompt}</p>
        </div>
      )}

      {/* Progress Bar */}
      {loading && currentStage && (
        <ProgressBar
          progress={progress}
          stage={currentStage}
          message={statusMessage}
        />
      )}
    </div>
  )
}

export default VideoForm
