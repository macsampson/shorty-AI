import React from "react"
import { Settings } from "../types"
import CaptionPreview from "./CaptionPreview"

interface SettingsPanelProps {
  settings: Settings
  voices: string[]
  ttsPresets: string[]
  captionStyles?: string[]
  captionStyleDescriptions?: Record<string, string>
  updateSetting: (name: keyof Settings, value: any) => void
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({
  settings,
  voices,
  ttsPresets,
  captionStyles = [],
  captionStyleDescriptions = {},
  updateSetting,
}) => {
  return (
    <div className="mt-6 bg-gray-50 rounded-lg p-6 shadow-sm">
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-800">Video Settings</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Video Structure Settings */}
        <div className="bg-white rounded p-4 shadow-sm">
          <h3 className="text-base font-medium text-primary mb-4 pb-2 border-b border-gray-100">
            Video Structure
          </h3>
          <div className="mb-4">
            <label
              htmlFor="num_scenes"
              className="block mb-2 font-medium text-gray-700 text-sm"
            >
              Number of Scenes
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                id="num_scenes"
                min="1"
                max="10"
                value={settings.num_scenes}
                onChange={(e) =>
                  updateSetting("num_scenes", parseInt(e.target.value))
                }
                className="flex-1"
              />
              <span className="min-w-8 text-right text-sm text-gray-600">
                {settings.num_scenes}
              </span>
            </div>
          </div>

          <div className="mb-2">
            <label
              htmlFor="scene_duration"
              className="block mb-2 font-medium text-gray-700 text-sm"
            >
              Scene Duration (seconds)
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                id="scene_duration"
                min="3"
                max="15"
                value={settings.scene_duration}
                onChange={(e) =>
                  updateSetting("scene_duration", parseInt(e.target.value))
                }
                className="flex-1"
              />
              <span className="min-w-8 text-right text-sm text-gray-600">
                {settings.scene_duration}s
              </span>
            </div>
          </div>
        </div>

        {/* Voice Settings */}
        <div className="bg-white rounded p-4 shadow-sm">
          <h3 className="text-base font-medium text-primary mb-4 pb-2 border-b border-gray-100">
            Voice Settings
          </h3>
          <div className="mb-4">
            <label
              htmlFor="voice"
              className="block mb-2 font-medium text-gray-700 text-sm"
            >
              Voice
            </label>
            <select
              id="voice"
              value={settings.voice}
              onChange={(e) => updateSetting("voice", e.target.value)}
              className="w-full p-2 border border-gray-300 rounded text-sm"
            >
              {voices.map((voice) => (
                <option
                  key={voice}
                  value={voice}
                >
                  {voice.replace("train_", "")}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-2">
            <label
              htmlFor="tts_preset"
              className="block mb-2 font-medium text-gray-700 text-sm"
            >
              TTS Quality
            </label>
            <select
              id="tts_preset"
              value={settings.tts_preset}
              onChange={(e) => updateSetting("tts_preset", e.target.value)}
              className="w-full p-2 border border-gray-300 rounded text-sm"
            >
              {ttsPresets.map((preset) => (
                <option
                  key={preset}
                  value={preset}
                >
                  {preset.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Caption Settings */}
        <div className="bg-white rounded p-4 shadow-sm">
          <h3 className="text-base font-medium text-primary mb-4 pb-2 border-b border-gray-100">
            Caption Settings
          </h3>

          {/* Caption Style Preset */}
          <div className="mb-4">
            <label
              htmlFor="caption_style"
              className="block mb-2 font-medium text-gray-700 text-sm"
            >
              Caption Style
            </label>
            <select
              id="caption_style"
              value={settings.caption_style}
              onChange={(e) => updateSetting("caption_style", e.target.value)}
              className="w-full p-2 border border-gray-300 rounded text-sm"
            >
              {captionStyles.map((style) => (
                <option
                  key={style}
                  value={style}
                  title={captionStyleDescriptions[style]}
                >
                  {style.charAt(0).toUpperCase() + style.slice(1)}
                </option>
              ))}
            </select>
            {captionStyleDescriptions[settings.caption_style] && (
              <p className="text-xs text-gray-500 mt-1">
                {captionStyleDescriptions[settings.caption_style]}
              </p>
            )}
          </div>

          <div className="mb-4">
            <label
              htmlFor="caption_words_per_line"
              className="block mb-2 font-medium text-gray-700 text-sm"
            >
              Words Per Line
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                id="caption_words_per_line"
                min="1"
                max="10"
                value={settings.caption_words_per_line}
                onChange={(e) =>
                  updateSetting(
                    "caption_words_per_line",
                    parseInt(e.target.value)
                  )
                }
                className="flex-1"
              />
              <span className="min-w-8 text-right text-sm text-gray-600">
                {settings.caption_words_per_line}
              </span>
            </div>
          </div>

          <div className="mb-4">
            <label
              htmlFor="caption_max_lines"
              className="block mb-2 font-medium text-gray-700 text-sm"
            >
              Maximum Lines
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                id="caption_max_lines"
                min="1"
                max="5"
                value={settings.caption_max_lines}
                onChange={(e) =>
                  updateSetting("caption_max_lines", parseInt(e.target.value))
                }
                className="flex-1"
              />
              <span className="min-w-8 text-right text-sm text-gray-600">
                {settings.caption_max_lines}
              </span>
            </div>
          </div>

          {/* Color Customization */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label
                htmlFor="caption_highlight_color"
                className="block mb-1 font-medium text-gray-700 text-xs"
              >
                Highlight Color
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  id="caption_highlight_color"
                  value={settings.caption_highlight_color}
                  onChange={(e) =>
                    updateSetting("caption_highlight_color", e.target.value)
                  }
                  className="w-8 h-8 border border-gray-300 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={settings.caption_highlight_color}
                  onChange={(e) =>
                    updateSetting("caption_highlight_color", e.target.value)
                  }
                  className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded"
                  placeholder="#00FF7F"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="caption_normal_color"
                className="block mb-1 font-medium text-gray-700 text-xs"
              >
                Normal Color
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  id="caption_normal_color"
                  value={settings.caption_normal_color}
                  onChange={(e) =>
                    updateSetting("caption_normal_color", e.target.value)
                  }
                  className="w-8 h-8 border border-gray-300 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={settings.caption_normal_color}
                  onChange={(e) =>
                    updateSetting("caption_normal_color", e.target.value)
                  }
                  className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded"
                  placeholder="#FFFFFF"
                />
              </div>
            </div>
          </div>

          {/* Caption Preview */}
          <CaptionPreview settings={settings} />
        </div>
      </div>
    </div>
  )
}

export default SettingsPanel
