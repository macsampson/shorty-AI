import React from "react"
import { Settings } from "../types"

interface CaptionPreviewProps {
  settings: Settings
}

const CaptionPreview: React.FC<CaptionPreviewProps> = ({ settings }) => {
  // Sample text for preview
  const sampleWords = [
    "This",
    "is",
    "how",
    "your",
    "captions",
    "will",
    "look",
    "in",
    "the",
    "video",
  ]
  const highlightIndex = 4 // Index of the word to highlight

  // Get style properties based on the selected caption style
  const getStyleProps = () => {
    const baseStyle = {
      padding: "12px 16px",
      borderRadius: "8px",
      fontFamily: "Helvetica, Arial, sans-serif",
      fontWeight: "bold",
      fontSize: "18px",
      lineHeight: "1.4",
      textAlign: "center" as const,
      maxWidth: "500px",
      margin: "0 auto",
    }

    switch (settings.caption_style) {
      case "modern":
        return {
          ...baseStyle,
          background: "rgba(0, 0, 0, 0.8)",
          border: "2px solid transparent",
          boxShadow:
            "0 4px 12px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1)",
        }
      case "classic":
        return {
          ...baseStyle,
          background: "rgba(0, 0, 0, 0.7)",
          border: "1px solid rgba(255, 215, 0, 0.3)",
          fontFamily: "Times, serif",
        }
      case "neon":
        return {
          ...baseStyle,
          background: "rgba(0, 0, 0, 0.9)",
          border: "2px solid #FF00FF",
          boxShadow:
            "0 0 20px rgba(255, 0, 255, 0.5), inset 0 0 20px rgba(255, 0, 255, 0.1)",
          fontSize: "20px",
        }
      case "minimal":
        return {
          ...baseStyle,
          background: "rgba(0, 0, 0, 0.6)",
          border: "none",
          fontSize: "16px",
          fontWeight: "normal" as const,
        }
      default:
        return {
          ...baseStyle,
          background: "rgba(0, 0, 0, 0.8)",
        }
    }
  }

  // Generate words in lines based on settings
  const wordsPerLine = settings.caption_words_per_line
  const maxLines = settings.caption_max_lines
  const totalWordsToShow = Math.min(sampleWords.length, wordsPerLine * maxLines)
  const wordsToShow = sampleWords.slice(0, totalWordsToShow)

  const lines: string[][] = []
  for (let i = 0; i < wordsToShow.length; i += wordsPerLine) {
    lines.push(wordsToShow.slice(i, i + wordsPerLine))
  }

  const styleProps = getStyleProps()

  return (
    <div className="mt-4 p-4 bg-gray-100 rounded-lg">
      <h4 className="text-sm font-medium text-gray-700 mb-3">
        Caption Preview
      </h4>
      <div
        className="relative bg-gray-800 rounded-lg overflow-hidden"
        style={{ minHeight: "120px" }}
      >
        {/* Simulated video background */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-purple-900 to-pink-900 opacity-70"></div>

        {/* Caption overlay */}
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
          <div style={styleProps}>
            {lines.map((line, lineIndex) => (
              <div
                key={lineIndex}
                className="mb-1 last:mb-0"
              >
                {line.map((word, wordIndex) => {
                  const globalIndex = lineIndex * wordsPerLine + wordIndex
                  const isHighlighted = globalIndex === highlightIndex

                  return (
                    <span
                      key={wordIndex}
                      style={{
                        color: isHighlighted
                          ? settings.caption_highlight_color
                          : settings.caption_normal_color,
                        textShadow: "2px 2px 4px rgba(0, 0, 0, 0.8)",
                        fontWeight: isHighlighted ? "bold" : "normal",
                        marginRight:
                          wordIndex < line.length - 1 ? "0.3em" : "0",
                        transition: "all 0.2s ease",
                      }}
                    >
                      {word}
                    </span>
                  )
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Style description */}
        <div className="absolute top-2 left-2 text-xs text-white bg-black bg-opacity-50 px-2 py-1 rounded">
          {settings.caption_style.charAt(0).toUpperCase() +
            settings.caption_style.slice(1)}{" "}
          Style
        </div>
      </div>

      <div className="mt-3 text-xs text-gray-600">
        <div className="flex flex-wrap gap-4">
          <span>Words per line: {settings.caption_words_per_line}</span>
          <span>Max lines: {settings.caption_max_lines}</span>
          <span>
            Highlight:{" "}
            <span style={{ color: settings.caption_highlight_color }}>●</span>
          </span>
          <span>
            Normal:{" "}
            <span style={{ color: settings.caption_normal_color }}>●</span>
          </span>
        </div>
      </div>
    </div>
  )
}

export default CaptionPreview
