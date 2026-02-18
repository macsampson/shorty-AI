import React, { useState } from "react"
import { GeneratedContent } from "../types"
import { formatFolderTitle } from "../utils/formatters"

interface VideoDetailsProps {
  selectedFolder: string
  generatedContent: GeneratedContent | null
  videoGenerating: boolean
}

const VideoDetails: React.FC<VideoDetailsProps> = ({
  selectedFolder,
  generatedContent,
  videoGenerating,
}) => {
  const [isMetadataExpanded, setIsMetadataExpanded] = useState(false)

  if (videoGenerating) {
    return (
      <div className="flex flex-col justify-center items-center py-12 px-8 text-center">
        <div className="spinner"></div>
        <p className="mt-6 text-gray-600">
          Your video is being generated. This may take a few minutes.
        </p>
      </div>
    )
  }

  if (!generatedContent) {
    return (
      <div className="flex flex-col justify-center items-center py-12 px-8 text-center">
        <div className="spinner"></div>
        <p className="mt-6 text-gray-600">Loading video details...</p>
      </div>
    )
  }

  const hasVideo =
    generatedContent.video_urls && generatedContent.video_urls.length > 0
  const metadata = generatedContent.script || {}

  return (
    <div className="flex flex-col gap-6">
      {/* Video section */}
      {hasVideo && (
        <div className="bg-white rounded-lg p-4 md:p-6 shadow-md flex flex-col items-center max-w-full overflow-hidden relative video-ready">
          <h3 className="text-xl font-semibold text-primary self-start mb-4">
            Video Preview
          </h3>
          <div className="w-full relative rounded-lg overflow-hidden bg-black flex justify-center items-center aspect-video max-h-[60vh]">
            <video
              controls
              src={`http://localhost:8000${generatedContent.video_urls[0]}`}
              playsInline
              preload="metadata"
              className="w-full h-full max-h-[60vh] rounded object-contain shadow-lg"
            />
          </div>
          <div className="flex justify-center mt-6 w-full">
            <button
              className="bg-primary hover:bg-primary-hover text-white border-none rounded px-6 py-3 text-base font-semibold cursor-pointer transition-all flex items-center shadow-md hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow"
              onClick={() => {
                const link = document.createElement("a")
                link.href = `http://localhost:8000${generatedContent.video_urls[0]}`
                link.download = `${formatFolderTitle(selectedFolder)}.mp4`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
              }}
            >
              <span className="mr-2">↓</span> Download Video
            </button>
          </div>
        </div>
      )}

      {/* Collapsible metadata */}
      {Object.keys(metadata).length > 0 && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div
            className="flex justify-between items-center p-4 md:p-6 cursor-pointer bg-gray-50 border-b border-gray-200 transition-colors hover:bg-gray-100"
            onClick={() => setIsMetadataExpanded(!isMetadataExpanded)}
          >
            <h3 className="text-lg font-medium text-primary m-0">
              Generation Details
            </h3>
            <span
              className="text-sm transition-transform duration-300"
              style={{
                transform: isMetadataExpanded
                  ? "rotate(0deg)"
                  : "rotate(-90deg)",
              }}
            >
              ▼
            </span>
          </div>
          {isMetadataExpanded && (
            <div className="animate-fadeIn p-4 md:p-6">
              {metadata.original_prompt && (
                <div className="mb-4">
                  <div className="font-semibold text-gray-700 mb-1">Prompt</div>
                  <div className="text-gray-600">{metadata.original_prompt}</div>
                </div>
              )}
              {metadata.expanded_prompt && (
                <div className="mb-4">
                  <div className="font-semibold text-gray-700 mb-1">Expanded Prompt</div>
                  <div className="text-gray-600">{metadata.expanded_prompt}</div>
                </div>
              )}
              {metadata.word_count !== undefined && (
                <div className="mb-4">
                  <div className="font-semibold text-gray-700 mb-1">Captions</div>
                  <div className="text-gray-600">{metadata.word_count} words extracted</div>
                </div>
              )}
              {metadata.created_at && (
                <div className="mb-2">
                  <div className="font-semibold text-gray-700 mb-1">Created</div>
                  <div className="text-gray-600">
                    {new Date(metadata.created_at).toLocaleString()}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default VideoDetails
